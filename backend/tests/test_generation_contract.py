from app.generation import inference_schema
from app.schemas import Classification, GeneratedFAQ, ValidationResult


def test_llama_grammar_has_no_unbounded_string_repetition():
    context = {"event_current": [{"id": "actual-source"}]}
    result = inference_schema(GeneratedFAQ, context)
    assert "maxLength" not in str(result)
    assert result["$defs"]["QAItem"]["properties"]["source_chunk_ids"]["items"][
        "enum"
    ] == ["actual-source"]
    result = inference_schema(Classification, context)
    assert result["$defs"]["DomainDecision"]["properties"]["evidence_chunk_ids"][
        "items"
    ]["enum"] == ["actual-source"]
    result = inference_schema(ValidationResult, {"items": [{"id": "actual-item"}]})
    assert result["$defs"]["ValidationItem"]["properties"]["id"]["enum"] == [
        "actual-item"
    ]
