import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit
from typing import Literal

import httpx
from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.responses import FileResponse, JSONResponse, Response

from .auth import identity
from .config import settings
from .db import audit, database, dumps, event_dict, initialize, now, uid
from .generation import Provider
from .ingestion import EXTENSIONS, SOURCE_TYPES, digest, extract, safe_name
from .orchestration import Worker
from .output import document_bytes
from .retrieval import embed, model_id, public_chunk, retrieve
from .schemas import Decision, EventCreate, ItemEdit, SectionReview
from .template import faq_template, section_definition
from .normatives import (
    NORMATIVE_QUERY,
    public_evidence,
    public_manual,
    retrieve_normatives,
    stale_references,
    enqueue_refresh,
)
from .validation import deterministic_validation, numeric_tokens


@asynccontextmanager
async def lifespan(app):
    initialize()
    worker = Worker()
    worker.start()
    yield
    worker.stop()


app = FastAPI(
    title="SimpliFAQ",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.middleware("http")
async def same_origin(request: Request, call_next):
    origin = request.headers.get("origin")
    if origin and urlsplit(origin).netloc != request.headers.get("host"):
        return JSONResponse({"detail": "Origem não autorizada"}, status_code=403)
    if request.method in {"POST", "PUT", "PATCH"}:
        try:
            size = int(request.headers.get("content-length", "0"))
        except ValueError:
            return JSONResponse({"detail": "Content-Length inválido"}, status_code=400)
        if size > settings().max_batch_mb * 1024 * 1024 + 1024 * 1024:
            return JSONResponse(
                {"detail": "Requisição excede o limite"}, status_code=413
            )
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def get_event(db, event_id):
    row = db.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Evento não encontrado")
    return event_dict(row)


def editable(event, expected=None):
    if event["status"] in {"queued", "processing", "approved"}:
        raise HTTPException(
            409,
            "Evento em processamento ou aprovado; crie outro evento para uma nova versão aprovada",
        )
    if expected is not None and event["version"] != expected:
        raise HTTPException(
            409, "O evento foi alterado. Atualize a página antes de salvar."
        )


def snapshot(db, event, actor):
    if event["result"]:
        db.execute(
            "INSERT INTO revisions VALUES (?,?,?,?,?,?)",
            (
                uid(),
                event["id"],
                event["version"],
                dumps(event["result"]),
                now(),
                actor,
            ),
        )


@app.get("/api/health/live")
def live():
    return {"status": "ok"}


@app.get("/api/health/ready")
def ready():
    with database() as db:
        db.execute("SELECT count(*) FROM events").fetchone()
    return {"status": "ready", "version": "1.0.0"}


@app.get("/api/config")
def config():
    cfg = settings()
    return {
        "auth_mode": cfg.auth_mode,
        "tenant_id": cfg.entra_tenant_id,
        "client_id": cfg.entra_client_id,
        "scope": f"api://{cfg.entra_audience}/{cfg.entra_scope}",
        "provider": cfg.llm_provider,
        "model": Provider().model,
        "embedding_model": model_id(),
        "max_upload_mb": cfg.max_upload_mb,
        "extensions": sorted(EXTENSIONS),
        "source_types": {k: v[2] for k, v in SOURCE_TYPES.items()},
        "template": faq_template(),
    }


@app.get("/api/me")
def me(user=Depends(identity)):
    return user


@app.get("/api/template")
def template_definition(user=Depends(identity)):
    return faq_template()


@app.get("/api/normatives")
def normative_catalog(user=Depends(identity)):
    with database() as db:
        documents = [
            public_manual(r)
            for r in db.execute(
                "SELECT * FROM normative_documents ORDER BY system,effective_from DESC"
            )
        ]
        jobs = [
            {**dict(r), "report": json.loads(r["report"]) if r["report"] else []}
            for r in db.execute(
                "SELECT * FROM normative_jobs ORDER BY created_at DESC LIMIT 20"
            )
        ]
    return {"documents": documents, "jobs": jobs}


@app.post("/api/normatives/refresh", status_code=202)
def refresh_normatives(user=Depends(identity)):
    try:
        return {"id": enqueue_refresh(user["id"]), "status": "queued"}
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from None


@app.get("/api/normatives/search")
def search_normatives(
    q: str = Query(min_length=3, max_length=500),
    system: Literal["camara", "depositaria"] = "depositaria",
    version: str | None = None,
    user=Depends(identity),
):
    with database() as db:
        return retrieve_normatives(db, q, [system], version=version)


@app.post("/api/normatives/{document_id}/deactivate")
def deactivate_normative(document_id: str, user=Depends(identity)):
    with database(True) as db:
        if not db.execute(
            "SELECT 1 FROM normative_documents WHERE id=?", (document_id,)
        ).fetchone():
            raise HTTPException(404, "Manual não encontrado")
        if db.execute(
            "SELECT 1 FROM normative_jobs WHERE status IN ('queued','running')"
        ).fetchone():
            raise HTTPException(409, "Atualização em andamento")
        db.execute(
            "UPDATE normative_documents SET status='inactive' WHERE id=?",
            (document_id,),
        )
        audit(db, user["id"], "normative.deactivated", document_id=document_id)
    return {"status": "inactive"}


@app.get("/api/system")
def system(user=Depends(identity)):
    cfg = settings()
    models, model_error = [], None
    if cfg.llm_provider == "ollama":
        try:
            response = httpx.get(
                cfg.ollama_url + "/api/tags", timeout=5, trust_env=False
            )
            response.raise_for_status()
            models = [m["name"] for m in response.json()["models"]]
        except (httpx.HTTPError, KeyError):
            model_error = "O serviço local de modelos não está disponível"
    with database() as db:
        totals = {
            t: db.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
            for t in ("events", "sources", "chunks", "audit")
        }
    return {
        "models": models,
        "model_error": model_error,
        "totals": totals,
        "provider": cfg.llm_provider,
        "model": Provider().model,
        "embedding_model": model_id(),
        "training_model": cfg.training_model,
    }


@app.get("/api/events")
def events(user=Depends(identity)):
    with database() as db:
        return [
            dict(r)
            for r in db.execute("""SELECT e.id,e.name,e.company,e.event_type,e.event_date,e.status,e.version,e.created_at,
            (SELECT count(*) FROM sources s WHERE s.event_id=e.id) AS source_count
            FROM events e ORDER BY created_at DESC LIMIT 500""")
        ]


@app.post("/api/events", status_code=201)
def create_event(body: EventCreate, user=Depends(identity)):
    event_id = uid()
    with database(True) as db:
        db.execute(
            "INSERT INTO events(id,name,company,event_type,event_date,created_at,created_by) VALUES (?,?,?,?,?,?,?)",
            (
                event_id,
                body.name.strip(),
                body.company.strip(),
                body.event_type,
                str(body.event_date) if body.event_date else None,
                now(),
                user["id"],
            ),
        )
        audit(db, user["id"], "event.created", event_id, name=body.name)
        return get_event(db, event_id)


@app.get("/api/events/{event_id}")
def event_detail(event_id: str, user=Depends(identity)):
    with database() as db:
        event = get_event(db, event_id)
        event["sources"] = [
            dict(r)
            for r in db.execute(
                "SELECT id,name,kind,size,sha256,version,created_at FROM sources WHERE event_id=? ORDER BY created_at",
                (event_id,),
            )
        ]
        event["runs"] = [
            dict(r)
            for r in db.execute(
                "SELECT * FROM runs WHERE event_id=? ORDER BY created_at DESC",
                (event_id,),
            )
        ]
        if event["result"] and event["result"].get("template_version"):
            event["normative_warnings"] = stale_references(
                db,
                event["result"]["evidence"],
                {
                    cid
                    for item in event["result"]["items"]
                    for cid in item["source_chunk_ids"]
                },
            )
        return event


@app.post("/api/events/{event_id}/sources", status_code=201)
async def upload(
    event_id: str,
    files: list[UploadFile] = File(...),
    kind: str = Form("official"),
    user=Depends(identity),
):
    if kind not in SOURCE_TYPES:
        raise HTTPException(
            422, "Tipo de fonte inválido; histórico só é criado pela aprovação"
        )
    with database() as db:
        editable(get_event(db, event_id))
    prepared, total, names = [], 0, set()
    for file in files:
        try:
            name = safe_name(file.filename)
            if name in names:
                raise ValueError(
                    "Não envie o mesmo nome de arquivo duas vezes no mesmo lote"
                )
            names.add(name)
            data = await file.read(settings().max_upload_mb * 1024 * 1024 + 1)
            total += len(data)
            if total > settings().max_batch_mb * 1024 * 1024:
                raise ValueError("O lote excede o limite de upload")
            sections = await asyncio.to_thread(extract, name, data)
            prepared.append((name, data, sections))
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from None
        finally:
            await file.close()
    written, created = [], []
    try:
        with database(True) as db:
            event = get_event(db, event_id)
            editable(event)
            for name, data, sections in prepared:
                checksum = digest(data)
                previous = db.execute(
                    "SELECT * FROM sources WHERE event_id=? AND name=? ORDER BY version DESC LIMIT 1",
                    (event_id, name),
                ).fetchone()
                if (
                    previous
                    and previous["sha256"] == checksum
                    and previous["kind"] == kind
                ):
                    continue
                source_id = uid()
                path = settings().data_dir / "originals" / source_id
                path.write_bytes(data)
                written.append(path)
                sidecar = Path(str(path) + ".json")
                sidecar.write_text(dumps(sections), encoding="utf-8")
                written.append(sidecar)
                version = previous["version"] + 1 if previous else 1
                db.execute(
                    "INSERT INTO sources VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (
                        source_id,
                        event_id,
                        name,
                        kind,
                        checksum,
                        len(data),
                        version,
                        str(path),
                        now(),
                        user["id"],
                    ),
                )
                created.append({"id": source_id, "name": name, "version": version})
                audit(
                    db,
                    user["id"],
                    "source.uploaded",
                    event_id,
                    source_id=source_id,
                    name=name,
                    sha256=checksum,
                    version=version,
                    kind=kind,
                    size=len(data),
                )
            if not created:
                raise HTTPException(409, "Os arquivos já estão na versão atual")
            snapshot(db, event, user["id"])
            db.execute(
                "UPDATE events SET status='draft',result=NULL,error=NULL,version=version+1 WHERE id=?",
                (event_id,),
            )
            db.execute(
                "DELETE FROM chunks WHERE event_id=? AND collection!='faq_history_approved'",
                (event_id,),
            )
    except Exception:
        for path in written:
            path.unlink(missing_ok=True)
        raise
    return {"sources": created}


@app.post("/api/events/{event_id}/runs", status_code=202)
def generate(
    event_id: str,
    mode: Literal["template", "legacy"] = "template",
    user=Depends(identity),
):
    with database(True) as db:
        event = get_event(db, event_id)
        editable(event)
        if (
            mode == "legacy"
            and not db.execute(
                "SELECT 1 FROM sources WHERE event_id=? AND kind!='language_guide'",
                (event_id,),
            ).fetchone()
        ):
            raise HTTPException(422, "Envie uma fonte factual antes de gerar")
        if (
            db.execute(
                "SELECT 1 FROM trainings WHERE status IN ('queued','running')"
            ).fetchone()
            or db.execute(
                "SELECT 1 FROM normative_jobs WHERE status IN ('queued','running')"
            ).fetchone()
        ):
            raise HTTPException(409, "Aguarde o fine-tuning concluir antes de gerar")
        run_id = uid()
        snapshot(db, event, user["id"])
        db.execute(
            "INSERT INTO runs(id,event_id,status,stage,created_at,actor,model,prompt_version,details) VALUES (?,?,'queued','queued',?,?,?,?,?)",
            (
                run_id,
                event_id,
                now(),
                user["id"],
                Provider().model,
                settings().prompt_version,
                dumps({"mode": mode}),
            ),
        )
        db.execute(
            "UPDATE events SET status='queued',result=NULL,error=NULL,version=version+1 WHERE id=?",
            (event_id,),
        )
        audit(db, user["id"], "processing.queued", event_id, run_id=run_id)
        return {"id": run_id, "status": "queued"}


@app.get("/api/events/{event_id}/chunks")
def chunks(event_id: str, user=Depends(identity)):
    with database() as db:
        get_event(db, event_id)
        return [
            public_chunk(r)
            for r in db.execute(
                "SELECT * FROM chunks WHERE event_id=? ORDER BY priority,source_name,location",
                (event_id,),
            )
        ]


@app.get("/api/events/{event_id}/search")
def search(
    event_id: str,
    q: str = Query(min_length=2, max_length=500),
    top_k: int = Query(8, ge=1, le=30),
    user=Depends(identity),
):
    with database() as db:
        event = get_event(db, event_id)
        if event["status"] in {"draft", "queued", "processing"}:
            raise HTTPException(409, "A indexação precisa estar concluída")
        result = retrieve(db, event_id, q, top_k=top_k)
    with database(True) as db:
        audit(
            db,
            user["id"],
            "retrieval.searched",
            event_id,
            chunk_ids=[r["id"] for r in result],
        )
    return result


@app.patch("/api/events/{event_id}/items/{item_id}")
def edit_item(event_id: str, item_id: str, body: ItemEdit, user=Depends(identity)):
    with database(True) as db:
        event = get_event(db, event_id)
        editable(event, body.expected_version)
        if not event["result"]:
            raise HTTPException(409, "Gere uma FAQ antes de editar")
        result = event["result"]
        templated = bool(result.get("template_version"))
        item = next((i for i in result["items"] if i["id"] == item_id), None)
        if not item:
            raise HTTPException(404, "Pergunta não encontrada")
        current_chunks = [
            public_chunk(r)
            for r in db.execute(
                "SELECT * FROM chunks WHERE event_id=? AND collection='event_current'",
                (event_id,),
            )
        ]
        current_ids = {c["id"] for c in current_chunks}
        if templated:
            normative = [
                public_evidence(r)
                for r in db.execute(
                    NORMATIVE_QUERY + " WHERE d.status='active'"
                ).fetchall()
            ]
            current_chunks.extend(normative)
            current_ids.update(c["id"] for c in normative)
        if not set(body.source_chunk_ids) <= current_ids:
            raise HTTPException(422, "Cite apenas chunks factuais deste evento")
        if body.reviewed and len(body.review_note.strip()) < 10:
            raise HTTPException(
                422, "Descreva a revisão factual e bilíngue em pelo menos 10 caracteres"
            )
        snapshot(db, event, user["id"])
        before = dict(item)
        item.update(body.model_dump(exclude={"expected_version"}, exclude_none=True))
        if templated:
            try:
                definition = section_definition(item["section_id"])
            except StopIteration:
                raise HTTPException(422, "Seção fora do template") from None
            if (
                body.domain
                and body.domain != definition["title_pt"]
                and body.section_id is None
            ):
                raise HTTPException(
                    422, "Selecione uma seção do template para reclassificar"
                )
            item["domain"] = definition["title_pt"]
            if any(
                c["system"] not in definition["systems"]
                for c in current_chunks
                if c["id"] in body.source_chunk_ids
                and c["collection"] == "normative_current"
            ):
                raise HTTPException(
                    422, "Normativo pertence a outro sistema para esta seção"
                )
            if before["section_id"] != item["section_id"]:
                for section in result["sections"]:
                    if section["section_id"] in {
                        before["section_id"],
                        item["section_id"],
                    }:
                        section["reviewed"] = False
            for section in result["sections"]:
                section["item_ids"] = [
                    i["id"]
                    for i in result["items"]
                    if i["section_id"] == section["section_id"]
                ]
        content_fields = (
            "domain",
            "question_pt",
            "answer_pt",
            "question_en",
            "answer_en",
            "source_chunk_ids",
        )
        item["human_edited"] = before.get("human_edited", False) or any(
            item[k] != before[k] for k in content_fields
        )
        if templated and before.get("claims") != item.get("claims"):
            item["human_edited"] = True
        errors = deterministic_validation(
            item, current_chunks, allow_normative=templated
        )
        if body.reviewed and errors:
            raise HTTPException(422, "; ".join(errors))
        item["grounded"] = body.reviewed
        item["pt_en_equivalent"] = body.reviewed
        item["requires_human_review"] = not body.reviewed
        item["review_reason"] = (
            body.review_note
            if body.reviewed
            else "Edição exige nova revisão factual e bilíngue"
        )
        item["reviewed_by"] = user["id"] if body.reviewed else None
        item["reviewed_at"] = now() if body.reviewed else None
        if templated:
            item["state"] = "reviewed" if body.reviewed else "pending_review"
            item["source_evidence"] = [
                c for c in current_chunks if c["id"] in body.source_chunk_ids
            ]
        item["validation"] = {
            "deterministic_errors": errors,
            "human_verified": body.reviewed,
            "previous": before.get("validation"),
        }
        evidence_map = {c["id"]: c for c in result["evidence"]}
        evidence_map.update(
            {c["id"]: c for c in current_chunks if c["id"] in body.source_chunk_ids}
        )
        result["evidence"] = list(evidence_map.values())
        result["metrics"]["human_review_rate"] = sum(
            bool(i.get("reviewed")) for i in result["items"]
        ) / max(1, len(result["items"]))
        result["metrics"]["human_edit_rate"] = sum(
            bool(i.get("human_edited")) for i in result["items"]
        ) / max(1, len(result["items"]))
        db.execute(
            "UPDATE events SET result=?,status='review',version=version+1 WHERE id=?",
            (dumps(result), event_id),
        )
        audit(
            db,
            user["id"],
            "review.item_saved",
            event_id,
            item_id=item_id,
            before=before,
            after=item,
        )
        return get_event(db, event_id)


@app.post("/api/events/{event_id}/decision")
def decide(event_id: str, body: Decision, user=Depends(identity)):
    # Compute embeddings outside the transaction, then compare the version inside the lock.
    with database() as db:
        event = get_event(db, event_id)
        editable(event, body.expected_version)
    if not event["result"] or event["status"] not in {"review", "rejected"}:
        raise HTTPException(409, "Não há resultado pronto para decisão")
    result = event["result"]
    history = []
    if body.decision == "approve":
        if not result["items"]:
            raise HTTPException(
                422,
                "Não há perguntas fundamentadas para aprovar; adicione fontes e elabore a FAQ",
            )
        if result.get("template_version"):
            if len(result.get("sections", [])) != 12 or not all(
                s.get("reviewed") for s in result["sections"]
            ):
                raise HTTPException(
                    422, "Revise as 12 seções, inclusive lacunas e não aplicabilidade"
                )
            with database() as db:
                obsolete = stale_references(
                    db,
                    result["evidence"],
                    {cid for i in result["items"] for cid in i["source_chunk_ids"]},
                )
            if obsolete:
                raise HTTPException(422, "; ".join(obsolete))
        if not all(
            i.get("reviewed") and i.get("grounded") and i.get("pt_en_equivalent")
            for i in result["items"]
        ):
            raise HTTPException(
                422, "Revise e confirme todos os itens antes de aprovar"
            )
        history = [
            f"PT: {i['question_pt']}\n{i['answer_pt']}\nEN: {i['question_en']}\n{i['answer_en']}"
            for i in result["items"]
        ]
        vectors = embed(history)
    with database(True) as db:
        event = get_event(db, event_id)
        editable(event, body.expected_version)
        snapshot(db, event, user["id"])
        approved = body.decision == "approve"
        if approved and result.get("template_version"):
            obsolete = stale_references(
                db,
                result["evidence"],
                {cid for i in result["items"] for cid in i["source_chunk_ids"]},
            )
            if obsolete:
                raise HTTPException(422, "; ".join(obsolete))
        status = "approved" if approved else "rejected"
        result["approval" if approved else "rejection"] = {
            "actor": user["id"],
            "timestamp": now(),
            "note": body.note,
        }
        db.execute(
            "UPDATE events SET status=?,result=?,version=version+1 WHERE id=?",
            (status, dumps(result), event_id),
        )
        if approved:
            for i, text, vector in zip(result["items"], history, vectors):
                db.execute(
                    """INSERT INTO chunks(id,event_id,source_name,collection,kind,priority,text,location,vector,embedding_model,domain,approved)
                    VALUES (?,?,?,'faq_history_approved','historical_faq',5,?,?,?,?,?,1)""",
                    (
                        uid(),
                        event_id,
                        event["name"],
                        text,
                        "FAQ aprovada · " + i["id"],
                        dumps(vector),
                        model_id(),
                        i["domain"],
                    ),
                )
        audit(
            db,
            user["id"],
            "review." + status,
            event_id,
            note=body.note,
            version=event["version"] + 1,
            history_chunks=len(history),
            acknowledged_gaps=result["gaps"],
            acknowledged_conflicts=result["conflicts"],
        )
        return get_event(db, event_id)


@app.get("/api/events/{event_id}/document")
def download_document(event_id: str, user=Depends(identity)):
    with database() as db:
        event = get_event(db, event_id)
    if not event["result"]:
        raise HTTPException(409, "Gere uma FAQ antes de exportar")
    data = document_bytes(event)
    filename = f"simplifaq-{event_id}-v{event['version']}.docx"
    path = settings().data_dir / "documents" / filename
    path.write_bytes(data)
    with database(True) as db:
        audit(
            db,
            user["id"],
            "document.generated",
            event_id,
            version=event["version"],
            status=event["status"],
            sha256=digest(data),
        )
        audit(db, user["id"], "document.downloaded", event_id, filename=filename)
    return Response(
        data,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.patch("/api/events/{event_id}/sections/{section_id}")
def review_section(
    event_id: str, section_id: str, body: SectionReview, user=Depends(identity)
):
    if body.section_id != section_id:
        raise HTTPException(422, "Identificador de seção divergente")
    with database(True) as db:
        event = get_event(db, event_id)
        editable(event, body.expected_version)
        if not event["result"] or not event["result"].get("template_version"):
            raise HTTPException(
                409, "Resultado anterior ao template; gere uma nova versão"
            )
        result = event["result"]
        section = next(
            (s for s in result["sections"] if s["section_id"] == section_id), None
        )
        if section is None:
            raise HTTPException(422, "Seção fora do template")
        current = [
            public_chunk(r)
            for r in db.execute(
                "SELECT * FROM chunks WHERE event_id=? AND collection='event_current'",
                (event_id,),
            )
        ]
        if not set(body.evidence_chunk_ids) <= {c["id"] for c in current}:
            raise HTTPException(422, "Aplicabilidade exige fontes do evento atual")
        if body.status != "insufficient_information" and not body.evidence_chunk_ids:
            raise HTTPException(
                422,
                "Cite evidências para aplicável/não aplicável; ausência significa informação insuficiente",
            )
        if body.reviewed and len(body.review_note.strip()) < 10:
            raise HTTPException(
                422, "Registre a revisão da seção em pelo menos 10 caracteres"
            )
        if body.reviewed and numeric_tokens(body.reason_pt) != numeric_tokens(
            body.reason_en
        ):
            raise HTTPException(
                422, "Números divergentes nas justificativas PT/EN da seção"
            )
        snapshot(db, event, user["id"])
        before = dict(section)
        section.update(body.model_dump(exclude={"expected_version"}))
        section.update(
            reviewed_by=user["id"] if body.reviewed else None,
            reviewed_at=now() if body.reviewed else None,
        )
        by_id = {c["id"]: c for c in result["evidence"]}
        by_id.update(
            {c["id"]: c for c in current if c["id"] in body.evidence_chunk_ids}
        )
        result["evidence"] = list(by_id.values())
        db.execute(
            "UPDATE events SET result=?,status='review',version=version+1 WHERE id=?",
            (dumps(result), event_id),
        )
        audit(
            db,
            user["id"],
            "review.section_saved",
            event_id,
            section_id=section_id,
            before=before,
            after=section,
        )
        return get_event(db, event_id)


@app.get("/api/audit")
def audit_log(
    event_id: str | None = None, before: int | None = None, user=Depends(identity)
):
    with database() as db:
        rows = db.execute(
            "SELECT * FROM audit WHERE (? IS NULL OR event_id=?) AND (? IS NULL OR id<?) ORDER BY id DESC LIMIT 200",
            (event_id, event_id, before, before),
        )
        return [{**dict(r), "details": json.loads(r["details"])} for r in rows]


@app.get("/api/events/{event_id}/revisions")
def revisions(event_id: str, user=Depends(identity)):
    with database() as db:
        get_event(db, event_id)
        return [
            {**dict(r), "result": json.loads(r["result"])}
            for r in db.execute(
                "SELECT * FROM revisions WHERE event_id=? ORDER BY created_at DESC",
                (event_id,),
            )
        ]


@app.get("/api/training/dataset")
def training_dataset(user=Depends(identity)):
    from .finetuning import approved_dataset

    data, provenance = approved_dataset()
    with database(True) as db:
        audit(
            db,
            user["id"],
            "training.dataset_exported",
            samples=len(data),
            provenance=provenance,
        )
    return Response(
        "\n".join(dumps(r) for r in data) + "\n",
        media_type="application/x-ndjson",
        headers={
            "Content-Disposition": 'attachment; filename="simplifaq-approved.jsonl"'
        },
    )


@app.get("/api/training")
def training_list(user=Depends(identity)):
    from .finetuning import list_trainings

    return list_trainings()


@app.post("/api/training", status_code=202)
def training_start(user=Depends(identity)):
    from .finetuning import enqueue_training

    return enqueue_training(user["id"])


@app.get("/api/training/{training_id}/artifact")
def training_artifact(training_id: str, user=Depends(identity)):
    with database(True) as db:
        row = db.execute(
            "SELECT * FROM trainings WHERE id=? AND status='completed'", (training_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Adapter não disponível")
        audit(db, user["id"], "training.adapter_downloaded", training_id=training_id)
    return FileResponse(
        settings().data_dir / "training" / training_id / "adapter.zip",
        filename=f"simplifaq-lora-{training_id}.zip",
    )
