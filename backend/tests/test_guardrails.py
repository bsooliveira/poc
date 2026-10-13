import io
import zipfile

import pytest
from docx import Document
from openpyxl import Workbook
from pptx import Presentation

from app.db import audit, database, dumps, now, uid
from app.ingestion import chunk_sections, extract, safe_name
from app.retrieval import embed, model_id, retrieve
from app.validation import deduplicate, deterministic_validation, numeric_tokens


def test_extract_office_formats_and_plain_text(client):
    doc = Document()
    doc.add_paragraph("Texto oficial de teste")
    doc.add_table(rows=1, cols=1).cell(0, 0).text = "Uma condição da tabela"
    out = io.BytesIO()
    doc.save(out)
    assert "condição" in str(extract("a.docx", out.getvalue()))
    book = Workbook()
    book.active.append(["Participantes", 200])
    out = io.BytesIO()
    book.save(out)
    assert "200" in str(extract("a.xlsx", out.getvalue()))
    slides = Presentation()
    slide = slides.slides.add_slide(slides.slide_layouts[1])
    slide.shapes.title.text = "Tema do evento"
    out = io.BytesIO()
    slides.save(out)
    assert "Tema" in str(extract("a.pptx", out.getvalue()))
    assert "200" in str(extract("a.csv", b"Nome,Valor\nVagas,200"))
    assert "evento" in str(extract("a.json", b'{"nome":"evento"}'))
    assert safe_name("../../documento.txt") == "documento.txt"


@pytest.mark.parametrize(
    "filename,data",
    [
        ("x.pdf", b"fake pdf"),
        ("x.txt", b"\xff"),
        ("x.txt", b"x\x00y"),
        ("x.txt", b""),
        ("x.docx", b"not a zip"),
        ("x.exe", b"MZ"),
    ],
)
def test_invalid_uploads(client, filename, data):
    with pytest.raises(ValueError):
        extract(filename, data)


def test_zip_bomb_and_macros(client):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("word/vbaProject.bin", b"macro")
    with pytest.raises(ValueError, match="Macros"):
        extract("a.docx", stream.getvalue())


def test_chunks_cover_full_document(client):
    text = "\n".join(f"Frase {i}: informação oficial do evento." for i in range(300))
    chunks = list(chunk_sections([("página 1", text)]))
    assert len(chunks) > 2
    assert chunks[0]["text"].startswith("Frase 0")
    assert "Frase 299" in chunks[-1]["text"]
    assert all(len(c["text"]) <= 1400 for c in chunks)


def test_retrieval_isolates_events_and_approved_history(client):
    ids = [
        client.post(
            "/api/events",
            json={"name": "Evento " + str(i), "company": "Acme" if i != 2 else "Outra"},
        ).json()["id"]
        for i in range(3)
    ]
    query = "prazo inscrição"
    vector = dumps(embed([query])[0])
    with database(True) as db:
        for eid in ids:
            for collection in ("event_current", "faq_history_approved"):
                db.execute(
                    "INSERT INTO chunks(id,event_id,source_name,collection,kind,priority,text,location,vector,embedding_model,approved) VALUES (?,?,?,?,?,?,?,?,?,?,1)",
                    (
                        uid(),
                        eid,
                        "fonte",
                        collection,
                        "official",
                        1,
                        query,
                        "texto",
                        vector,
                        model_id(),
                    ),
                )
        db.execute(
            "UPDATE events SET status='approved' WHERE id IN (?,?)", (ids[1], ids[2])
        )
    with database() as db:
        assert {r["event_id"] for r in retrieve(db, ids[0], query)} == {ids[0]}
        assert {
            r["event_id"]
            for r in retrieve(db, ids[0], query, "faq_history_approved", company="Acme")
        } == {ids[1]}
        assert retrieve(db, ids[0], query, "faq_history_approved", company="") == []


def test_validation_blocks_unfounded_numbers_and_history(client):
    evidence = [
        {
            "id": "a",
            "collection": "event_current",
            "text": "Limite de 200 participantes",
        }
    ]
    item = {
        "source_chunk_ids": ["a"],
        "answer_pt": "Limite de 200",
        "answer_en": "Limit of 300",
    }
    assert deterministic_validation(item, evidence)
    item.update(answer_en="Limit of 200", source_chunk_ids=["b"])
    assert deterministic_validation(item, evidence)
    item["source_chunk_ids"] = ["a"]
    assert not deterministic_validation(item, evidence)
    evidence[0]["collection"] = "faq_history_approved"
    assert deterministic_validation(item, evidence)


def test_dedup_preserves_distinct_facts():
    items = [
        {"answer_pt": "Prazo de 2 dias", "answer_en": "Within 2 days"},
        {"answer_pt": "Prazo de 3 dias", "answer_en": "Within 3 days"},
    ]
    assert len(deduplicate(items + items)) == 2
    assert numeric_tokens("1,5") != numeric_tokens("15")
    assert numeric_tokens("9 a.m. to noon") == numeric_tokens("9h às 12h")


def test_audit_is_append_only(client):
    with database(True) as db:
        audit(db, "test", "test.action", marker="synthetic")
    with pytest.raises(Exception, match="append-only"):
        with database(True) as db:
            db.execute("DELETE FROM audit")


def test_stale_approval_and_numeric_edit(client):
    from test_workflow import generated_event

    event = generated_event(client)
    item = event["result"]["items"][0]
    payload = {
        k: item[k]
        for k in (
            "question_pt",
            "answer_pt",
            "question_en",
            "answer_en",
            "source_chunk_ids",
        )
    }
    payload.update(
        expected_version=event["version"],
        answer_en="The event is in 2099",
        reviewed=True,
        review_note="Teste de alteração numérica indevida",
    )
    assert (
        client.patch(
            f"/api/events/{event['id']}/items/{item['id']}", json=payload
        ).status_code
        == 422
    )


def test_interrupted_run_is_recoverable(client):
    # Recovery is exercised directly with a separate worker without waiting on external models.
    from app.orchestration import Worker

    eid = client.post("/api/events", json={"name": "Execução interrompida"}).json()[
        "id"
    ]
    with database(True) as db:
        db.execute("UPDATE events SET status='processing' WHERE id=?", (eid,))
        db.execute(
            "INSERT INTO runs(id,event_id,status,stage,created_at,actor,model,prompt_version) VALUES (?,?,'running','generation',?,'test','mock','v1')",
            (uid(), eid, now()),
        )
    worker = Worker()
    worker.start()
    worker.stop()
    event = client.get(f"/api/events/{eid}").json()
    assert event["status"] == "failed"
    assert event["runs"][0]["stage"] == "interrupted"
    assert event["result"] is None
