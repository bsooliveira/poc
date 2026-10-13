import importlib.util
import json
import os
import shutil
import subprocess
import sys

import httpx
from fastapi import HTTPException

from .config import settings
from .db import audit, database, dumps, now, uid


def approved_dataset():
    samples, provenance = [], []
    with database() as db:
        events = db.execute(
            "SELECT * FROM events WHERE status='approved' ORDER BY created_at"
        ).fetchall()
    for event in events:
        result = json.loads(event["result"])
        evidence = {c["id"]: c["text"] for c in result["evidence"]}
        for item in result["items"]:
            if not item.get("reviewed"):
                continue
            context = "\n".join(
                evidence[cid] for cid in item["source_chunk_ids"] if cid in evidence
            )
            for lang in ("pt", "en"):
                samples.append(
                    {
                        "messages": [
                            {
                                "role": "system",
                                "content": "Answer only using the supplied event evidence. Preserve conditions and numbers.",
                            },
                            {
                                "role": "user",
                                "content": f"Evidence:\n{context}\nQuestion: {item['question_' + lang]}",
                            },
                            {"role": "assistant", "content": item["answer_" + lang]},
                        ]
                    }
                )
            provenance.append(
                {
                    "event_id": event["id"],
                    "version": event["version"],
                    "item_id": item["id"],
                    "source_chunk_ids": item["source_chunk_ids"],
                }
            )
    return samples, provenance


def list_trainings():
    samples, _ = approved_dataset()
    with database() as db:
        rows = db.execute(
            "SELECT * FROM trainings ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
    return {
        "available_samples": len(samples),
        "minimum_samples": 4,
        "training_available": importlib.util.find_spec("peft") is not None,
        "base_model": settings().training_model,
        "runs": [
            {
                **dict(r),
                "config": json.loads(r["config"]),
                "metrics": json.loads(r["metrics"]) if r["metrics"] else None,
            }
            for r in rows
        ],
    }


def enqueue_training(actor):
    samples, provenance = approved_dataset()
    if len(samples) < 4:
        raise HTTPException(
            422, "Aprove pelo menos 2 perguntas bilíngues (4 exemplos) antes de treinar"
        )
    if importlib.util.find_spec("peft") is None:
        raise HTTPException(
            503,
            "A imagem de treinamento não está instalada. Use scripts/build.sh --training.",
        )
    run_id = uid()
    folder = settings().data_dir / "training" / run_id
    folder.mkdir(parents=True)
    (folder / "dataset.jsonl").write_text(
        "\n".join(dumps(s) for s in samples), encoding="utf-8"
    )
    (folder / "provenance.json").write_text(dumps(provenance), encoding="utf-8")
    config = {
        "model": settings().training_model,
        "samples": len(samples),
        "max_steps": 8,
        "sequence_length": 256,
        "rank": 4,
        "learning_rate": 0.0002,
        "seed": 42,
    }
    try:
        with database(True) as db:
            if (
                db.execute(
                    "SELECT 1 FROM trainings WHERE status IN ('queued','running')"
                ).fetchone()
                or db.execute(
                    "SELECT 1 FROM runs WHERE status IN ('queued','running') UNION ALL SELECT 1 FROM normative_jobs WHERE status IN ('queued','running')"
                ).fetchone()
            ):
                raise HTTPException(
                    409,
                    "Aguarde o processamento atual; o notebook executa uma tarefa de IA por vez",
                )
            db.execute(
                "INSERT INTO trainings(id,status,actor,created_at,config) VALUES (?,'queued',?,?,?)",
                (run_id, actor, now(), dumps(config)),
            )
            audit(
                db,
                actor,
                "training.queued",
                training_id=run_id,
                config=config,
                provenance=provenance,
            )
    except Exception:
        for child in folder.iterdir():
            child.unlink()
        folder.rmdir()
        raise
    return {"id": run_id, "status": "queued"}


def process_next_training():
    with database(True) as db:
        row = db.execute(
            "SELECT * FROM trainings WHERE status='queued' ORDER BY created_at LIMIT 1"
        ).fetchone()
        if not row:
            return
        run = dict(row)
        db.execute("UPDATE trainings SET status='running' WHERE id=?", (run["id"],))
        audit(db, run["actor"], "training.started", training_id=run["id"])
    cfg = settings()
    folder = cfg.data_dir / "training" / run["id"]
    config = json.loads(run["config"])
    try:
        if cfg.llm_provider == "ollama":
            response = httpx.post(
                cfg.ollama_url + "/api/generate",
                json={"model": cfg.ollama_model, "keep_alive": 0},
                timeout=30,
                trust_env=False,
            )
            response.raise_for_status()
        with (folder / "training.log").open("w") as log:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "app.train_lora",
                    "--dataset",
                    str(folder / "dataset.jsonl"),
                    "--output",
                    str(folder / "adapter"),
                    "--model",
                    config["model"],
                    "--steps",
                    str(config["max_steps"]),
                ],
                stdout=log,
                stderr=log,
                timeout=3600,
                env={
                    **os.environ,
                    "HF_HOME": str(cfg.data_dir / "models" / "huggingface"),
                    "OMP_NUM_THREADS": "2",
                    "TOKENIZERS_PARALLELISM": "false",
                },
            )
        if completed.returncode:
            raise RuntimeError(
                "Treinamento falhou. Consulte training.log no volume de dados."
            )
        metrics = json.loads((folder / "adapter" / "metrics.json").read_text())
        shutil.copyfile(
            folder / "provenance.json", folder / "adapter" / "provenance.json"
        )
        shutil.make_archive(str(folder / "adapter"), "zip", folder / "adapter")
        with database(True) as db:
            db.execute(
                "UPDATE trainings SET status='completed',finished_at=?,metrics=? WHERE id=?",
                (now(), dumps(metrics), run["id"]),
            )
            audit(
                db,
                run["actor"],
                "training.completed",
                training_id=run["id"],
                metrics=metrics,
            )
    except Exception as exc:
        with database(True) as db:
            db.execute(
                "UPDATE trainings SET status='failed',finished_at=?,error=? WHERE id=?",
                (now(), str(exc)[:400], run["id"]),
            )
            audit(
                db,
                run["actor"],
                "training.failed",
                training_id=run["id"],
                error=type(exc).__name__,
            )
