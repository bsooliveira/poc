"""Public B3 manuals: verified discovery, additive storage and version-filtered RAG."""

import hashlib
import io
import json
import re
import time
import unicodedata
import uuid
from datetime import date, datetime
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from zoneinfo import ZoneInfo

import httpx
from pypdf import PdfReader

from .config import settings
from .db import audit, database, dumps, now, uid
from .ingestion import chunk_sections
from .retrieval import cosine, embed, model_id, tokens

LISTING_URL = "https://www.b3.com.br/pt_br/regulacao/estrutura-normativa/estrutura-normativa/pos-negociacao/"
MANUALS = {
    "camara": "Manual de Procedimentos Operacionais da Câmara B3",
    "depositaria": "Manual de Procedimentos Operacionais da Central Depositária de Renda Variável B3",
}


def b3_today():
    return datetime.now(ZoneInfo("America/Sao_Paulo")).date().isoformat()


def normalized(text):
    return re.sub(
        r"[^a-z0-9]",
        "",
        unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower(),
    )


class Listing(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text, self.links, self.current = "", [], None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.current = {
                "url": dict(attrs).get("href", ""),
                "text": "",
                "offset": len(self.text),
            }

    def handle_data(self, data):
        self.text += data + " "
        if self.current is not None:
            self.current["text"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            self.links.append(self.current)
            self.current = None


def official_url(url):
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "www.b3.com.br"
        or parsed.port not in (None, 443)
        or parsed.username
        or parsed.password
    ):
        raise ValueError("Somente URLs HTTPS oficiais da B3 são permitidas")
    return url


def discover(html):
    listing = Listing()
    listing.feed(html)
    found = []
    for system, title in MANUALS.items():
        matches = [
            a
            for a in listing.links
            if normalized(title) in normalized(a["text"])
            and "semmarca" in normalized(a["text"])
            and "/data/files/" in a["url"]
        ]
        if len(matches) != 1:
            raise ValueError(
                f"Link sem marcas não identificado de forma inequívoca: {system}"
            )
        link = matches[0]
        preceding = listing.text[max(0, link["offset"] - 500) : link["offset"]]
        dates = re.findall(r"vers[aã]o\s+(\d{2})/(\d{2})/(\d{4})", preceding, re.I)
        if not dates or "em vigor" not in preceding.casefold():
            raise ValueError(f"Vigência não confirmada na página oficial: {system}")
        day, month, year = dates[-1]
        version = f"{year}-{month}-{day}"
        date.fromisoformat(version)
        found.append(
            dict(
                system=system,
                title=title,
                listing_url=LISTING_URL,
                url=official_url(urljoin(LISTING_URL, link["url"])),
                version=version,
                effective_from=version,
                verified_at=now(),
                origin="official",
            )
        )
    return found


def ingest_document(metadata, data):
    cfg = settings()
    if (
        metadata["system"] not in MANUALS
        or len(data) > cfg.max_upload_mb * 1024 * 1024
        or not data.startswith(b"%PDF")
    ):
        raise ValueError("Manual PDF inválido ou acima do limite")
    reader = PdfReader(io.BytesIO(data))
    cover = reader.pages[0].extract_text() or ""
    if metadata.get("origin", "official") == "official":
        official_url(metadata["url"])
        cover_date = "/".join(reversed(metadata["version"].split("-")))
        if (
            normalized(metadata["title"]) not in normalized(cover)
            or cover_date not in cover
        ):
            raise ValueError(
                "Título/versão da capa divergem da página oficial; versão anterior preservada"
            )
    digest = hashlib.sha256(data).hexdigest()
    with database() as db:
        existing = db.execute(
            "SELECT * FROM normative_documents WHERE system=? AND sha256=?",
            (metadata["system"], digest),
        ).fetchone()
    if existing:
        with database(True) as db:
            status = existing["status"]
            if status == "pending" and existing["effective_from"] <= b3_today():
                active = db.execute(
                    "SELECT effective_from FROM normative_documents WHERE system=? AND status='active'",
                    (metadata["system"],),
                ).fetchone()
                status = (
                    "inactive"
                    if active and active[0] > existing["effective_from"]
                    else "active"
                )
                if status == "active":
                    db.execute(
                        "UPDATE normative_documents SET status='inactive' WHERE system=? AND status='active'",
                        (metadata["system"],),
                    )
                audit(
                    db,
                    "manual-updater",
                    "normative.effective_status",
                    document_id=existing["id"],
                    status=status,
                )
            db.execute(
                "UPDATE normative_documents SET verified_at=?,url=?,status=? WHERE id=?",
                (metadata["verified_at"], metadata["url"], status, existing["id"]),
            )
            return dict(
                db.execute(
                    "SELECT * FROM normative_documents WHERE id=?", (existing["id"],)
                ).fetchone()
            )
    document_id = str(uuid.uuid5(uuid.NAMESPACE_URL, metadata["system"] + digest))
    chunks, heading, total = [], "Capa / Cover", 0
    for page_number, page in enumerate(reader.pages, 1):
        text = page.extract_text(extraction_mode="layout") or ""
        total += len(text)
        if total > cfg.max_extracted_chars:
            raise ValueError("Manual excede o limite de texto extraído")
        headings = re.findall(
            r"^\s*(\d+(?:\.\d+)*\.?\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][^\n]{3,140})\s*$", text, re.M
        )
        if headings:
            heading = headings[0].strip()
        for index, chunk in enumerate(
            chunk_sections([(f"página {page_number} · {heading}", text)])
        ):
            chunks.append(
                dict(
                    id=str(
                        uuid.uuid5(
                            uuid.NAMESPACE_URL, f"{document_id}:{page_number}:{index}"
                        )
                    ),
                    text=chunk["text"],
                    location=chunk["location"],
                    section=heading,
                    page=page_number,
                )
            )
    if not chunks:
        raise ValueError("Manual sem texto extraível; OCR necessário")
    for start in range(0, len(chunks), 32):
        batch = chunks[start : start + 32]
        for chunk, vector in zip(batch, embed([c["text"] for c in batch])):
            chunk["vector"] = dumps(vector)
    path = cfg.data_dir / "normatives" / f"{document_id}.pdf"
    path.write_bytes(data)
    status = "active" if metadata["effective_from"] <= b3_today() else "pending"
    with database(True) as db:
        active = db.execute(
            "SELECT * FROM normative_documents WHERE system=? AND status='active'",
            (metadata["system"],),
        ).fetchone()
        if active and active["effective_from"] > metadata["effective_from"]:
            status = "inactive"
        if status == "active":
            db.execute(
                "UPDATE normative_documents SET status='inactive' WHERE system=? AND status='active'",
                (metadata["system"],),
            )
        db.execute(
            "INSERT INTO normative_documents(id,system,title,listing_url,url,sha256,version,effective_from,verified_at,ingested_at,status,path,page_count,chunk_count,origin) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                document_id,
                metadata["system"],
                metadata["title"],
                metadata["listing_url"],
                metadata["url"],
                digest,
                metadata["version"],
                metadata["effective_from"],
                metadata["verified_at"],
                now(),
                status,
                str(path),
                len(reader.pages),
                len(chunks),
                metadata.get("origin", "official"),
            ),
        )
        db.executemany(
            "INSERT INTO normative_chunks VALUES (?,?,?,?,?,?,?,?)",
            [
                (
                    c["id"],
                    document_id,
                    c["text"],
                    c["location"],
                    c["section"],
                    c["page"],
                    c["vector"],
                    model_id(),
                )
                for c in chunks
            ],
        )
        audit(
            db,
            "manual-updater",
            "normative.ingested",
            document_id=document_id,
            system=metadata["system"],
            version=metadata["version"],
            sha256=digest,
            status=status,
        )
        return dict(
            db.execute(
                "SELECT * FROM normative_documents WHERE id=?", (document_id,)
            ).fetchone()
        )


def public_manual(row):
    return {k: v for k, v in dict(row).items() if k != "path"}


def public_evidence(row):
    value = {
        k: v for k, v in dict(row).items() if k not in {"vector", "embedding_model"}
    }
    value.update(
        collection="normative_current",
        kind="normative",
        source_name=value["title"],
        source_id=value["document_id"],
        source_version=value["version"],
        source_sha256=value["sha256"],
        priority=4,
    )
    return value


NORMATIVE_QUERY = "SELECT c.*,d.system,d.title,d.url,d.listing_url,d.sha256,d.version,d.effective_from,d.status FROM normative_chunks c JOIN normative_documents d ON d.id=c.document_id"


def retrieve_normatives(db, query, systems, version=None, top_k=3, as_of=None):
    if not systems:
        return []
    if not set(systems) <= MANUALS.keys():
        raise ValueError("Sistema normativo desconhecido")
    rows = db.execute(
        NORMATIVE_QUERY
        + " WHERE d.status='active' AND d.effective_from<=? AND d.system IN ("
        + ",".join("?" for _ in systems)
        + ")"
        + (" AND d.version=?" if version else ""),
        [as_of or b3_today(), *systems] + ([version] if version else []),
    ).fetchall()
    if not rows:
        return []
    vector = embed([query], query=True)[0]
    ranked = []
    for row in rows:
        if row["embedding_model"] != model_id():
            raise ValueError("Reindexe os normativos com o modelo de embeddings atual")
        similarity = cosine(vector, json.loads(row["vector"]))
        lexical = len(set(tokens(query)) & set(tokens(row["text"]))) / max(
            1, len(set(tokens(query)))
        )
        if similarity >= settings().retrieval_threshold:
            ranked.append(
                {
                    **public_evidence(row),
                    "score": round(similarity, 4),
                    "rerank_score": 0.8 * similarity + 0.2 * lexical,
                }
            )
    return sorted(ranked, key=lambda c: -c["rerank_score"])[:top_k]


def stale_references(db, evidence, ids):
    errors = []
    for chunk in evidence:
        if chunk["id"] in ids and chunk["collection"] == "normative_current":
            row = db.execute(
                "SELECT d.status FROM normative_documents d JOIN normative_chunks c ON c.document_id=d.id WHERE c.id=?",
                (chunk["id"],),
            ).fetchone()
            if not row or row["status"] != "active":
                errors.append("Normativo desativado ou ausente: " + chunk["id"])
    return errors


def fetch_public(client, url, limit):
    official_url(url)
    with client.stream("GET", url) as response:
        response.raise_for_status()
        data = bytearray()
        for block in response.iter_bytes():
            data.extend(block)
            if len(data) > limit:
                raise ValueError("Download oficial acima do limite")
        return bytes(data)


def refresh_public():
    with httpx.Client(timeout=60, trust_env=False, follow_redirects=False) as client:
        html = fetch_public(client, LISTING_URL, 2_000_000)
        digest = hashlib.sha256(html).hexdigest()
        (settings().data_dir / "normatives" / f"listing-{digest}.html").write_bytes(
            html
        )
        discovered = discover(html.decode("utf-8"))
        return [
            public_manual(
                ingest_document(
                    m,
                    fetch_public(
                        client, m["url"], settings().max_upload_mb * 1024 * 1024
                    ),
                )
            )
            for m in discovered
        ]


def enqueue_refresh(actor):
    with database(True) as db:
        busy = any(
            db.execute(
                f"SELECT 1 FROM {table} WHERE status IN ('queued','running')"
            ).fetchone()
            for table in ("runs", "trainings", "normative_jobs")
        )
        if busy:
            raise ValueError("Aguarde as tarefas ativas antes de atualizar os manuais")
        job_id = uid()
        db.execute(
            "INSERT INTO normative_jobs(id,actor,status,created_at) VALUES (?,?,'queued',?)",
            (job_id, actor, now()),
        )
        audit(db, actor, "normative.refresh_queued", job_id=job_id)
        return job_id


def process_next_normative():
    with database(True) as db:
        job = db.execute(
            "SELECT * FROM normative_jobs WHERE status='queued' ORDER BY created_at LIMIT 1"
        ).fetchone()
        if not job:
            return False
        db.execute(
            "UPDATE normative_jobs SET status='running' WHERE id=?", (job["id"],)
        )
    try:
        report = refresh_public()
        status, error = "completed", None
    except Exception as exc:
        report, status, error = [], "failed", str(exc)[:1000]
    with database(True) as db:
        db.execute(
            "UPDATE normative_jobs SET status=?,finished_at=?,report=?,error=? WHERE id=?",
            (status, now(), dumps(report), error, job["id"]),
        )
        audit(
            db,
            job["actor"],
            "normative.refresh_" + status,
            job_id=job["id"],
            error=error,
        )
    return True


if __name__ == "__main__":
    # Run inside the live API container: its existing worker serializes the update.
    job_id = enqueue_refresh("operator-cli")
    print(dumps({"job_id": job_id}), flush=True)
    while True:
        with database() as db:
            job = dict(
                db.execute(
                    "SELECT * FROM normative_jobs WHERE id=?", (job_id,)
                ).fetchone()
            )
        if job["status"] in {"completed", "failed"}:
            print(dumps(job), flush=True)
            raise SystemExit(0 if job["status"] == "completed" else 1)
        time.sleep(2)
