import json
import logging
import threading
import hashlib
import uuid
from pathlib import Path

from .config import settings
from .db import audit, database, dumps, now, uid
from .generation import Provider
from .ingestion import SOURCE_TYPES, chunk_sections
from .retrieval import embed, model_id, retrieve
from .schemas import Classification, GeneratedFAQ
from .validation import deduplicate, validate_items

log = logging.getLogger(__name__)


def stage(run_id, name, **details):
    with database(True) as db:
        run = db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        db.execute("UPDATE runs SET stage=? WHERE id=?", (name, run_id))
        audit(
            db,
            run["actor"],
            "processing.stage",
            run["event_id"],
            run_id=run_id,
            stage=name,
            **details,
        )


def index_event(event_id, allow_empty=False):
    with database() as db:
        sources = db.execute(
            """SELECT s.* FROM sources s WHERE event_id=? AND version=(
            SELECT max(s2.version) FROM sources s2 WHERE s2.event_id=s.event_id AND s2.name=s.name)""",
            (event_id,),
        ).fetchall()
    chunks = []
    for source in sources:
        sections = json.loads(
            Path(source["path"] + ".json").read_text(encoding="utf-8")
        )
        collection, priority, _ = SOURCE_TYPES[source["kind"]]
        for chunk in chunk_sections(sections):
            chunks.append(
                {
                    **chunk,
                    "id": str(
                        uuid.uuid5(
                            uuid.NAMESPACE_URL,
                            source["id"]
                            + ":"
                            + chunk["location"]
                            + ":"
                            + hashlib.sha256(chunk["text"].encode()).hexdigest(),
                        )
                    ),
                    "source_id": source["id"],
                    "source_name": source["name"],
                    "collection": collection,
                    "kind": source["kind"],
                    "priority": priority,
                    "source_version": source["version"],
                    "source_sha256": source["sha256"],
                }
            )
    if not allow_empty and not any(c["collection"] == "event_current" for c in chunks):
        raise ValueError("Envie ao menos uma fonte factual do evento atual")
    vectors = embed([c["text"] for c in chunks]) if chunks else []
    with database(True) as db:
        db.execute(
            "DELETE FROM chunks WHERE event_id=? AND collection!='faq_history_approved'",
            (event_id,),
        )
        for c, vector in zip(chunks, vectors):
            db.execute(
                """INSERT INTO chunks(id,event_id,source_id,source_name,collection,kind,priority,text,location,vector,embedding_model,metadata)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    c["id"],
                    event_id,
                    c["source_id"],
                    c["source_name"],
                    c["collection"],
                    c["kind"],
                    c["priority"],
                    c["text"],
                    c["location"],
                    dumps(vector),
                    model_id(),
                    dumps({k: c[k] for k in ("source_version", "source_sha256")}),
                ),
            )
    return chunks


def execute_run(run):
    event_id, run_id = run["event_id"], run["id"]
    try:
        stage(run_id, "indexing")
        template_mode = json.loads(run["details"]).get("mode", "legacy") == "template"
        chunks = index_event(event_id, allow_empty=template_mode)
        current = [c for c in chunks if c["collection"] == "event_current"]
        with database() as db:
            event = dict(
                db.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
            )
        provider = Provider()
        if json.loads(run["details"]).get("mode", "legacy") == "template":
            from .template_pipeline import build_report

            result = build_report(
                event, current, provider, lambda name, **kw: stage(run_id, name, **kw)
            )
            result["run_id"] = run_id
            with database(True) as db:
                db.execute(
                    "UPDATE events SET status='review',result=?,version=version+1,error=NULL WHERE id=?",
                    (dumps(result), event_id),
                )
                db.execute(
                    "UPDATE runs SET status='completed',stage='review',finished_at=?,details=? WHERE id=?",
                    (
                        now(),
                        dumps({"mode": "template", "metrics": result["metrics"]}),
                        run_id,
                    ),
                )
                audit(
                    db,
                    run["actor"],
                    "processing.completed",
                    event_id,
                    run_id=run_id,
                    template_version=result["template_version"],
                )
            return
        stage(run_id, "classification", chunks=len(chunks), embedding_model=model_id())
        classification = provider.complete(
            "Classifique em até 3 temas distintos sobre os quais participantes precisam de respostas (ex.: agenda, inscrição/acesso, materiais). Domínios em português. Não use idioma nem formato do arquivo como domínio. Razões em uma frase, cite IDs reais.",
            {
                "event": {
                    k: event[k] for k in ("name", "company", "event_type", "event_date")
                },
                "event_current": [
                    {
                        **c,
                        "text": c["text"][: max(120, 7000 // min(len(current), 40))]
                        + (
                            "\n[...]\n" + c["text"][-70:]
                            if len(c["text"]) > max(120, 7000 // min(len(current), 40))
                            else ""
                        ),
                    }
                    for c in current[:40]
                ],
            },
            Classification,
        )
        current_ids = {c["id"] for c in current}
        domains = []
        for decision in classification.domains:
            valid = [cid for cid in decision.evidence_chunk_ids if cid in current_ids]
            if (
                decision.applicable
                and valid
                and decision.domain not in {d.domain for d in domains}
            ):
                decision.evidence_chunk_ids = valid
                domains.append(decision)
        if not domains:
            raise ValueError(
                "O modelo não classificou domínios com citações válidas. Ajuste as fontes ou tente novamente."
            )
        gaps, conflicts, items, evidence_map, retrieval_log = (
            list(classification.gaps),
            [],
            [],
            {},
            [],
        )
        if len(current) > 40:
            gaps.append(
                "Classificação usou trechos de 40 chunks; revise a cobertura dos demais documentos indexados."
            )
        if len(domains) > 3:
            gaps.append(
                "A POC processa até três domínios por execução; revise a cobertura dos demais temas classificados."
            )
        for decision in domains[:3]:
            stage(run_id, "retrieval", domain=decision.domain)
            query = decision.domain + " " + decision.reason
            with database() as db:
                factual = retrieve(db, event_id, query)
                factual_ids = {c["id"] for c in factual}
                # Include classification evidence regardless of threshold, maintaining source priority.
                for c in current:
                    if (
                        c["id"] in decision.evidence_chunk_ids
                        and c["id"] not in factual_ids
                    ):
                        factual.append(c)
                factual = sorted(factual, key=lambda c: c["priority"])[:12]
                history = retrieve(
                    db,
                    event_id,
                    query,
                    "faq_history_approved",
                    top_k=2,
                    company=event["company"],
                )
                linguistic = retrieve(
                    db, event_id, query, "language_guidelines", top_k=2, threshold=0
                )
            retrieval_log.append(
                {
                    "domain": decision.domain,
                    "chunks": [
                        {
                            "id": c["id"],
                            "score": c.get("score"),
                            "rerank_score": c.get("rerank_score"),
                            "priority": c["priority"],
                        }
                        for c in factual
                    ],
                    "history": [c["id"] for c in history],
                    "guidelines": [c["id"] for c in linguistic],
                }
            )
            evidence_map.update({c["id"]: c for c in factual})
            stage(run_id, "generation", domain=decision.domain)
            generated = provider.complete(
                "Gere de 1 a 3 perguntas somente sobre o domínio indicado. Cada resposta PT deve responder sua pergunta; EN deve traduzir exatamente pergunta e resposta PT, sem fato adicional. Use frases curtas, números em algarismos (12 p.m., não noon). Não repita perguntas já geradas. Cite IDs de event_current. Histórico só orienta estrutura.",
                {
                    "domain": decision.domain,
                    "event_current": factual,
                    "faq_history_approved": history,
                    "language_guidelines": linguistic,
                    "previous_questions": [i["question_pt"] for i in items],
                },
                GeneratedFAQ,
            )
            batch = []
            for item in generated.items:
                item.id = uid()
                item.domain = decision.domain
                batch.append(item.model_dump())
            stage(run_id, "validation", domain=decision.domain)
            batch = validate_items(batch, factual)
            items.extend(batch)
            gaps.extend(generated.gaps)
            conflicts.extend(generated.conflicts)
        stage(run_id, "consolidation")
        items = deduplicate(items)
        if not items:
            raise ValueError("Nenhuma pergunta válida foi produzida")
        used = {
            cid for i in items for cid in i["source_chunk_ids"] if cid in current_ids
        }
        missing_sources = {c["source_name"] for c in current} - {
            c["source_name"] for c in current if c["id"] in used
        }
        gaps.extend(
            "Fonte sem citação na FAQ: " + name for name in sorted(missing_sources)
        )
        conflicts.extend(
            conflict
            for item in items
            for conflict in (item["validation"].get("semantic") or {}).get(
                "conflicting_sources", []
            )
        )
        result = {
            "items": items,
            "domains": [d.model_dump() for d in domains],
            "gaps": list(dict.fromkeys(gaps)),
            "conflicts": list(dict.fromkeys(conflicts)),
            "evidence": list(evidence_map.values()),
            "retrieval": retrieval_log,
            "model": provider.model,
            "provider": settings().llm_provider,
            "prompt_version": settings().prompt_version,
            "embedding_model": model_id(),
            "run_id": run_id,
            "metrics": {
                "chunk_coverage": round(len(used) / len(current), 3),
                "total_chunks": len(current),
                "used_chunks": len(used),
                "source_coverage": round(
                    1 - len(missing_sources) / len({c["source_name"] for c in current}),
                    3,
                ),
                "grounded_rate": sum(i["grounded"] for i in items) / len(items),
                "equivalence_rate": sum(i["pt_en_equivalent"] for i in items)
                / len(items),
            },
        }
        with database(True) as db:
            db.execute(
                "UPDATE events SET status='review',result=?,version=version+1,error=NULL WHERE id=?",
                (dumps(result), event_id),
            )
            db.execute(
                "UPDATE runs SET status='completed',stage='review',finished_at=?,details=? WHERE id=?",
                (
                    now(),
                    dumps({"retrieval": retrieval_log, "metrics": result["metrics"]}),
                    run_id,
                ),
            )
            audit(
                db,
                run["actor"],
                "processing.completed",
                event_id,
                run_id=run_id,
                model=provider.model,
                prompt_version=settings().prompt_version,
                validations=result["metrics"],
                chunks=list(evidence_map),
            )
    except Exception as exc:
        # Never log provider response bodies or credentials.
        message = (
            str(exc)[:400]
            if isinstance(exc, ValueError)
            else f"Falha de processamento ({type(exc).__name__}). Consulte a disponibilidade do modelo e tente novamente."
        )
        log.error("Run %s failed (%s)", run_id, type(exc).__name__)
        with database(True) as db:
            db.execute(
                "UPDATE events SET status='failed',error=? WHERE id=?",
                (message, event_id),
            )
            db.execute(
                "UPDATE runs SET status='failed',stage='failed',finished_at=?,details=? WHERE id=?",
                (now(), dumps({"error": message}), run_id),
            )
            audit(
                db,
                run["actor"],
                "processing.failed",
                event_id,
                run_id=run_id,
                error=message,
            )


class Worker:
    def __init__(self):
        self.stop_event = threading.Event()
        self.thread = threading.Thread(
            target=self.loop, daemon=True, name="simplfaq-worker"
        )

    def start(self):
        with database(True) as db:
            interrupted = db.execute(
                "SELECT * FROM runs WHERE status='running'"
            ).fetchall()
            for run in interrupted:
                db.execute(
                    "UPDATE runs SET status='failed',stage='interrupted',finished_at=? WHERE id=?",
                    (now(), run["id"]),
                )
                db.execute(
                    "UPDATE events SET status='failed',error='Execução interrompida por reinício. Execute novamente.' WHERE id=?",
                    (run["event_id"],),
                )
                audit(
                    db,
                    "system",
                    "processing.interrupted",
                    run["event_id"],
                    run_id=run["id"],
                )
            for training in db.execute(
                "SELECT id FROM trainings WHERE status='running'"
            ).fetchall():
                db.execute(
                    "UPDATE trainings SET status='failed',error='Treinamento interrompido por reinício',finished_at=? WHERE id=?",
                    (now(), training["id"]),
                )
                audit(db, "system", "training.interrupted", training_id=training["id"])
            db.execute(
                "UPDATE normative_jobs SET status='failed',finished_at=?,error='Atualização interrompida por reinício; tente novamente' WHERE status='running'",
                (now(),),
            )
        self.thread.start()

    def loop(self):
        while not self.stop_event.is_set():
            try:
                with database(True) as db:
                    run = db.execute(
                        "SELECT * FROM runs WHERE status='queued' ORDER BY created_at LIMIT 1"
                    ).fetchone()
                    if run:
                        run = dict(run)
                        db.execute(
                            "UPDATE runs SET status='running',started_at=? WHERE id=?",
                            (now(), run["id"]),
                        )
                        db.execute(
                            "UPDATE events SET status='processing' WHERE id=?",
                            (run["event_id"],),
                        )
                        audit(
                            db,
                            run["actor"],
                            "processing.started",
                            run["event_id"],
                            run_id=run["id"],
                            model=run["model"],
                            prompt_version=run["prompt_version"],
                        )
                if run:
                    execute_run(run)
                else:
                    from .finetuning import process_next_training
                    from .normatives import process_next_normative

                    if not process_next_normative():
                        process_next_training()
            except Exception as exc:
                log.error("Worker cycle failed (%s)", type(exc).__name__)
            self.stop_event.wait(1)

    def stop(self):
        self.stop_event.set()
        self.thread.join(timeout=5)
