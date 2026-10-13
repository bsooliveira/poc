import json
from functools import lru_cache
from pathlib import Path


@lru_cache
def faq_template():
    value = json.loads(
        Path(__file__).with_name("faq_template.json").read_text(encoding="utf-8")
    )
    if len(value["sections"]) != 12 or len({s["id"] for s in value["sections"]}) != 12:
        raise ValueError("Template deve ter exatamente 12 seções distintas")
    return value


def section_definition(section_id):
    return next(s for s in faq_template()["sections"] if s["id"] == section_id)


def empty_sections():
    return [
        dict(
            section_id=s["id"],
            status="insufficient_information",
            reason_pt="Informações ainda não suficientes para avaliar esta seção.",
            reason_en="Insufficient information to assess this section.",
            evidence_chunk_ids=[],
            reviewed=False,
            review_note="",
        )
        for s in faq_template()["sections"]
    ]
