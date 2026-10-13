import io
import time

from docx import Document

from app.db import database


def make_event(
    client,
    text="PT: O evento acontecerá em 2026.\nEN: The event will take place in 2026.",
):
    response = client.post(
        "/api/events", json={"name": "Evento sintético", "company": "Teste"}
    )
    assert response.status_code == 201
    event = response.json()
    response = client.post(
        f"/api/events/{event['id']}/sources",
        files=[("files", ("fonte.txt", text.encode(), "text/plain"))],
    )
    assert response.status_code == 201, response.text
    return event["id"]


def generated_event(client):
    eid = make_event(client)
    # Preserve the previous public contract as an explicit compatibility mode.
    assert client.post(f"/api/events/{eid}/runs?mode=legacy").status_code == 202
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        event = client.get(f"/api/events/{eid}").json()
        if event["status"] in {"review", "failed"}:
            assert event["status"] == "review", event
            return event
        time.sleep(0.1)
    raise AssertionError("Processamento não terminou")


def test_auth_and_origin(client):
    assert client.get("/api/health/ready").status_code == 200
    assert client.get("/api/events", headers={"X-SimplFAQ": ""}).status_code == 401
    assert (
        client.post(
            "/api/events",
            json={"name": "teste"},
            headers={"Origin": "https://evil.example"},
        ).status_code
        == 403
    )


def test_upload_atomic_versioned_and_validated(client):
    eid = make_event(client)
    url = f"/api/events/{eid}/sources"
    assert (
        client.post(
            url, files=[("files", ("a.txt", b"valid text")), ("files", ("b.exe", b"x"))]
        ).status_code
        == 422
    )
    assert len(client.get(f"/api/events/{eid}").json()["sources"]) == 1
    assert (
        client.post(url, files={"files": ("fonte.txt", b"novo texto")}).status_code
        == 201
    )
    assert client.get(f"/api/events/{eid}").json()["sources"][-1]["version"] == 2
    assert (
        client.post(url, files={"files": ("fonte.txt", b"novo texto")}).status_code
        == 409
    )
    assert (
        client.post(
            url, data={"kind": "historical_faq"}, files={"files": ("a.txt", b"test")}
        ).status_code
        == 422
    )


def test_review_approval_history_docx_and_training_gate(client):
    event = generated_event(client)
    eid = event["id"]
    result = event["result"]
    url = f"/api/events/{eid}"
    assert (
        client.post(
            url + "/decision",
            json={
                "decision": "approve",
                "expected_version": event["version"],
                "note": "Aprovado para teste",
            },
        ).status_code
        == 422
    )
    assert client.post("/api/training").status_code == 422
    with database() as db:
        assert (
            db.execute(
                "SELECT count(*) FROM chunks WHERE collection='faq_history_approved'"
            ).fetchone()[0]
            == 0
        )
    draft = Document(io.BytesIO(client.get(url + "/document").content))
    assert any("RASCUNHO" in p.text for p in draft.paragraphs)
    for item in result["items"]:
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
            reviewed=True,
            review_note="Verifiquei números, fontes e tradução dos dados sintéticos.",
        )
        response = client.patch(url + "/items/" + item["id"], json=payload)
        assert response.status_code == 200, response.text
        event = response.json()
        assert event["result"]["metrics"]["human_edit_rate"] == 0
        assert (
            client.patch(url + "/items/" + item["id"], json=payload).status_code == 409
        )
    response = client.post(
        url + "/decision",
        json={
            "decision": "approve",
            "expected_version": event["version"],
            "note": "Revisão sintética completa",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "approved"
    with database() as db:
        assert db.execute(
            "SELECT count(*) FROM chunks WHERE collection='faq_history_approved'"
        ).fetchone()[0] == len(result["items"])
    assert client.post(url + "/runs").status_code == 409
    assert client.get(url + "/document").content.startswith(b"PK")
    assert '"messages"' in client.get("/api/training/dataset").text
    actions = [a["action"] for a in client.get("/api/audit").json()]
    assert "review.approved" in actions and "document.downloaded" in actions


def test_reject_and_foreign_citations(client):
    event = generated_event(client)
    eid = event["id"]
    item = event["result"]["items"][0]
    payload = {
        k: item[k] for k in ("question_pt", "answer_pt", "question_en", "answer_en")
    }
    payload.update(
        source_chunk_ids=["foreign-id"],
        expected_version=event["version"],
        reviewed=True,
        review_note="Revisão inválida de teste",
    )
    assert (
        client.patch(f"/api/events/{eid}/items/{item['id']}", json=payload).status_code
        == 422
    )
    response = client.post(
        f"/api/events/{eid}/decision",
        json={
            "decision": "reject",
            "expected_version": event["version"],
            "note": "Corrigir fontes e tradução",
        },
    )
    assert response.status_code == 200
    with database() as db:
        assert (
            db.execute(
                "SELECT count(*) FROM chunks WHERE collection='faq_history_approved'"
            ).fetchone()[0]
            == 0
        )
