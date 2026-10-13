"""Local diagnostic without user documents."""

import httpx
from .config import settings

cfg = settings()
for fmt in [None, "json"]:
    payload = {
        "model": cfg.ollama_model,
        "stream": False,
        "messages": [
            {"role": "user", "content": 'Return exactly a JSON object: {"status":"ok"}'}
        ],
        "options": {
            "num_predict": 30,
            "num_ctx": 4096,
            "temperature": 0,
            "num_thread": 2,
        },
    }
    if fmt:
        payload["format"] = fmt
    response = httpx.post(
        cfg.ollama_url + "/api/chat", json=payload, timeout=180, trust_env=False
    )
    print(response.status_code, response.text[:500], flush=True)
