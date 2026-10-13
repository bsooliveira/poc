import httpx
import pytest
from app.config import settings
from app.generation import Provider
from app.schemas import Classification


def test_oversized_local_context_fails_explicitly_before_inference(client, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    settings.cache_clear()
    with pytest.raises(ValueError, match="não será truncado"):
        Provider().complete(
            "Classify",
            {"event_current": [{"id": "synthetic-source", "text": "x" * 20000}]},
            Classification,
        )


def test_oversized_repair_context_stops_before_second_request(client, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    settings.cache_clear()
    calls = []
    original_client = httpx.Client

    def handle(request):
        calls.append(request)
        return httpx.Response(200, json={"message": {"content": "x" * 20000}})

    monkeypatch.setattr(
        "app.generation.httpx.Client",
        lambda **kwargs: original_client(transport=httpx.MockTransport(handle)),
    )
    with pytest.raises(ValueError, match="não será truncado"):
        Provider().complete(
            "Classify", {"event_current": [{"id": "synthetic-source"}]}, Classification
        )
    assert len(calls) == 1
