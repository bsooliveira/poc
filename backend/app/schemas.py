from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EventCreate(StrictModel):
    name: str = Field(min_length=3, max_length=180)
    company: str = Field(default="", max_length=180)
    event_type: str = Field(default="Comunicado corporativo", max_length=100)
    event_date: date | None = None


class DomainDecision(StrictModel):
    domain: str = Field(min_length=2, max_length=100)
    applicable: bool
    reason: str = Field(max_length=2000)
    evidence_chunk_ids: list[str] = Field(max_length=100)
    requires_human_review: bool = True


class Classification(StrictModel):
    domains: list[DomainDecision] = Field(min_length=1, max_length=12)
    gaps: list[str] = Field(default_factory=list, max_length=30)


class QAItem(StrictModel):
    id: str = Field(min_length=1, max_length=100)
    domain: str = Field(min_length=1, max_length=100)
    question_pt: str = Field(min_length=3, max_length=2000)
    answer_pt: str = Field(min_length=3, max_length=10000)
    question_en: str = Field(min_length=3, max_length=2000)
    answer_en: str = Field(min_length=3, max_length=10000)
    source_chunk_ids: list[str] = Field(min_length=1, max_length=30)
    grounded: bool = False
    pt_en_equivalent: bool = False
    confidence: float = Field(default=0, ge=0, le=1)
    requires_human_review: bool = True
    review_reason: str | None = Field(default=None, max_length=5000)


class GeneratedFAQ(StrictModel):
    items: list[QAItem] = Field(min_length=1, max_length=40)
    gaps: list[str] = Field(default_factory=list, max_length=30)
    conflicts: list[str] = Field(default_factory=list, max_length=30)


class ValidationItem(StrictModel):
    id: str
    reason: str = Field(
        description="Explain factual support and whether PT/EN have the same meaning before choosing the flags."
    )
    unsupported_claims: list[str]
    conflicting_sources: list[str]
    supported: bool = Field(
        description="True if all claims in both answers are supported by current evidence. This is not human approval."
    )
    equivalent: bool = Field(
        description="True if PT/EN questions and answers express the same meaning, numbers, negations and conditions. Different languages are expected."
    )


class ValidationResult(StrictModel):
    items: list[ValidationItem]


class ClaimEvidence(StrictModel):
    text_pt: str = Field(min_length=3, max_length=10000)
    text_en: str = Field(default="", max_length=10000)
    source_chunk_ids: list[str] = Field(min_length=1, max_length=12)


class ItemEdit(StrictModel):
    expected_version: int
    domain: str | None = Field(default=None, min_length=2, max_length=100)
    section_id: str | None = None
    claims: list[ClaimEvidence] | None = Field(default=None, max_length=30)
    question_pt: str = Field(min_length=3, max_length=2000)
    answer_pt: str = Field(min_length=3, max_length=10000)
    question_en: str = Field(min_length=3, max_length=2000)
    answer_en: str = Field(min_length=3, max_length=10000)
    source_chunk_ids: list[str] = Field(min_length=1, max_length=30)
    reviewed: bool = False
    review_note: str = Field(default="", max_length=5000)


class Decision(StrictModel):
    expected_version: int
    decision: Literal["approve", "reject"]
    note: str = Field(min_length=5, max_length=5000)


class SectionAssessment(StrictModel):
    section_id: str
    status: Literal["applicable", "not_applicable", "insufficient_information"]
    reason_pt: str = Field(min_length=3, max_length=1500)
    reason_en: str = Field(min_length=3, max_length=1500)
    evidence_chunk_ids: list[str] = Field(default_factory=list, max_length=12)


class TemplateAssessment(StrictModel):
    event_classification: str = Field(min_length=3, max_length=500)
    sections: list[SectionAssessment] = Field(min_length=1, max_length=12)


class PTItem(StrictModel):
    question_pt: str = Field(min_length=3, max_length=2000)
    answer_pt: str = Field(min_length=3, max_length=10000)
    source_chunk_ids: list[str] = Field(min_length=1, max_length=12)
    claims: list[ClaimEvidence] = Field(min_length=1, max_length=30)


class PTGeneration(StrictModel):
    items: list[PTItem] = Field(min_length=1, max_length=3)
    gaps: list[str] = Field(default_factory=list, max_length=12)
    conflicts: list[str] = Field(default_factory=list, max_length=12)


class TranslationItem(StrictModel):
    id: str
    question_en: str = Field(min_length=3, max_length=2000)
    answer_en: str = Field(min_length=3, max_length=10000)
    claims_en: list[str] = Field(min_length=1, max_length=30)


class Translations(StrictModel):
    items: list[TranslationItem] = Field(min_length=1, max_length=3)


class SectionReview(SectionAssessment):
    expected_version: int
    reviewed: bool = False
    review_note: str = Field(default="", max_length=5000)
