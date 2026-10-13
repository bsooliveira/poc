import json
import time
import zipfile
import io
import importlib.util
from types import SimpleNamespace

from app.db import database
from test_workflow import generated_event


def approve_synthetic_event(client):
    event = generated_event(client)
    for item in event["result"]["items"]:
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
            review_note="Conferência dos dados sintéticos feita pelo harness de teste.",
        )
        response = client.patch(
            f"/api/events/{event['id']}/items/{item['id']}", json=payload
        )
        assert response.status_code == 200
        event = response.json()
    response = client.post(
        f"/api/events/{event['id']}/decision",
        json={
            "expected_version": event["version"],
            "decision": "approve",
            "note": "Aprovação sintética no banco isolado de teste",
        },
    )
    assert response.status_code == 200


def test_training_queue_artifact_provenance_and_approved_only(client, monkeypatch):
    from pathlib import Path

    original_find_spec = importlib.util.find_spec
    monkeypatch.setattr(
        "app.finetuning.importlib.util.find_spec",
        lambda name, *args: (
            object() if name == "peft" else original_find_spec(name, *args)
        ),
    )

    def completed_training(command, **kwargs):
        output = Path(command[command.index("--output") + 1])
        output.mkdir(parents=True)
        (output / "metrics.json").write_text(
            json.dumps(
                {
                    "steps": 8,
                    "losses": [2.0, 1.9],
                    "validation_loss_before": 2.0,
                    "validation_loss_after": 1.9,
                }
            )
        )
        (output / "adapter_config.json").write_text(
            '{"test":"synthetic mocked weights"}'
        )
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("app.finetuning.subprocess.run", completed_training)
    approve_synthetic_event(client)
    approve_synthetic_event(client)
    generated_event(client)  # Unapproved data must not enter the dataset.
    listing = client.get("/api/training").json()
    assert listing["available_samples"] == 4
    response = client.post("/api/training")
    assert response.status_code == 202, response.text
    tid = response.json()["id"]
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        run = next(
            r for r in client.get("/api/training").json()["runs"] if r["id"] == tid
        )
        if run["status"] in {"completed", "failed"}:
            break
        time.sleep(0.1)
    assert run["status"] == "completed", run
    artifact = client.get(f"/api/training/{tid}/artifact")
    assert artifact.status_code == 200
    with zipfile.ZipFile(io.BytesIO(artifact.content)) as package:
        assert {"metrics.json", "provenance.json", "adapter_config.json"} <= set(
            package.namelist()
        )
        assert len(json.loads(package.read("provenance.json"))) == 2
    with database() as db:
        assert (
            db.execute(
                "SELECT count(*) FROM audit WHERE action='training.completed'"
            ).fetchone()[0]
            == 1
        )
