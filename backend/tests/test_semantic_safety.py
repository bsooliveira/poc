from pydantic import ValidationError
import pytest
from app.config import Settings
from app.schemas import ValidationResult, ValidationItem
from app.validation import validate_items


def test_repeated_generic_verdicts_are_inconclusive(client, monkeypatch):
    items = [
        {
            "id": str(i),
            "question_pt": f"Pergunta {i}?",
            "answer_pt": f"Valor {i}",
            "question_en": f"Question {i}?",
            "answer_en": f"Value {i}",
            "source_chunk_ids": ["source"],
        }
        for i in (1, 2)
    ]
    verdict = ValidationResult(
        items=[
            ValidationItem(
                id=i["id"],
                reason="Tudo está correto",
                supported=True,
                equivalent=True,
                unsupported_claims=[],
                conflicting_sources=[],
            )
            for i in items
        ]
    )
    monkeypatch.setattr("app.validation.Provider.complete", lambda *args: verdict)
    validated = validate_items(
        items,
        [{"id": "source", "collection": "event_current", "text": "Valores 1 e 2"}],
    )
    assert all(
        not i["grounded"] and not i["pt_en_equivalent"] and i["requires_human_review"]
        for i in validated
    )
    assert all(i["validation"]["semantic_inconclusive"] for i in validated)


def test_configuration_errors_do_not_echo_secret_values(client):
    with pytest.raises(ValidationError) as error:
        Settings(
            llm_provider="b3",
            b3_api_url="invalid",
            b3_api_key="synthetic-value-not-to-log",
            b3_model="mock",
        )
    assert "synthetic-value-not-to-log" not in str(error.value)
