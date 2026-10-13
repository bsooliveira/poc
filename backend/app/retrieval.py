import hashlib
import json
import math
import re
import threading
from functools import lru_cache

from .config import settings

_embedding_lock = threading.Lock()


def tokens(text):
    return re.findall(r"\w+", text.casefold())


def model_id():
    cfg = settings()
    return (
        cfg.embedding_model
        if cfg.embedding_provider == "fastembed"
        else "hash-lexical-768-v1"
    )


@lru_cache
def embedding_model():
    from fastembed import TextEmbedding

    return TextEmbedding(
        model_name=settings().embedding_model,
        cache_dir=str(
            settings().embedding_cache_dir or (settings().data_dir / "models")
        ),
        threads=4,
    )


def embed(texts, query=False):
    if settings().embedding_provider == "fastembed":
        with _embedding_lock:
            model = embedding_model()
            vectors = model.query_embed(texts) if query else model.passage_embed(texts)
            return [v.tolist() for v in vectors]
    output = []
    for text in texts:
        vector = [0.0] * 768
        for token in tokens(text):
            idx = (
                int.from_bytes(hashlib.sha256(token.encode()).digest()[:4], "big") % 768
            )
            vector[idx] += 1
        norm = math.sqrt(sum(v * v for v in vector)) or 1
        output.append([v / norm for v in vector])
    return output


def cosine(a, b):
    if len(a) != len(b):
        return 0.0
    divisor = math.sqrt(sum(x * x for x in a) * sum(x * x for x in b))
    return sum(x * y for x, y in zip(a, b)) / divisor if divisor else 0.0


def public_chunk(row):
    result = {
        k: v for k, v in dict(row).items() if k not in {"vector", "embedding_model"}
    }
    result.update(json.loads(result.pop("metadata", "{}")))
    return result


def retrieve(
    db,
    event_id,
    query,
    collection="event_current",
    top_k=None,
    threshold=None,
    company=None,
):
    cfg = settings()
    top_k = max(1, min(top_k or cfg.retrieval_top_k, 40))
    threshold = cfg.retrieval_threshold if threshold is None else threshold
    if collection == "faq_history_approved":
        rows = db.execute(
            """SELECT c.* FROM chunks c JOIN events e ON e.id=c.event_id
            WHERE c.collection=? AND c.approved=1 AND e.status='approved' AND e.id!=?
            AND e.company=? AND e.company!=''""",
            (collection, event_id, company or ""),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM chunks WHERE event_id=? AND collection=?",
            (event_id, collection),
        ).fetchall()
    query_vector = embed([query], query=True)[0]
    query_tokens = set(tokens(query))
    ranked = []
    for row in rows:
        if row["embedding_model"] != model_id():
            raise ValueError(
                "Modelo de embedding alterado: reindexação dos dados necessária"
            )
        similarity = cosine(query_vector, json.loads(row["vector"]))
        if similarity < threshold:
            continue
        lexical = len(query_tokens & set(tokens(row["text"]))) / max(
            1, len(query_tokens)
        )
        # Reranking híbrido determinístico. Prioridade factual é explícita no contexto.
        rerank = 0.75 * similarity + 0.20 * lexical + 0.05 * (7 - row["priority"]) / 6
        ranked.append(
            {
                **public_chunk(row),
                "score": round(similarity, 4),
                "rerank_score": round(rerank, 4),
            }
        )
    ranked.sort(key=lambda c: (-c["rerank_score"], c["priority"]))
    return ranked[:top_k]
