# SimpliFAQ — Schemas sugeridos

## EventMetadata
```json
{
  "event_id": "string",
  "company": "string|null",
  "event_type": "string|null",
  "event_date": "YYYY-MM-DD|null",
  "version": "string",
  "status": "draft|validated|approved"
}
```

## SourceChunk
```json
{
  "chunk_id": "string",
  "source_type": "current_event|meeting_transcript|historical_faq|language_guide",
  "source_name": "string",
  "event_id": "string|null",
  "domain": "string|null",
  "language": "pt|en|mixed",
  "approved": true,
  "text": "string",
  "metadata": {}
}
```

## DomainDecision
```json
{
  "domain": "string",
  "applicable": true,
  "reason": "string",
  "evidence_chunk_ids": ["..."],
  "requires_human_review": false
}
```

## QAItem
```json
{
  "id": "string",
  "domain": "string",
  "question_pt": "string",
  "answer_pt": "string",
  "question_en": "string",
  "answer_en": "string",
  "source_chunk_ids": ["..."],
  "grounded": true,
  "pt_en_equivalent": true,
  "confidence": 0.0,
  "requires_human_review": false,
  "review_reason": null
}
```
