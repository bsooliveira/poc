import json
import sqlite3
import uuid
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime, timezone

from .config import settings


def now():
    return datetime.now(timezone.utc).isoformat()


def uid():
    return str(uuid.uuid4())


def dumps(value):
    return json.dumps(value, ensure_ascii=False)


@contextmanager
def database(write=False):
    conn = sqlite3.connect(settings().data_dir / "simplfaq.db", timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        if write:
            conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize():
    cfg = settings()
    for name in ("originals", "documents", "models", "normatives"):
        (cfg.data_dir / name).mkdir(parents=True, exist_ok=True)
    with database() as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript("""
        CREATE TABLE IF NOT EXISTS events (
          id TEXT PRIMARY KEY, name TEXT NOT NULL, company TEXT, event_type TEXT,
          event_date TEXT, status TEXT NOT NULL DEFAULT 'draft', version INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL, created_by TEXT NOT NULL, result TEXT, error TEXT);
        CREATE TABLE IF NOT EXISTS sources (
          id TEXT PRIMARY KEY, event_id TEXT NOT NULL REFERENCES events(id), name TEXT NOT NULL,
          kind TEXT NOT NULL, sha256 TEXT NOT NULL, size INTEGER NOT NULL, version INTEGER NOT NULL,
          path TEXT NOT NULL, created_at TEXT NOT NULL, created_by TEXT NOT NULL,
          UNIQUE(event_id,name,version));
        CREATE TABLE IF NOT EXISTS chunks (
          id TEXT PRIMARY KEY, event_id TEXT NOT NULL REFERENCES events(id), source_id TEXT,
          source_name TEXT NOT NULL, collection TEXT NOT NULL, kind TEXT NOT NULL,
          priority INTEGER NOT NULL, text TEXT NOT NULL, location TEXT NOT NULL,
          vector TEXT NOT NULL, embedding_model TEXT NOT NULL, domain TEXT, approved INTEGER NOT NULL DEFAULT 0);
        CREATE INDEX IF NOT EXISTS chunks_event ON chunks(event_id,collection,approved);
        CREATE TABLE IF NOT EXISTS runs (
          id TEXT PRIMARY KEY, event_id TEXT NOT NULL REFERENCES events(id), status TEXT NOT NULL,
          stage TEXT NOT NULL, created_at TEXT NOT NULL, started_at TEXT, finished_at TEXT,
          actor TEXT NOT NULL, model TEXT NOT NULL, prompt_version TEXT NOT NULL, details TEXT NOT NULL DEFAULT '{}');
        CREATE UNIQUE INDEX IF NOT EXISTS one_active_run ON runs(event_id) WHERE status IN ('queued','running');
        CREATE TABLE IF NOT EXISTS revisions (
          id TEXT PRIMARY KEY, event_id TEXT NOT NULL REFERENCES events(id), version INTEGER NOT NULL,
          result TEXT NOT NULL, created_at TEXT NOT NULL, actor TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS trainings (
          id TEXT PRIMARY KEY, status TEXT NOT NULL, actor TEXT NOT NULL, created_at TEXT NOT NULL,
          finished_at TEXT, config TEXT NOT NULL, metrics TEXT, error TEXT);
        CREATE TABLE IF NOT EXISTS audit (
          id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT, actor TEXT NOT NULL,
          timestamp TEXT NOT NULL, action TEXT NOT NULL, details TEXT NOT NULL);
        CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit BEGIN SELECT RAISE(ABORT,'Audit is append-only'); END;
        CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit BEGIN SELECT RAISE(ABORT,'Audit is append-only'); END;
        """)
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version < 2:
            migration = Path(__file__).with_name("migrations") / "002_normatives.sql"
            sql = migration.read_text(encoding="utf-8")
            if "metadata" in {
                r["name"] for r in db.execute("PRAGMA table_info(chunks)")
            }:
                # Older binaries can reset user_version during an image rollback.
                sql = sql.replace(
                    "ALTER TABLE chunks ADD COLUMN metadata TEXT NOT NULL DEFAULT '{}';",
                    "",
                )
            db.executescript("BEGIN IMMEDIATE;\n" + sql + "\nCOMMIT;")


def audit(db, actor, action, event_id=None, **details):
    db.execute(
        "INSERT INTO audit(event_id,actor,timestamp,action,details) VALUES (?,?,?,?,?)",
        (event_id, actor, now(), action, dumps(details)),
    )


def event_dict(row):
    out = dict(row)
    out["result"] = json.loads(out["result"]) if out["result"] else None
    return out
