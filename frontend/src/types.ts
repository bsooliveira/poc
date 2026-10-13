export interface Config { auth_mode: string; tenant_id: string; client_id: string; scope: string; provider: string; model: string; embedding_model: string; max_upload_mb: number; extensions: string[]; source_types: Record<string, string>; template: FAQTemplate }
export interface Source { id: string; name: string; kind: string; size: number; sha256: string; version: number; created_at: string }
export interface Chunk { id: string; source_name: string; text: string; location: string; collection: string; priority: number; score?: number; rerank_score?: number; source_version?: number|string; system?: string; url?: string; sha256?: string; page?: number; section?: string }
export interface Item { id: string; domain: string; section_id?: string; claims?: ClaimEvidence[]; question_pt: string; answer_pt: string; question_en: string; answer_en: string; source_chunk_ids: string[]; grounded: boolean; pt_en_equivalent: boolean; confidence: number; requires_human_review: boolean; review_reason: string | null; reviewed: boolean; review_note: string }
export interface Result { items: Item[]; gaps: string[]; conflicts: string[]; evidence: Chunk[]; model: string; provider: string; prompt_version: string; metrics: Record<string, number>; template_version?: string; template_snapshot?: FAQTemplate; sections?: SectionAssessment[]; event_classification?: string; approval?: { actor: string; timestamp: string; note: string } }

export interface FAQTemplate { version: string; sections: TemplateSection[]; states: Record<string,{pt:string;en:string}> }
export interface TemplateSection { id: string; number: string; title_pt: string; title_en: string; systems: string[] }
export interface SectionAssessment { section_id: string; status: string; reason_pt: string; reason_en: string; evidence_chunk_ids: string[]; reviewed: boolean; review_note: string; generation_warning?: string }
export interface EventSummary { id: string; name: string; company: string; event_type: string; event_date: string; status: string; version: number; created_at: string; source_count?: number }
export interface EventDetail extends EventSummary { result: Result | null; sources: Source[]; runs: { id: string; status: string; stage: string; created_at: string; finished_at: string | null }[]; error: string | null; normative_warnings?: string[] }
export interface AuditEntry { id: number; event_id: string | null; actor: string; timestamp: string; action: string; details: Record<string, unknown> }
export interface TrainingRun { id: string; status: string; created_at: string; error: string | null; config: { samples: number; max_steps: number; model: string }; metrics: { validation_loss_before: number | null; validation_loss_after: number | null; elapsed_seconds: number; steps: number } | null }
export interface Training { available_samples: number; minimum_samples: number; training_available: boolean; base_model: string; runs: TrainingRun[] }
export interface System { models: string[]; model_error: string | null; totals: Record<string, number>; provider: string; model: string; embedding_model: string; training_model: string }

export interface ClaimEvidence { text_pt: string; text_en: string; source_chunk_ids: string[] }
