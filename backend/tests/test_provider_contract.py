import json

import httpx
import pytest

from app.config import settings
from app.generation import Provider
from app.schemas import GeneratedFAQ, Classification


def fake_client(monkeypatch, handler):
    original_client = httpx.Client
    monkeypatch.setattr(
        "app.generation.httpx.Client",
        lambda **kwargs: original_client(transport=httpx.MockTransport(handler)),
    )


def test_ollama_minimal_output_is_normalized(monkeypatch, client):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    settings.cache_clear()
    captured = []

    def handle(request):
        captured.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "message": {
                    "content": json.dumps(
                        {
                            "items": [
                                {
                                    "question_pt": "Qual é o formato?",
                                    "answer_pt": "Online.",
                                    "question_en": "What is the format?",
                                    "answer_en": "Online.",
                                    "source_chunk_ids": ["actual-source"],
                                }
                            ],
                            "gaps": [],
                            "conflicts": [],
                        }
                    )
                }
            },
        )

    fake_client(monkeypatch, handle)
    faq = Provider().complete(
        "Generate",
        {"domain": "Formato", "event_current": [{"id": "actual-source"}]},
        GeneratedFAQ,
    )
    assert faq.items[0].domain == "Formato" and faq.items[0].id
    assert faq.items[0].requires_human_review
    properties = captured[0]["format"]["$defs"]["QAItem"]["properties"]
    assert "id" not in properties and "grounded" not in properties


def test_b3_contract_and_auth_are_kept(monkeypatch, client):
    monkeypatch.setenv("LLM_PROVIDER", "b3")
    monkeypatch.setenv("B3_API_URL", "https://b3-mock.example.test/chat/completions")
    monkeypatch.setenv("B3_API_KEY", "synthetic-contract-test")
    monkeypatch.setenv("B3_MODEL", "fictitious-model")
    settings.cache_clear()
    captured = []

    def handle(request):
        captured.append(request)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "domains": [
                                        {
                                            "domain": "Agenda",
                                            "applicable": True,
                                            "reason": "Factual",
                                            "evidence_chunk_ids": ["a"],
                                        }
                                    ],
                                    "gaps": [],
                                }
                            )
                        }
                    }
                ]
            },
        )

    fake_client(monkeypatch, handle)
    result = Provider().complete(
        "Classify", {"event_current": [{"id": "a"}]}, Classification
    )
    assert result.domains[0].domain == "Agenda"
    assert captured[0].headers["Authorization"] == "Bearer synthetic-contract-test"
    assert json.loads(captured[0].content)["model"] == "fictitious-model"


def test_invalid_model_json_fails_after_bounded_retry(monkeypatch, client):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    settings.cache_clear()
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(200, json={"message": {"content": "invalid json"}})

    fake_client(monkeypatch, handle)
    with pytest.raises(ValueError, match="duas tentativas"):
        Provider().complete(
            "Classify", {"event_current": [{"id": "a"}]}, Classification
        )
    assert len(calls) == 2
