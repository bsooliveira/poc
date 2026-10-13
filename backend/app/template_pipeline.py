"""Twelve-section report; conservative applicability and PT-before-EN generation."""

import re
import unicodedata
import uuid
import httpx

from .config import settings
from .db import database
from .normatives import retrieve_normatives
from .retrieval import model_id, retrieve, tokens
from .schemas import TemplateAssessment, PTGeneration, Translations
from .template import faq_template, section_definition
from .validation import validate_items, numeric_tokens


def folded(text):
    return (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode()
        .casefold()
    )


def keyword_pattern(keyword):
    word = folded(keyword)
    return r"\b" + re.escape(word) + (r"\b" if word.endswith("s") else r"(?:s|es)?\b")


def topic_matches(section, text):
    return section["id"] == "resumo" or any(
        re.search(keyword_pattern(k), folded(text)) for k in section["keywords"]
    )


def conservative_sections(chunks):
    out = []
    for definition in faq_template()["sections"]:
        matching = [c for c in chunks if topic_matches(definition, c["text"])]
        negative = [
            c
            for c in matching
            if any(
                re.search(
                    r"\b(?:nao (?:ha|havera|se aplica)|there(?: will be| are| is) no|does not apply|not applicable)\b[^.;\n]{0,60}"
                    + keyword_pattern(k),
                    folded(c["text"]),
                )
                for k in definition["keywords"]
            )
            and definition["id"] not in {"resumo", "cronograma"}
        ]
        contradictory = bool(negative) and len(negative) < len(matching)
        status = (
            "insufficient_information"
            if contradictory
            else (
                "not_applicable"
                if negative
                else ("applicable" if matching else "insufficient_information")
            )
        )
        out.append(
            dict(
                section_id=definition["id"],
                status=status,
                reason_pt="Indicações divergentes de aplicabilidade; conferir todas as fontes."
                if contradictory
                else "Indicação nas fontes do evento; confirme aplicabilidade e contexto na revisão."
                if matching
                else "Sem evidências específicas suficientes nas fontes do evento.",
                reason_en="Conflicting applicability indications; check all sources."
                if contradictory
                else "Indicated in the event sources; confirm applicability and context during review."
                if matching
                else "Insufficient specific evidence in the event sources.",
                evidence_chunk_ids=[
                    c["id"]
                    for c in (matching if contradictory else negative or matching)[:3]
                ],
            )
        )
    return out


def timeline_conflicts(chunks):
    fields = {}
    for chunk in chunks:
        for label, date in re.findall(
            r"([A-Za-zÀ-ÿ ]{3,60})\s*[:=]\s*(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})",
            chunk["text"],
        ):
            key = folded(label).strip()
            canonical = "-".join(reversed(date.split("/"))) if "/" in date else date
            fields.setdefault(key, []).append(
                dict(value=canonical, chunk_id=chunk["id"], source=chunk["source_name"])
            )
    conflicts = [
        f"Cronograma divergente ({key}): "
        + "; ".join(f"{v['value']} em {v['source']} [{v['chunk_id']}]" for v in values)
        for key, values in fields.items()
        if len({v["value"] for v in values}) > 1
    ]
    for start_label, start_values in fields.items():
        if "inicio" in start_label:
            end_values = fields.get(start_label.replace("inicio", "fim"), [])
            if end_values and min(v["value"] for v in start_values) > max(
                v["value"] for v in end_values
            ):
                conflicts.append(
                    "Cronograma com início posterior ao fim: " + start_label
                )
    return conflicts, fields


def build_report(event, current, provider, progress=lambda *a, **k: None):
    template = faq_template()
    conservative = {s["section_id"]: s for s in conservative_sections(current)}
    gaps, items, evidence, duplicate_log = [], [], {}, []
    progress("classification")
    try:
        if not current:
            raise ValueError(
                "Sem documentos factuais; nenhuma aplicabilidade pode ser presumida"
            )
        assessment = provider.complete(
            "Classifique o evento e avalie TODAS as 12 seções do template. Não crie seções ou subitens. Só declare não aplicável com exclusão explícita na fonte. Ausência de documento/informação significa insufficient_information. Justificativas PT/EN equivalentes. Cite apenas fontes atuais do evento para a aplicabilidade, nunca procedimentos gerais.",
            {
                "event": {k: event[k] for k in ("name", "event_type", "event_date")},
                "template": [
                    {k: s[k] for k in ("id", "title_pt", "title_en")}
                    for s in template["sections"]
                ],
                "event_current": [
                    {
                        **c,
                        "text": c["text"][
                            : max(150, 6500 // max(1, min(len(current), 30)))
                        ],
                    }
                    for c in current[:30]
                ],
            },
            TemplateAssessment,
        )
        proposed = {}
        for section in assessment.sections:
            if section.section_id in proposed:
                gaps.append(
                    "Modelo repetiu uma avaliação de seção; revisão obrigatória."
                )
            else:
                proposed[section.section_id] = section.model_dump()
        classification = assessment.event_classification
    except (ValueError, httpx.HTTPError):
        proposed, classification = (
            {},
            "Classificação automática inconclusiva; revisão humana necessária.",
        )
        gaps.append(
            "Avaliação do modelo fora do contrato; estrutura mantida com avaliação conservadora."
        )
    if len(current) > 30:
        gaps.append(
            "Classificação avaliou resumos de 30 chunks; conferir cobertura do restante."
        )
    kinds = {c["kind"] for c in current}
    if "official" not in kinds:
        gaps.append("Documento oficial do evento ausente.")
    if "financial" not in kinds:
        gaps.append("Arquivo financeiro ausente.")
    if "transcript" not in kinds:
        gaps.append("Transcrição da reunião ausente.")
    conflicts, schedule = timeline_conflicts(current)
    conflicts.extend(
        "Aplicabilidade divergente: "
        + section_definition(sid)["title_pt"]
        + " · "
        + ", ".join(s["evidence_chunk_ids"])
        for sid, s in conservative.items()
        if s["reason_pt"].startswith("Indicações divergentes")
    )
    sections, seen_answers = [], {}
    for definition in template["sections"]:
        sid = definition["id"]
        safe = conservative[sid]
        section = dict(proposed.get(sid, safe))
        if safe["reason_pt"].startswith("Indicações divergentes"):
            section = dict(safe)
        relevant_ids = {
            c["id"] for c in current if topic_matches(definition, c["text"])
        }
        section["evidence_chunk_ids"] = [
            cid for cid in section["evidence_chunk_ids"] if cid in relevant_ids
        ]
        if not section["evidence_chunk_ids"] and safe["evidence_chunk_ids"]:
            section = dict(safe)
            gaps.append(
                "Avaliação do modelo sem citação pertinente em "
                + definition["title_pt"]
                + "; indicação nas fontes mantida para revisão."
            )
        if section["status"] == "not_applicable" and safe["status"] != "not_applicable":
            section = dict(safe)
            section["status"] = "insufficient_information"
        if section["status"] == "applicable" and (
            not section["evidence_chunk_ids"]
            or safe["status"] == "insufficient_information"
        ):
            section = dict(safe)
            section["status"] = "insufficient_information"
        section.update(reviewed=False, review_note="", item_ids=[])
        evidence.update(
            {c["id"]: c for c in current if c["id"] in section["evidence_chunk_ids"]}
        )
        sections.append(section)
        if section["status"] != "applicable":
            continue
        progress("retrieval", domain=definition["title_pt"])
        with database() as db:
            ranked = retrieve(db, event["id"], definition["title_pt"], top_k=3)
            factual = [c for c in current if c["id"] in section["evidence_chunk_ids"]]
            factual_ids = {c["id"] for c in factual}
            factual += [
                c
                for c in ranked
                if c["id"] not in factual_ids and topic_matches(definition, c["text"])
            ]
            factual = factual[:4]
            normative = retrieve_normatives(
                db,
                definition["title_pt"] + " " + " ".join(definition["keywords"]),
                definition["systems"],
                top_k=2,
                as_of=event["event_date"] or None,
            )
            history = retrieve(
                db,
                event["id"],
                definition["title_pt"],
                "faq_history_approved",
                top_k=1,
                company=event["company"],
            )
            language = retrieve(
                db,
                event["id"],
                definition["title_pt"],
                "language_guidelines",
                top_k=1,
                threshold=0,
            )
        selected = factual + normative
        evidence.update({c["id"]: c for c in selected})
        if definition["systems"] and not normative:
            gaps.append(
                "Sem normativo vigente recuperado para " + definition["title_pt"]
            )
        progress("generation", domain=definition["title_pt"])
        try:
            generated = provider.complete(
                "Elabore de 1 a 3 perguntas e respostas SOMENTE em PT-BR para a seção indicada. Cada afirmação exige fonte específica citada. Documento do evento, financeiro e transcrição descrevem o caso; normativos gerais apenas sustentam procedimentos se aplicáveis. Não transforme regras da Câmara em procedimentos da Depositária. Não invente valores, regras, tributos ou contatos. Não copie nem repita respostas anteriores. Divergências devem ser explicitadas, sem escolher silenciosamente uma fonte. Não gere inglês nesta etapa. Liste cada afirmação literal de answer_pt em claims com os IDs específicos que a sustentam; answer_pt deve corresponder à concatenação das afirmações.",
                {
                    "domain": definition["title_pt"],
                    "event_current": factual,
                    "normative_current": normative,
                    "faq_history_approved": history,
                    "language_guidelines": language,
                    "previous_answers": [i["answer_pt"][:400] for i in items[-6:]],
                },
                PTGeneration,
            )
            gaps.extend(generated.gaps)
            conflicts.extend(generated.conflicts)
            batch = []
            selected_ids = {c["id"] for c in selected}
            for pt in generated.items:
                if not set(pt.source_chunk_ids) <= selected_ids or not set(
                    pt.source_chunk_ids
                ) & {c["id"] for c in factual}:
                    gaps.append(
                        "Resposta descartada por citações inválidas em "
                        + definition["title_pt"]
                    )
                    continue
                duplicate_key = (
                    pt.answer_pt.strip().casefold(),
                    tuple(sorted(pt.source_chunk_ids)),
                )
                if duplicate_key in seen_answers:
                    duplicate_log.append(
                        dict(
                            section_id=sid,
                            consolidated_into=seen_answers[duplicate_key],
                            question_pt=pt.question_pt,
                        )
                    )
                    continue
                item_id = str(
                    uuid.uuid5(
                        uuid.NAMESPACE_URL,
                        event["id"]
                        + ":"
                        + sid
                        + ":"
                        + pt.question_pt
                        + ":"
                        + ",".join(sorted(pt.source_chunk_ids)),
                    )
                )
                if any(i["id"] == item_id for i in batch):
                    conflicts.append(
                        "Pergunta com respostas divergentes na mesma evidência: "
                        + pt.question_pt
                        + " · "
                        + ", ".join(pt.source_chunk_ids)
                    )
                    gaps.append(
                        "Pergunta repetida com respostas diferentes; revisar "
                        + definition["title_pt"]
                    )
                    continue
                batch.append(
                    dict(
                        **pt.model_dump(),
                        id=item_id,
                        section_id=sid,
                        domain=definition["title_pt"],
                        confidence=0,
                        state="pending_review",
                        languages=["pt-BR", "en"],
                    )
                )
            if not batch:
                section["generation_warning"] = (
                    "Nenhuma pergunta exclusiva e fundamentada produzida; revisar a seção."
                )
                continue
            progress("translation", domain=definition["title_pt"])
            translated = provider.complete(
                "Traduza para EN cada pergunta/resposta PT-BR, preservando identificadores, fatos, números, datas, negações e condições. Não acrescente informação das fontes que não consta em PT. A tradução deve responder à mesma pergunta. claims_en deve traduzir cada claims.text_pt na mesma ordem, e answer_en deve corresponder à concatenação de claims_en.",
                {
                    "items": batch,
                    "event_current": factual,
                    "normative_current": normative,
                },
                Translations,
            )
            english = {i.id: i for i in translated.items}
            if set(english) != {i["id"] for i in batch} or len(translated.items) != len(
                batch
            ):
                raise ValueError("Tradução não preservou todos os identificadores")
            for item in batch:
                item.update(
                    question_en=english[item["id"]].question_en,
                    answer_en=english[item["id"]].answer_en,
                )
                for index, claim in enumerate(item["claims"]):
                    claim["text_en"] = (
                        english[item["id"]].claims_en[index]
                        if index < len(english[item["id"]].claims_en)
                        else ""
                    )
            progress("validation", domain=definition["title_pt"])
            validated = validate_items(batch, selected, allow_normative=True)
            for item in validated:
                if not topic_matches(
                    definition, item["question_pt"] + " " + item["answer_pt"]
                ):
                    item["classification_warning"] = (
                        "Conteúdo pode não corresponder à seção; confirme a classificação."
                    )
                    item["review_reason"] = (
                        item["classification_warning"] + " " + item["review_reason"]
                    )
                item["source_evidence"] = [
                    c for c in selected if c["id"] in item["source_chunk_ids"]
                ]
                seen_answers[
                    (
                        item["answer_pt"].strip().casefold(),
                        tuple(sorted(item["source_chunk_ids"])),
                    )
                ] = item["id"]
                section["item_ids"].append(item["id"])
            items.extend(validated)
        except (ValueError, httpx.HTTPError) as exc:
            section.update(
                status="insufficient_information",
                generation_warning=str(exc),
                reason_pt="A geração ou validação automática foi inconclusiva; seção preservada para revisão.",
                reason_en="Generation or validation was inconclusive; section retained for review.",
            )
            gaps.append("Geração inconclusiva em " + definition["title_pt"])
    for section in sections:
        if section["status"] == "insufficient_information":
            gaps.append(
                section_definition(section["section_id"])["title_pt"]
                + ": informação insuficiente"
            )
    for index, item in enumerate(items):
        for previous in items[:index]:
            left, right = (
                set(tokens(item["question_pt"])),
                set(tokens(previous["question_pt"])),
            )
            similarity = len(left & right) / max(1, len(left | right))
            if similarity > 0.85 and numeric_tokens(
                item["answer_pt"]
            ) == numeric_tokens(previous["answer_pt"]):
                item["possible_duplicate_of"] = previous["id"]
                item["review_reason"] = (
                    "Possível redundância; conferir condições e consolidar se necessário. "
                    + item["review_reason"]
                )
    used = {cid for i in items for cid in i["source_chunk_ids"]}
    current_ids = {c["id"] for c in current}
    cited = used & current_ids
    missing = {c["source_name"] for c in current} - {
        c["source_name"] for c in current if c["id"] in cited
    }
    gaps.extend("Fonte sem citação na FAQ: " + name for name in sorted(missing))
    conflicts.extend(
        text
        for i in items
        for text in (i["validation"].get("semantic") or {}).get(
            "conflicting_sources", []
        )
    )
    progress("consolidation")
    return dict(
        template_version=template["version"],
        template_snapshot=template,
        sections=sections,
        event_classification=classification,
        timeline_checks=schedule,
        deduplication=duplicate_log,
        items=items,
        domains=sections,
        gaps=list(dict.fromkeys(gaps)),
        conflicts=list(dict.fromkeys(conflicts)),
        evidence=list(evidence.values()),
        model=provider.model,
        provider=settings().llm_provider,
        prompt_version=settings().prompt_version,
        embedding_model=model_id(),
        metrics=dict(
            chunk_coverage=len(cited) / max(1, len(current)),
            total_chunks=len(current),
            used_chunks=len(cited),
            source_coverage=1 - len(missing) / len({c["source_name"] for c in current})
            if current
            else 0,
            grounded_rate=sum(i["grounded"] for i in items) / max(1, len(items)),
            equivalence_rate=sum(i["pt_en_equivalent"] for i in items)
            / max(1, len(items)),
        ),
    )
