"""Read-only integrity verification for a mounted POC or restored backup."""

import hashlib
import json
import sqlite3
from pathlib import Path

from .config import settings


def verify():
    root = settings().data_dir
    db_path = root / "simplfaq.db"
    # A stopped backup has no WAL and can be inspected without creating an SHM file.
    immutable = "&immutable=1" if not Path(str(db_path) + "-wal").exists() else ""
    conn = sqlite3.connect(f"{db_path.as_uri()}?mode=ro{immutable}", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok" or conn.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("Falha de integridade SQLite")
        sources = conn.execute("SELECT path,sha256 FROM sources").fetchall()
        for source in sources:
            # Stored paths are under /data; a backup can be checked at another mount point.
            path = root / "originals" / Path(source["path"]).name
            if hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
                raise ValueError("Arquivo original ausente ou checksum incorreto")
            if not json.loads(Path(str(path) + ".json").read_text(encoding="utf-8")):
                raise ValueError("Extração persistida ausente")
        verified_manuals = 0
        if conn.execute(
            "SELECT 1 FROM sqlite_master WHERE name='normative_documents'"
        ).fetchone():
            for manual in conn.execute("SELECT path,sha256 FROM normative_documents"):
                path = root / "normatives" / Path(manual["path"]).name
                if hashlib.sha256(path.read_bytes()).hexdigest() != manual["sha256"]:
                    raise ValueError("PDF normativo ausente ou checksum incorreto")
                verified_manuals += 1
        return {
            "integrity": integrity,
            "verified_originals": len(sources),
            "verified_manuals": verified_manuals,
            "counts": {
                t: conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
                for t in ("events", "chunks", "audit", "revisions")
            },
        }
    finally:
        conn.close()


if __name__ == "__main__":
    print(json.dumps(verify()))
