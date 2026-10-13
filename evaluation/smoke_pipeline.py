"""Small final real-model smoke test using the default local provider and fictitious data."""
import io
import json
import time
from pathlib import Path
from docx import Document
from fastapi.testclient import TestClient
from app.main import app

output = Path("/artifacts/final-smoke")
output.mkdir(parents=True, exist_ok=True)
with TestClient(app) as client:
    client.headers["X-SimplFAQ"] = "local-poc"
    event = client.post("/api/events", json={"name": "Prazo de inscrição fictício", "company": "Empresa fictícia", "event_type": "Inscrições"}).json()
    eid = event["id"]
    text = "TESTE FICTÍCIO. O prazo de inscrição do evento fictício termina em 13 de outubro de 2026. Não haverá inscrições após esse prazo."
    assert client.post(f"/api/events/{eid}/sources", files={"files": ("prazo-ficticio.txt", text.encode(), "text/plain")}).status_code == 201
    started = time.monotonic()
    assert client.post(f"/api/events/{eid}/runs").status_code == 202
    previous = None
    while time.monotonic() - started < 1000:
        event = client.get(f"/api/events/{eid}").json()
        stage = event["runs"][0]["stage"]
        if stage != previous:
            print(json.dumps({"status": event["status"], "stage": stage, "elapsed_seconds": round(time.monotonic() - started)}), flush=True)
            previous = stage
        if event["status"] in {"review", "failed"}:
            break
        time.sleep(2)
    (output / "event.json").write_text(json.dumps(event, ensure_ascii=False, indent=2), encoding="utf-8")
    assert event["status"] == "review", event["error"]
    valid_ids = {c["id"] for c in event["result"]["evidence"]}
    assert all(set(i["source_chunk_ids"]) <= valid_ids and i["requires_human_review"] and not i["reviewed"] for i in event["result"]["items"])
    doc = client.get(f"/api/events/{eid}/document").content
    parsed = Document(io.BytesIO(doc))
    assert any("RASCUNHO" in p.text for p in parsed.paragraphs)
    (output / "faq.docx").write_bytes(doc)
    print(json.dumps({"model": event["result"]["model"], "prompt_version": event["result"]["prompt_version"], "items": len(event["result"]["items"]), "elapsed_seconds": round(time.monotonic() - started), "metrics": event["result"]["metrics"]}), flush=True)
