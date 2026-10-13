import re
import unicodedata
from collections import Counter
from decimal import Decimal

from .generation import Provider
from .schemas import ValidationResult
from .claims import coverage_key


def numeric_tokens(text):
    text = re.sub(r"\bnoon\b", "12", text, flags=re.I)
    text = re.sub(r"\bmidnight\b", "0", text, flags=re.I)
    values = re.findall(r"\d+(?:[.,]\d+)*", text)
    normalized = []
    for value in values:
        parts = re.split(r"[.,]", value)
        if len(parts) > 1 and len(parts[-1]) != 3:
            value = "".join(parts[:-1]) + "." + parts[-1]
        else:
            value = "".join(parts)
        normalized.append(str(Decimal(value).normalize()))
    return sorted(normalized)


def deduplicate(items):
    seen = set()
    output = []
    for item in items:
        # Only exact bilingual answer duplicates are discarded; similar questions can contain distinct facts.
        key = tuple(
            re.sub(r"\W+", "", unicodedata.normalize("NFKC", item[k]).casefold())
            for k in ("answer_pt", "answer_en")
        )
        if key not in seen:
            seen.add(key)
            output.append(item)
    return output


def deterministic_validation(item, evidence, allow_normative=False):
    by_id = {c["id"]: c for c in evidence}
    cited = [by_id[cid] for cid in item["source_chunk_ids"] if cid in by_id]
    errors = []
    if len(cited) != len(set(item["source_chunk_ids"])) or not cited:
        errors.append(
            "Citação inexistente ou fora das evidências recuperadas do evento atual"
        )
    allowed = (
        {"event_current", "normative_current"} if allow_normative else {"event_current"}
    )
    if any(c["collection"] not in allowed for c in cited):
        errors.append("Histórico e guia linguístico não são evidência factual")
    if allow_normative and not any(c["collection"] == "event_current" for c in cited):
        errors.append("A resposta precisa de vínculo com uma fonte do evento atual")
    if allow_normative:
        claims = item.get("claims", [])
        if not claims or any(
            coverage_key(" ".join(c.get("text_" + lang, "") for c in claims))
            != coverage_key(item["answer_" + lang])
            for lang in ("pt", "en")
        ):
            errors.append(
                "Afirmações PT/EN não cobrem integralmente a resposta; revise cada trecho e suas fontes"
            )
        for claim in claims:
            if not claim["source_chunk_ids"] or not set(
                claim["source_chunk_ids"]
            ) <= set(item["source_chunk_ids"]):
                errors.append("Afirmação sem referência específica válida")
            if numeric_tokens(claim["text_pt"]) != numeric_tokens(
                claim.get("text_en", "")
            ):
                errors.append("Números/datas divergem entre afirmações PT e EN")
            specific_numbers = set(
                numeric_tokens(
                    " ".join(
                        by_id[c]["text"]
                        for c in claim["source_chunk_ids"]
                        if c in by_id
                    )
                )
            )
            if (
                not set(
                    numeric_tokens(claim["text_pt"])
                    + numeric_tokens(claim.get("text_en", ""))
                )
                <= specific_numbers
            ):
                errors.append(
                    "Afirmação contém números ausentes no trecho especificamente citado"
                )
    if numeric_tokens(item["answer_pt"]) != numeric_tokens(item["answer_en"]):
        errors.append("Números/datas divergem entre PT e EN")
    evidence_numbers = set(numeric_tokens(" ".join(c["text"] for c in cited)))
    if (
        not set(numeric_tokens(item["answer_pt"]) + numeric_tokens(item["answer_en"]))
        <= evidence_numbers
    ):
        errors.append("A resposta contém números ausentes nas fontes citadas")
    return errors


def validate_items(items, evidence, allow_normative=False):
    provider = Provider()
    verified = provider.complete(
        "Valide cada item separadamente. supported=true se TODAS as afirmações de ambas as respostas são sustentadas. equivalent=true apenas se perguntas E respostas PT/EN expressam os MESMOS fatos e respondem à pergunta. Trechos bilíngues equivalentes não são conflito; não exija idioma da fonte igual ao da resposta. conflicting_sources=[] se não houver valores ou condições contraditórias. Justifique em português, em uma frase.",
        {
            "items": [
                {
                    k: i[k]
                    for k in (
                        "id",
                        "question_pt",
                        "answer_pt",
                        "question_en",
                        "answer_en",
                        "source_chunk_ids",
                        *(("claims",) if allow_normative else ()),
                    )
                }
                for i in items
            ],
            "event_current": evidence,
        },
        ValidationResult,
    )
    verdicts = {v.id: v for v in verified.items}
    repeated_reasons = Counter(v.reason.strip().casefold() for v in verdicts.values())
    for item in items:
        errors = deterministic_validation(item, evidence, allow_normative)
        verdict = verdicts.get(item["id"])
        inconclusive = bool(
            verdict and repeated_reasons[verdict.reason.strip().casefold()] > 1
        )
        item["grounded"] = bool(
            verdict
            and not inconclusive
            and verdict.supported
            and not errors
            and not verdict.unsupported_claims
            and not verdict.conflicting_sources
        )
        item["pt_en_equivalent"] = bool(
            verdict and verdict.equivalent and not errors and not inconclusive
        )
        item["requires_human_review"] = True
        item["reviewed"] = False
        item["review_note"] = ""
        item["validation"] = {
            "deterministic_errors": errors,
            "semantic": verdict.model_dump() if verdict else None,
            "semantic_inconclusive": inconclusive,
        }
        item["review_reason"] = "; ".join(
            errors + ([verdict.reason] if verdict else ["Modelo não validou este item"])
        )
        if inconclusive:
            item["review_reason"] = (
                "O modelo repetiu a mesma justificativa entre itens. Validação automática inconclusiva; confira fontes e PT/EN manualmente. "
                + item["review_reason"]
            )
    return items
