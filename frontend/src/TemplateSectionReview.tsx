import { useState } from 'react'
import { api } from './api'
import type { EventDetail, SectionAssessment, TemplateSection, FAQTemplate } from './types'

export default function TemplateSectionReview({ event, section, definition, template, reload, report }: { event: EventDetail; section: SectionAssessment; definition: TemplateSection; template: FAQTemplate; reload: () => Promise<void>; report: (e: unknown) => void }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(section)
  const [busy, setBusy] = useState(false)
  const evidence = event.result?.evidence.filter(c => section.evidence_chunk_ids.includes(c.id)) || []
  async function save() {
    setBusy(true)
    try {
      await api(`/events/${event.id}/sections/${section.section_id}`, {method:'PATCH',body:JSON.stringify({expected_version:event.version,section_id:section.section_id,status:draft.status,reason_pt:draft.reason_pt,reason_en:draft.reason_en,evidence_chunk_ids:draft.evidence_chunk_ids,reviewed:draft.reviewed,review_note:draft.review_note})})
      await reload(); setEditing(false)
    } catch(e) { report(e) } finally { setBusy(false) }
  }
  return <div className="template-section"><div className="section-heading"><div><h3>{definition.number}. {definition.title_pt}</h3><small>{definition.title_en}</small></div><span className={`badge ${section.reviewed ? 'approved' : 'review'}`}>{template.states[section.status]?.pt} · {section.reviewed ? 'Revisada' : 'Pendente'}</span></div><p>{section.reason_pt}</p><p className="muted">{section.reason_en}</p>{section.generation_warning && <p className="danger-text">{section.generation_warning}</p>}{evidence.map(c=><details className="audit-entry" key={c.id}><summary>{c.source_name} · {c.location} · v{c.source_version ?? '—'}</summary><p>{c.text}</p><code>{c.id}</code></details>)}{editing ? <div className="review-form"><label>Aplicabilidade<select value={draft.status} onChange={e=>setDraft({...draft,status:e.target.value,reviewed:false})}>{Object.entries(template.states).map(([key,value])=><option key={key} value={key}>{value.pt}</option>)}</select></label><label>Justificativa em português<textarea value={draft.reason_pt} onChange={e=>setDraft({...draft,reason_pt:e.target.value,reviewed:false})} /></label><label>Justificativa em inglês<textarea value={draft.reason_en} onChange={e=>setDraft({...draft,reason_en:e.target.value,reviewed:false})} /></label><label>IDs das evidências do evento<input value={draft.evidence_chunk_ids.join(', ')} onChange={e=>setDraft({...draft,evidence_chunk_ids:e.target.value.split(',').map(s=>s.trim()).filter(Boolean),reviewed:false})} /></label><label>Nota de revisão da seção<textarea value={draft.review_note} onChange={e=>setDraft({...draft,review_note:e.target.value})} /></label><label className="checkbox-label"><input type="checkbox" checked={draft.reviewed} onChange={e=>setDraft({...draft,reviewed:e.target.checked})} />Conferi a aplicabilidade, as justificativas PT/EN e as pendências.</label><div className="modal-actions"><button className="secondary" disabled={busy} onClick={()=>setEditing(false)}>Cancelar seção</button><button className="primary" disabled={busy} onClick={save}>Salvar seção</button></div></div> : event.status !== 'approved' && <button className="secondary small" onClick={()=>{setDraft(section);setEditing(true)}}>Revisar seção {definition.number}</button>}</div>
}
