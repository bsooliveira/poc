import { useCallback, useEffect, useRef, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { Activity, ArrowDownToLine, ArrowLeft, ArrowRight, BookOpen, Check, CheckCheck, ChevronRight, CircleHelp, Database, FileCheck2, FileText, FlaskConical, FolderOpen, Globe2, Layers3, LoaderCircle, MessageSquareText, Plus, Search, ShieldCheck, Sparkles, UploadCloud, X, Zap } from 'lucide-react'
import { api, download, login, setToken } from './api'
import TemplateSectionReview from './TemplateSectionReview'
import ManualsPage from './ManualsPage'
import type { AuditEntry, Chunk, Config, EventDetail, EventSummary, Item, System, Training } from './types'

const labels: Record<string, string> = { draft: 'Fontes pendentes', queued: 'Na fila', processing: 'Processando', review: 'Em revisão', approved: 'Aprovado', rejected: 'Ajustes solicitados', failed: 'Falha', completed: 'Concluído', running: 'Em execução' }
const stages: Record<string, string> = { queued: 'Aguardando processamento', indexing: 'Criando o índice de conhecimento', classification: 'Identificando os temas do evento', retrieval: 'Buscando as evidências relevantes', generation: 'Escrevendo perguntas em PT e EN', validation: 'Verificando fontes e equivalência', consolidation: 'Organizando sua FAQ', review: 'Pronto para revisão', failed: 'Processamento interrompido' }
const date = (value: string) => new Date(value).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
const pct = (value: number) => `${Math.round(value * 100)}%`
function Badge({ status }: { status: string }) { return <span className={`badge ${status}`}><span />{labels[status] || status}</span> }
function Empty({ icon, title, children }: { icon: ReactNode; title: string; children: ReactNode }) { return <div className="empty"><div className="empty-icon">{icon}</div><h3>{title}</h3><p>{children}</p></div> }

export default function App() {
  const [config, setConfig] = useState<Config | null>(null)
  const [authenticated, setAuthenticated] = useState(false)
  const [page, setPage] = useState('events')
  const [events, setEvents] = useState<EventSummary[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [modal, setModal] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)
  const [query, setQuery] = useState('')
  const [demoToken, setDemoToken] = useState('')
  const report = useCallback((e: unknown) => setError(e instanceof Error ? e.message : 'Algo deu errado. Tente novamente.'), [])
  const refreshEvents = useCallback(async () => setEvents(await api<EventSummary[]>('/events')), [])
  useEffect(() => { api<Config>('/config').then(c => { setConfig(c); if (c.auth_mode === 'local') setAuthenticated(true) }).catch(report) }, [report])
  useEffect(() => { if (authenticated) refreshEvents().catch(report) }, [authenticated, refreshEvents, report])
  useEffect(() => { if (notice) { const t = setTimeout(() => setNotice(''), 6000); return () => clearTimeout(t) } }, [notice])
  const navigate = (target: string) => { setPage(target); setSelected(null); setError(''); refreshEvents().catch(report) }
  async function useExample() {
    setBusy(true)
    try {
      const event = await api<EventDetail>('/events', { method: 'POST', body: JSON.stringify({ name: 'Encontro Horizonte · exemplo', company: 'Aurora Tecnologia (fictícia)', event_type: 'Evento online', event_date: '2026-11-20' }) })
      const text = await (await fetch('/examples/evento-horizonte.txt')).text()
      const form = new FormData(); form.append('kind', 'official'); form.append('files', new File([text], 'evento-horizonte.txt', { type: 'text/plain' }))
      await api(`/events/${event.id}/sources`, { method: 'POST', body: form })
      await refreshEvents(); setSelected(event.id); setNotice('Exemplo carregado. Confira as fontes e clique em Gerar FAQ.')
    } catch (e) { report(e) } finally { setBusy(false) }
  }
  if (!config) return <div className="startup"><div className="logo-mark"><MessageSquareText /></div><h1>SimplFAQ</h1>{error ? <p role="alert">{error}</p> : <LoaderCircle className="spin" />}</div>
  if (!authenticated) return <div className="startup"><div className="logo-mark"><MessageSquareText /></div><h1>SimplFAQ</h1><p>Conhecimento com fontes. Respostas com confiança.</p>{config.auth_mode === 'demo' && <label>Token local<input type="password" value={demoToken} onChange={e => setDemoToken(e.target.value)} /></label>}<button className="primary" onClick={async () => { try { if (config.auth_mode === 'entra') await login(config); else setToken(demoToken); await api('/me'); setAuthenticated(true) } catch (e) { report(e) } }}>Entrar {config.auth_mode === 'entra' ? 'com Microsoft' : 'na demonstração'}<ArrowRight size={16} /></button>{error && <p role="alert">{error}</p>}</div>
  const filtered = events.filter(e => (e.name + ' ' + e.company).toLowerCase().includes(query.toLowerCase()))
  return <div className="shell">
    <aside className="sidebar">
      <a href="#" className="brand" onClick={e => { e.preventDefault(); navigate('events') }}><span className="logo-mark"><MessageSquareText size={23} /></span><span>Simpl<span className="brand-light">FAQ</span><small>CONHECIMENTO COM CONFIANÇA</small></span></a>
      <div className="workspace"><span className="workspace-icon">P</span><div>Meu workspace<small>Laboratório local</small></div><ChevronRight size={15} /></div>
      <div className="nav-label">WORKSPACE</div>
      <nav aria-label="Navegação principal">
        <button className={page === 'events' ? 'active' : ''} onClick={() => navigate('events')}><FolderOpen size={19} />Meus eventos<span className="nav-count">{events.length}</span></button>
        <button className={page === 'history' ? 'active' : ''} onClick={() => navigate('history')}><BookOpen size={19} />Base aprovada</button>
        <button className={page === 'training' ? 'active' : ''} onClick={() => navigate('training')}><FlaskConical size={19} />Fine-tuning<span className="tiny">LAB</span></button>
        <button className={page === 'manuals' ? 'active' : ''} onClick={() => navigate('manuals')}><BookOpen size={19} />Manuais públicos B3</button>
        <button className={page === 'audit' ? 'active' : ''} onClick={() => navigate('audit')}><Activity size={19} />Trilha de auditoria</button>
      </nav>
      <div className="sidebar-note"><ShieldCheck size={21} /><strong>Você tem a última palavra.</strong><p>Toda FAQ passa por revisão humana antes de entrar na base de conhecimento.</p></div>
      <button className={`system-link ${page === 'system' ? 'active' : ''}`} onClick={() => navigate('system')}><span className="status-dot" />Ambiente local<ChevronRight size={15} /></button>
      <div className="profile"><div className="avatar">RL</div><div>Revisor local<small>Prova de conceito</small></div><span className="version">v1.0</span></div>
    </aside>
    <div className="main-shell">
      <header className="topbar"><div className="breadcrumb">Workspace <ChevronRight size={14} /><strong>{{ events: 'Meus eventos', history: 'Base aprovada', training: 'Fine-tuning', audit: 'Auditoria', system: 'Ambiente', manuals: 'Manuais públicos' }[page]}</strong>{selected && <><ChevronRight size={14} /><span>Evento</span></>}</div><div className="topbar-right"><span className="local-label"><span className="status-dot" />POC LOCAL</span><span className="topbar-separator" /><Globe2 size={16} /><span>PT / EN</span></div></header>
      <main>
        {error && <div className="alert error" role="alert"><CircleHelp size={18} /><span>{error}</span><button aria-label="Fechar erro" onClick={() => setError('')}><X size={18} /></button></div>}
        {notice && <div className="alert success" role="status"><Check size={18} /><span>{notice}</span><button aria-label="Fechar mensagem" onClick={() => setNotice('')}><X size={18} /></button></div>}
        {selected ? <EventWorkspace key={selected} id={selected} config={config} back={() => { setSelected(null); refreshEvents().catch(report) }} report={report} notify={setNotice} /> : <>
          {page === 'events' && <>
            <div className="page-heading"><div className="eyebrow">DO DOCUMENTO À RESPOSTA</div><div className="heading-row"><div><h1>Menos trabalho repetido.<br /><span>Mais conhecimento compartilhado.</span></h1><p>Crie FAQs em português e inglês, com evidências em cada resposta.</p></div><button className="primary" onClick={() => setModal(true)}><Plus size={18} />Novo evento</button></div></div>
            <div className="intro-card"><div><div className="intro-icon"><Sparkles size={21} /></div><h2>Seus documentos. Uma FAQ pronta para revisar.</h2><p>A IA organiza as perguntas. As fontes sustentam as respostas. Você aprova.</p><button className="text-button" disabled={busy} onClick={useExample}>Explorar um evento de exemplo {busy ? <LoaderCircle size={16} className="spin" /> : <ArrowRight size={16} />}</button></div><div className="flow"><FlowStep number="01" icon={<UploadCloud size={20} />} label="Adicione fontes" detail="Documentos do evento" /><span className="flow-line" /><FlowStep number="02" icon={<Sparkles size={20} />} label="Gere em PT + EN" detail="Com contexto e evidências" /><span className="flow-line" /><FlowStep number="03" icon={<FileCheck2 size={20} />} label="Revise e aprove" detail="Conhecimento validado" /></div></div>
            <div className="stats"><Stat icon={<FolderOpen size={19} />} number={events.length} label="Eventos no workspace" /><Stat icon={<FileText size={19} />} number={events.filter(e => e.status === 'review').length} label="Aguardando sua revisão" /><Stat icon={<ShieldCheck size={19} />} number={events.filter(e => e.status === 'approved').length} label="FAQs aprovadas" /></div>
            <div className="section-heading"><div><h2>Seus eventos <span className="count">{events.length}</span></h2><p>Cada evento reúne suas fontes, respostas e decisões.</p></div><label className="search-input"><Search size={17} /><input aria-label="Buscar eventos" placeholder="Buscar um evento..." value={query} onChange={e => setQuery(e.target.value)} /></label></div>
            {filtered.length ? <div className="event-grid">{filtered.map(event => <EventCard key={event.id} event={event} open={() => setSelected(event.id)} />)}</div> : <div className="empty-panel"><Empty icon={<FolderOpen size={32} />} title={query ? 'Nenhum evento encontrado' : 'Seu próximo evento começa aqui'}>{query ? 'Tente outro nome ou empresa.' : 'Adicione seus documentos ou explore o exemplo para conhecer o fluxo.'}</Empty>{!query && <button className="secondary" onClick={() => setModal(true)}><Plus size={16} />Criar primeiro evento</button>}</div>}
          </>}
          {page === 'history' && <><PageTitle eyebrow="CONHECIMENTO REVISADO" title="Base aprovada" description="FAQs que passaram por revisão humana. Usadas como referência de estrutura e cobertura." /><div className="info-strip"><ShieldCheck size={20} />Os fatos do evento atual sempre têm prioridade sobre o histórico.</div>{events.some(e => e.status === 'approved') ? <div className="event-grid">{events.filter(e => e.status === 'approved').map(event => <EventCard key={event.id} event={event} open={() => setSelected(event.id)} />)}</div> : <Empty icon={<BookOpen size={32} />} title="Uma base construída com confiança">As FAQs aparecerão aqui depois da sua aprovação.</Empty>}</>}
          {page === 'training' && <TrainingPage report={report} notify={setNotice} />}
          {page === 'audit' && <><PageTitle eyebrow="RASTREABILIDADE" title="Cada decisão tem uma história" description="Uploads, gerações, edições e aprovações registrados em uma trilha persistente." /><AuditTable report={report} /></>}
          {page === 'system' && <SystemPage report={report} config={config} />}
          {page === 'manuals' && <ManualsPage report={report} />}
        </>}
      </main>
      <footer>SimplFAQ <span>·</span> Conhecimento com fontes, revisão com responsabilidade.<span className="footer-right">Feito para conectar perguntas e respostas.</span></footer>
    </div>
    {modal && <NewEvent close={() => setModal(false)} report={report} created={async event => { setModal(false); await refreshEvents(); setSelected(event.id) }} />}
  </div>
}

function FlowStep({ number, icon, label, detail }: { number: string; icon: ReactNode; label: string; detail: string }) { return <div className="flow-step"><div className="flow-icon">{icon}<span>{number}</span></div><strong>{label}</strong><small>{detail}</small></div> }
function Stat({ icon, number, label }: { icon: ReactNode; number: number; label: string }) { return <div className="stat"><div className="stat-icon">{icon}</div><div><strong>{number.toString().padStart(2, '0')}</strong><span>{label}</span></div></div> }
function PageTitle({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) { return <div className="page-heading"><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div> }
function EventCard({ event, open }: { event: EventSummary; open: () => void }) { return <button className="event-card" onClick={open}><div className="card-top"><div className="event-icon"><FileText size={23} /></div><Badge status={event.status} /></div><small className="event-company">{event.company || 'EVENTO CORPORATIVO'}</small><h3>{event.name}</h3><p>{event.event_type}</p><div className="card-bottom"><span><Layers3 size={14} />{event.source_count || 0} fontes <span className="dot">·</span> v{event.version}</span><span>Abrir evento <ArrowRight size={15} /></span></div></button> }

function NewEvent({ close, report, created }: { close: () => void; report: (e: unknown) => void; created: (e: EventDetail) => Promise<void> }) {
  const [busy, setBusy] = useState(false)
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); const values = Object.fromEntries(new FormData(e.currentTarget)); setBusy(true)
    try { const event = await api<EventDetail>('/events', { method: 'POST', body: JSON.stringify({ ...values, event_date: values.event_date || null }) }); await created(event) } catch (error) { report(error) } finally { setBusy(false) }
  }
  return <div className="modal-backdrop" onClick={e => { if (e.target === e.currentTarget && !busy) close() }}><section className="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title"><div className="modal-heading"><div className="event-icon"><Plus /></div><button aria-label="Fechar" disabled={busy} onClick={close}><X size={22} /></button></div><h2 id="modal-title">Um novo evento, novas respostas.</h2><p>Comece com as informações básicas. Depois, adicione suas fontes.</p><form onSubmit={submit}><label>Nome do evento<input name="name" required minLength={3} maxLength={180} autoFocus placeholder="Ex.: Divulgação de resultados · 3T26" /></label><label>Empresa<input name="company" maxLength={180} placeholder="Nome da empresa" /></label><div className="form-row"><label>Tipo de evento<select name="event_type"><option>Comunicado corporativo</option><option>Divulgação de resultados</option><option>Evento online</option><option>Assembleia</option><option>Outro</option></select></label><label>Data do evento<input name="event_date" type="date" /></label></div><div className="modal-actions"><button type="button" className="secondary" onClick={close} disabled={busy}>Cancelar</button><button className="primary" disabled={busy}>{busy ? <LoaderCircle className="spin" size={17} /> : <ArrowRight size={17} />}Criar evento</button></div></form></section></div>
}

function EventWorkspace({ id, config, back, report, notify }: { id: string; config: Config; back: () => void; report: (e: unknown) => void; notify: (s: string) => void }) {
  const [event, setEvent] = useState<EventDetail | null>(null)
  const [loadError, setLoadError] = useState('')
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('faq')
  const [kind, setKind] = useState('official')
  const [busy, setBusy] = useState(false)
  const [note, setNote] = useState('')
  const [decision, setDecision] = useState<'approve' | 'reject' | null>(null)
  const input = useRef<HTMLInputElement>(null)
  const reload = useCallback(async () => {
    setLoading(true)
    try {
      setEvent(await api<EventDetail>(`/events/${id}`, { signal: AbortSignal.timeout(15000) }))
      setLoadError('')
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : 'Não foi possível carregar o evento.')
      throw error
    } finally { setLoading(false) }
  }, [id])
  useEffect(() => { reload().catch(() => {}) }, [reload])
  const processing = event?.status === 'queued' || event?.status === 'processing'
  useEffect(() => { if (processing) { const t = setInterval(() => reload().catch(report), 4000); return () => clearInterval(t) } }, [processing, reload, report])
  async function upload(files: FileList | File[]) {
    if (!files.length) return
    setBusy(true)
    try { const form = new FormData(); form.append('kind', kind); Array.from(files).forEach(f => form.append('files', f)); await api(`/events/${id}/sources`, { method: 'POST', body: form }); await reload(); notify('Fontes adicionadas. Gere a FAQ para indexar e processar os documentos.') } catch (e) { report(e) } finally { setBusy(false); if (input.current) input.current.value = '' }
  }
  async function generate() { setBusy(true); try { await api(`/events/${id}/runs`, { method: 'POST' }); await reload() } catch (e) { report(e) } finally { setBusy(false) } }
  async function submitDecision(e: FormEvent) {
    e.preventDefault(); setBusy(true)
    try { await api(`/events/${id}/decision`, { method: 'POST', body: JSON.stringify({ expected_version: event!.version, decision, note }) }); setDecision(null); setNote(''); await reload(); notify(decision === 'approve' ? 'FAQ aprovada e incorporada ao histórico.' : 'Ajustes registrados. Você pode editar ou gerar uma nova versão.') } catch (error) { report(error) } finally { setBusy(false) }
  }
  if (!event) return <>
    <button className="back-button" onClick={back}><ArrowLeft size={16} />Voltar aos eventos</button>
    {loading ? <div className="loading" role="status"><LoaderCircle className="spin" />Carregando evento...</div> : <div className="empty-panel"><div className="alert error" role="alert"><CircleHelp size={18} /><span>{loadError}</span></div><button className="primary" onClick={() => reload().catch(() => {})}>Tentar novamente</button></div>}
  </>
  const locked = processing || event.status === 'approved'
  const result = event.result
  const reviewed = result?.items.filter(i => i.reviewed).length || 0
  return <>
    <button className="back-button" onClick={back}><ArrowLeft size={16} />Voltar aos eventos</button>
    <div className="event-heading"><div><div className="eyebrow">{event.company || 'WORKSPACE'} <span> / </span> {event.event_type}</div><h1>{event.name}</h1><div className="event-meta"><Badge status={event.status} /><span>Versão {event.version}</span><span>Criado em {date(event.created_at)}</span></div></div><div className="heading-actions">{result && <button className="secondary" onClick={() => download(`/events/${id}/document`, `SimplFAQ-${event.name}.docx`).catch(report)}><ArrowDownToLine size={17} />Exportar Word</button>}{!locked && <button className="primary" disabled={busy} onClick={generate}>{busy ? <LoaderCircle size={17} className="spin" /> : <Sparkles size={17} />}{result ? 'Gerar nova versão' : 'Gerar FAQ'}</button>}</div></div>
    {event.error && <div className="alert error"><CircleHelp size={18} />{event.error}</div>}
    {result && !result.template_version && <div className="info-strip">Esta FAQ conserva o formato anterior. {event.status === 'approved' ? 'Crie outro evento para elaborar uma FAQ com as 12 seções atuais.' : 'Gerar nova versão aplica o template de 12 seções e preserva o resultado anterior no histórico de versões.'}</div>}
    {!!event.normative_warnings?.length && <div className="alert error"><CircleHelp size={18} /><div>{event.normative_warnings.map(warning => <p key={warning}>{warning}</p>)}<p>Atualize as evidências antes de aprovar esta FAQ.</p></div></div>}
    {processing && <div className="processing-panel" role="status"><div className="processing-orb"><Sparkles size={25} /></div><div><strong>{stages[event.runs[0]?.stage] || 'Preparando a FAQ'}</strong><p>A geração acontece no notebook e pode levar alguns minutos. Você pode navegar enquanto o processamento continua.</p><div className="progress-track"><span /></div></div><Badge status={event.status} /></div>}
    <div className="event-layout"><aside className="source-panel"><div className="panel-title"><h2>Fontes do evento</h2><span className="count">{event.sources.length}</span></div><p className="muted">O ponto de partida de cada resposta.</p>{!locked && <><label className="compact-label">Tipo de fonte<select value={kind} onChange={e => setKind(e.target.value)}>{Object.entries(config.source_types).map(([key, value]) => <option key={key} value={key}>{value}</option>)}</select></label><input className="hidden-input" ref={input} type="file" multiple accept={config.extensions.join(',')} onChange={e => e.target.files && upload(e.target.files)} /><button className="upload-zone" disabled={busy} onClick={() => input.current?.click()} onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); if (!busy) upload(e.dataTransfer.files) }}><UploadCloud size={27} /><strong>{busy ? 'Adicionando fontes...' : 'Solte seus arquivos aqui'}</strong><span>ou clique para selecionar</span><small>PDF, Word, Excel, slides e texto<br />Até {config.max_upload_mb} MB por arquivo</small></button></>}
      <div className="source-list">{event.sources.map(s => <div className="source-file" key={s.id}><FileText size={20} /><div><strong title={s.name}>{s.name}</strong><small>{config.source_types[s.kind]} · v{s.version}</small><small>{(s.size / 1024).toFixed(1)} KB</small></div><Check size={14} /></div>)}</div>
      <div className="source-hint"><ShieldCheck size={17} /><p>Fontes oficiais têm prioridade. O histórico ajuda na estrutura, sem substituir os fatos atuais.</p></div>
    </aside><section className="result-panel"><div className="tabs" role="tablist" aria-label="Conteúdo do evento">{[['faq', 'FAQ e revisão', MessageSquareText], ['sources', 'Explorar RAG', Search], ['activity', 'Atividade', Activity]].map(([key, label, Icon]) => { const IconComponent = Icon as typeof Search; return <button key={String(key)} role="tab" aria-selected={tab === key} className={tab === key ? 'active' : ''} onClick={() => setTab(String(key))}><IconComponent size={17} />{String(label)}{key === 'faq' && result && <span className="count">{result.items.length}</span>}</button> })}</div>
      {tab === 'faq' && <>{result ? <div className="faq-content"><div className="review-summary"><div><span className="eyebrow">PORTUGUÊS + ENGLISH</span><h2>{event.status === 'approved' ? 'Respostas revisadas e aprovadas' : 'Sua revisão faz a diferença'}</h2><p>{reviewed} de {result.items.length} perguntas revisadas · Confira fontes, condições e tradução.</p></div><div className="review-ring">{reviewed}<small>/{result.items.length}</small></div></div>
        {(result.gaps.length > 0 || result.conflicts.length > 0) && <details className="validation-alert"><summary><CircleHelp size={17} />{result.gaps.length + result.conflicts.length} pontos de atenção</summary><ul>{[...result.conflicts, ...result.gaps].map((t, n) => <li key={n}>{t}</li>)}</ul></details>}
        <div className="metric-pills"><span><Database size={14} />Cobertura de fontes: {pct(result.metrics.source_coverage || 0)}</span><span><Layers3 size={14} />{result.metrics.used_chunks}/{result.metrics.total_chunks} trechos citados</span><span><Globe2 size={14} />Equivalência automática: {pct(result.metrics.equivalence_rate || 0)}</span></div>
        {result.sections ? (result.template_snapshot || config.template).sections.map(definition => {
          const assessment = result.sections!.find(s => s.section_id === definition.id)!
          return <section key={definition.id} aria-label={definition.title_pt}><TemplateSectionReview event={event} section={assessment} definition={definition} template={result.template_snapshot || config.template} reload={reload} report={report} />{result.items.filter(i=>i.section_id===definition.id).map(item=><ItemEditor key={item.id} item={item} index={result.items.indexOf(item)} event={event} locked={event.status === 'approved'} reload={reload} report={report} />)}</section>
        }) : result.items.map((item, n) => <ItemEditor key={item.id} item={item} index={n} event={event} locked={event.status === 'approved'} reload={reload} report={report} />)}
        {event.status !== 'approved' ? <div className="approval-bar"><div><ShieldCheck size={23} /><span><strong>Pronto para entrar na base?</strong><small>Revise todos os itens e registre sua decisão.</small></span></div><div><button className="secondary" disabled={busy} onClick={() => setDecision('reject')}>Solicitar ajustes</button><button className="primary" disabled={busy || !result.items.length || reviewed !== result.items.length || !!result.sections?.some(s=>!s.reviewed)} onClick={() => setDecision('approve')}><CheckCheck size={17} />Aprovar FAQ</button></div></div> : <div className="approved-banner"><ShieldCheck size={24} /><div><strong>Esta FAQ faz parte da base aprovada.</strong><p>{result.approval?.note}</p><small>{result.approval?.timestamp && date(result.approval.timestamp)}</small></div></div>}
      </div> : <Empty icon={processing ? <LoaderCircle className="spin" size={32} /> : <MessageSquareText size={36} />} title={processing ? 'Construindo respostas com contexto' : 'Suas respostas começam nas fontes'}>{processing ? 'Acompanhe a etapa atual acima. O resultado aparecerá aqui para revisão.' : 'Adicione os documentos do evento e clique em Gerar FAQ. As perguntas em PT e EN aparecerão aqui, lado a lado.'}</Empty>}</>}
      {tab === 'sources' && <RagExplorer id={id} report={report} />}
      {tab === 'activity' && <div className="activity-content"><AuditTable eventId={id} report={report} /></div>}
    </section></div>
    {decision && <div className="modal-backdrop"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="decision-title"><h2 id="decision-title">{decision === 'approve' ? 'Aprovar esta FAQ?' : 'Registrar ajustes necessários'}</h2><p>{decision === 'approve' ? 'Confirme a revisão das fontes, da tradução e dos pontos de atenção. A versão aprovada será preservada e poderá ser usada como referência histórica.' : 'Descreva os ajustes para manter a decisão rastreável.'}</p><form onSubmit={submitDecision}><label>Nota de revisão<textarea required minLength={5} maxLength={5000} value={note} onChange={e => setNote(e.target.value)} placeholder="O que foi conferido? Como os pontos de atenção foram tratados?" /></label><div className="modal-actions"><button type="button" className="secondary" disabled={busy} onClick={() => setDecision(null)}>Cancelar</button><button className="primary" disabled={busy}>{busy && <LoaderCircle className="spin" size={16} />}Confirmar {decision === 'approve' ? 'aprovação' : 'ajustes'}</button></div></form></section></div>}
  </>
}

function ItemEditor({ item, index, event, locked, reload, report }: { item: Item; index: number; event: EventDetail; locked: boolean; reload: () => Promise<void>; report: (e: unknown) => void }) {
  const [draft, setDraft] = useState(item)
  const [busy, setBusy] = useState(false)
  const [editing, setEditing] = useState(false)
  async function save() {
    setBusy(true)
    try { await api(`/events/${event.id}/items/${item.id}`, { method: 'PATCH', body: JSON.stringify({ expected_version: event.version, section_id: draft.section_id, claims: draft.claims, domain: draft.domain, question_pt: draft.question_pt, answer_pt: draft.answer_pt, question_en: draft.question_en, answer_en: draft.answer_en, source_chunk_ids: draft.source_chunk_ids, reviewed: draft.reviewed, review_note: draft.review_note || '' }) }); await reload(); setEditing(false) } catch (e) { report(e) } finally { setBusy(false) }
  }
  const displayedClaims = editing ? draft.claims : item.claims
  const evidence = event.result!.evidence.filter(c => item.source_chunk_ids.includes(c.id))
  const field = (key: 'question_pt' | 'answer_pt' | 'question_en' | 'answer_en', title: string) => <label>{title}<textarea value={draft[key]} rows={key.startsWith('answer') ? 5 : 2} onChange={e => setDraft({ ...draft, [key]: e.target.value, reviewed: false })} /></label>
  return <article className={`qa-card ${item.reviewed ? 'is-reviewed' : ''}`}><div className="qa-heading"><span className="question-number">{String(index + 1).padStart(2, '0')}</span><span className="domain-tag">{item.domain}</span><span className={`review-state ${item.reviewed ? 'checked' : ''}`}>{item.reviewed ? <><CheckCheck size={15} />Revisado</> : <><CircleHelp size={14} />Revisão pendente</>}</span></div><div className="bilingual"><section><div className="language-label">PT <span>PORTUGUÊS</span></div>{editing ? <>{field('question_pt', 'Pergunta em português')}{field('answer_pt', 'Resposta em português')}</> : <><h3>{item.question_pt}</h3><p>{item.answer_pt}</p></>}</section><section><div className="language-label">EN <span>ENGLISH</span></div>{editing ? <>{field('question_en', 'Question in English')}{field('answer_en', 'Answer in English')}</> : <><h3>{item.question_en}</h3><p>{item.answer_en}</p></>}</section></div>
    <div className="qa-evidence"><span><Layers3 size={14} />Evidências</span>{evidence.map(c => <details key={c.id}><summary><FileText size={13} />{c.source_name}<ChevronRight size={13} /></summary><p>{c.text}</p><small>{c.location} · v{c.source_version ?? '—'} · {c.system || 'Evento atual'} · {c.id}</small>{c.url && <p><a href={c.url} target="_blank" rel="noreferrer">PDF oficial</a></p>}{c.sha256 && <code>{c.sha256}</code>}</details>)}{!evidence.length && <span className="danger-text">Citação inválida: corrija os IDs abaixo.</span>}</div>
    {!item.reviewed && item.review_reason && <div className="review-reason"><CircleHelp size={14} /><span>{item.review_reason}</span></div>}
    {editing && <div className="review-form"><label>Domínio da pergunta{event.result?.template_snapshot ? <select value={draft.section_id} onChange={e=>setDraft({...draft,section_id:e.target.value,domain:event.result!.template_snapshot!.sections.find(s=>s.id===e.target.value)!.title_pt,reviewed:false})}>{event.result.template_snapshot.sections.map(s=><option key={s.id} value={s.id}>{s.number}. {s.title_pt}</option>)}</select> : <input value={draft.domain} maxLength={100} onChange={e => setDraft({ ...draft, domain: e.target.value, reviewed: false })} />}</label><label>IDs dos trechos factuais (separados por vírgula)<input value={draft.source_chunk_ids.join(', ')} onChange={e => setDraft({ ...draft, source_chunk_ids: e.target.value.split(',').map(s => s.trim()).filter(Boolean), reviewed: false })} /></label><label>Registro da revisão<textarea rows={2} value={draft.review_note || ''} onChange={e => setDraft({ ...draft, review_note: e.target.value })} placeholder="Descreva a conferência das fontes, dos números, das condições e da tradução." /></label><label className="checkbox-label"><input type="checkbox" checked={draft.reviewed} onChange={e => setDraft({ ...draft, reviewed: e.target.checked })} />Conferi as evidências e confirmo a equivalência entre PT e EN.</label></div>}
    {displayedClaims && <details className="review-form"><summary>Afirmações e fontes específicas</summary>{displayedClaims.map((claim,index)=><div key={index}>{editing ? <><label>Afirmação {index+1} em português<textarea value={claim.text_pt} onChange={e=>setDraft({...draft,reviewed:false,claims:draft.claims!.map((c,n)=>n===index?{...c,text_pt:e.target.value}:c)})}/></label><label>Afirmação {index+1} em inglês<textarea value={claim.text_en} onChange={e=>setDraft({...draft,reviewed:false,claims:draft.claims!.map((c,n)=>n===index?{...c,text_en:e.target.value}:c)})}/></label><label>IDs das fontes da afirmação {index+1}<input value={claim.source_chunk_ids.join(', ')} onChange={e=>setDraft({...draft,reviewed:false,claims:draft.claims!.map((c,n)=>n===index?{...c,source_chunk_ids:e.target.value.split(',').map(s=>s.trim()).filter(Boolean)}:c)})}/></label></> : <><p>{claim.text_pt}</p><p>{claim.text_en}</p><small>{claim.source_chunk_ids.map(id=>evidence.find(c=>c.id===id)?.source_name+' · '+id).join('; ')}</small></>}</div>)}{editing&&<button className="secondary small" onClick={()=>{const split=(s:string)=>s.split(/(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ])|\n+/).filter(Boolean);const en=split(draft.answer_en);setDraft({...draft,reviewed:false,claims:split(draft.answer_pt).map((text_pt,n)=>({text_pt,text_en:en[n]||'',source_chunk_ids:[...draft.source_chunk_ids]}))})}}>Recriar afirmações do texto atual para conferência</button>}</details>}
    {!locked && <div className="qa-actions">{editing ? <><button className="text-button" disabled={busy} onClick={() => { setEditing(false); setDraft(item) }}>Cancelar</button><button className="primary small" disabled={busy} onClick={save}>{busy ? <LoaderCircle size={15} className="spin" /> : <Check size={15} />}Salvar revisão</button></> : <button className="secondary small" onClick={() => { setDraft(item); setEditing(true) }}>{item.reviewed ? 'Editar revisão' : 'Revisar pergunta'}<ArrowRight size={14} /></button>}</div>}
  </article>
}

function RagExplorer({ id, report }: { id: string; report: (e: unknown) => void }) {
  const [query, setQuery] = useState('')
  const [chunks, setChunks] = useState<Chunk[]>([])
  const [busy, setBusy] = useState(false)
  const [searched, setSearched] = useState(false)
  async function search(e: FormEvent) { e.preventDefault(); setBusy(true); try { setChunks(await api<Chunk[]>(`/events/${id}/search?q=${encodeURIComponent(query)}`)); setSearched(true) } catch (error) { report(error) } finally { setBusy(false) } }
  return <div className="rag-content"><h2>Encontre a origem das respostas</h2><p className="muted">Explore os trechos recuperados por similaridade e prioridade de fonte.</p><form className="rag-search" onSubmit={search}><Search size={18} /><input required minLength={2} maxLength={500} aria-label="Pesquisar nas fontes" value={query} onChange={e => setQuery(e.target.value)} placeholder="Ex.: Qual é o prazo de inscrição?" /><button className="primary small" disabled={busy}>{busy ? <LoaderCircle className="spin" size={16} /> : 'Buscar'}</button></form>{chunks.map(c => <article className="chunk-card" key={c.id}><div><strong><FileText size={16} />{c.source_name}</strong><span className="score">Similaridade {pct(c.score || 0)}</span></div><p>{c.text}</p><small>{c.location} · Prioridade {c.priority}</small><code>{c.id}</code></article>)}{!chunks.length && <Empty icon={<Database size={30} />} title={searched ? 'Nenhum trecho acima do limiar' : 'Uma busca, todas as evidências'}>{searched ? 'Tente uma pergunta com termos mais próximos do documento.' : 'Após gerar a FAQ, pesquise os documentos indexados do evento.'}</Empty>}</div>
}

function AuditTable({ eventId, report }: { eventId?: string; report: (e: unknown) => void }) {
  const [entries, setEntries] = useState<AuditEntry[]>([])
  const [busy, setBusy] = useState(true)
  useEffect(() => { api<AuditEntry[]>('/audit' + (eventId ? `?event_id=${eventId}` : '')).then(setEntries).catch(report).finally(() => setBusy(false)) }, [eventId, report])
  async function more() { setBusy(true); try { const rows = await api<AuditEntry[]>(`/audit?before=${entries[entries.length - 1]?.id}${eventId ? `&event_id=${eventId}` : ''}`); setEntries(old => [...old, ...rows]) } catch (e) { report(e) } finally { setBusy(false) } }
  return <div className="audit-list">{entries.map(entry => <details key={entry.id} className="audit-entry"><summary><span className="audit-dot"><Activity size={14} /></span><span><strong>{entry.action}</strong><small>{entry.actor} · {date(entry.timestamp)}</small></span><span className="audit-id">#{entry.id}</span><ChevronRight size={16} /></summary><pre>{JSON.stringify(entry.details, null, 2)}</pre></details>)}{!entries.length && <Empty icon={<Activity size={30} />} title={busy ? 'Carregando registros' : 'Tudo começa com uma ação'}>As atividades serão registradas automaticamente aqui.</Empty>}{entries.length >= 200 && <button className="secondary" onClick={more} disabled={busy}>Carregar registros anteriores</button>}</div>
}

function TrainingPage({ report, notify }: { report: (e: unknown) => void; notify: (s: string) => void }) {
  const [training, setTraining] = useState<Training | null>(null)
  const [busy, setBusy] = useState(false)
  const [confirmed, setConfirmed] = useState(false)
  const reload = useCallback(async () => setTraining(await api<Training>('/training')), [])
  useEffect(() => { reload().catch(report); const t = setInterval(() => reload().catch(report), 5000); return () => clearInterval(t) }, [reload, report])
  async function start() { setBusy(true); try { await api('/training', { method: 'POST' }); await reload(); setConfirmed(false); notify('Experimento de fine-tuning iniciado. Acompanhe o resultado nesta página.') } catch (e) { report(e) } finally { setBusy(false) } }
  return <><PageTitle eyebrow="LABORATÓRIO DE APRENDIZADO" title="Ajuste o estilo. Preserve as evidências." description="Experimente fine-tuning local com perguntas e respostas aprovadas por você." /><div className="training-layout"><div className="training-card"><div className="intro-icon"><FlaskConical size={24} /></div><h2>Um pequeno experimento LoRA</h2><p>O treinamento adapta uma pequena parte do modelo a exemplos revisados. O RAG continua sendo a fonte dos fatos.</p><div className="training-facts"><div><span>Modelo base</span><strong>{training?.base_model || 'Carregando...'}</strong></div><div><span>Exemplos aprovados</span><strong>{training?.available_samples || 0} <small>/ mínimo de 4</small></strong></div><div><span>Configuração local</span><strong>CPU · 8 passos · LoRA rank 4</strong></div></div><label className="checkbox-label"><input type="checkbox" checked={confirmed} onChange={e => setConfirmed(e.target.checked)} />Entendo que este é um experimento. O adapter será salvo para avaliação e não será ativado automaticamente.</label><div className="training-actions"><button className="primary" disabled={busy || !confirmed || !training?.training_available || training.available_samples < 4 || training.runs.some(r => ['queued', 'running'].includes(r.status))} onClick={start}><Zap size={17} />Iniciar experimento</button><button className="secondary" disabled={!training?.available_samples} onClick={() => download('/training/dataset', 'simplfaq-aprovado.jsonl').catch(report)}><ArrowDownToLine size={17} />Exportar dataset</button></div></div><aside className="training-explainer"><h3>O que muda em cada etapa?</h3><div><Database size={21} /><section><strong>RAG encontra os fatos</strong><p>Busca documentos atuais, guarda as fontes e dá contexto ao modelo.</p></section></div><div><FlaskConical size={21} /><section><strong>Fine-tuning aprende padrões</strong><p>Exemplos aprovados ajudam a experimentar tom, formato e consistência.</p></section></div><div><ShieldCheck size={21} /><section><strong>A revisão continua com você</strong><p>Um loss menor não prova maior precisão. Avalie o adapter antes de qualquer uso.</p></section></div></aside></div><div className="section-heading"><div><h2>Experimentos</h2><p>Artefatos, configuração e métricas de cada treinamento.</p></div></div>{training?.runs.map(run => <div className="training-run" key={run.id}><div><FlaskConical size={21} /><span><strong>{run.config.model}</strong><small>{date(run.created_at)} · {run.config.samples} exemplos · {run.config.max_steps} passos</small></span><Badge status={run.status} /></div>{run.error && <p className="danger-text">{run.error}</p>}{run.metrics && <><div className="metric-pills"><span>Loss inicial: {run.metrics.validation_loss_before?.toFixed(3) ?? 'Sem holdout'}</span><span>Loss final: {run.metrics.validation_loss_after?.toFixed(3) ?? 'Sem holdout'}</span><span>{Math.round(run.metrics.elapsed_seconds)}s de treinamento</span></div><button className="secondary small" onClick={() => download(`/training/${run.id}/artifact`, `simplfaq-adapter-${run.id}.zip`).catch(report)}><ArrowDownToLine size={16} />Baixar adapter LoRA</button></>}</div>)}{!training?.runs.length && <Empty icon={<FlaskConical size={30} />} title="Seu laboratório está pronto">Aprove ao menos duas perguntas bilíngues para preparar o primeiro experimento.</Empty>}</>
}

function SystemPage({ report, config }: { report: (e: unknown) => void; config: Config }) {
  const [system, setSystem] = useState<System | null>(null)
  useEffect(() => { api<System>('/system').then(setSystem).catch(report) }, [report])
  return <><PageTitle eyebrow="INFRAESTRUTURA DA POC" title="Tudo perto dos seus documentos." description="Processamento e persistência no Podman do AlmaLinux, dentro do WSL." /><div className="system-grid"><div className="system-card"><Sparkles /><h3>Geração local</h3><strong>{config.model}</strong><p>{system?.model_error || (system?.models.includes(config.model) ? 'Modelo disponível para processamento' : 'Verificando disponibilidade do modelo')}</p></div><div className="system-card"><Database /><h3>Busca semântica</h3><strong>{config.embedding_model}</strong><p>Embeddings multilíngues e índice vetorial local.</p></div><div className="system-card"><ShieldCheck /><h3>Acesso da POC</h3><strong>{config.auth_mode === 'local' ? 'Somente neste notebook' : config.auth_mode}</strong><p>Sem credenciais corporativas. Porta publicada em loopback.</p></div></div><div className="info-strip"><CircleHelp size={20} />Os modelos são baixados no primeiro uso. Depois do download, os documentos são processados localmente.</div><div className="stats"><Stat icon={<FolderOpen size={19} />} number={system?.totals.events || 0} label="Eventos persistidos" /><Stat icon={<Layers3 size={19} />} number={system?.totals.chunks || 0} label="Trechos indexados" /><Stat icon={<Activity size={19} />} number={system?.totals.audit || 0} label="Registros de auditoria" /></div></>
}
