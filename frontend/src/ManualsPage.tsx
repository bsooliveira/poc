import { useCallback, useEffect, useState } from 'react'
import { api } from './api'
import type { Chunk } from './types'

type Manual = { id:string; system:string; title:string; url:string; version:string; effective_from:string; status:string; verified_at:string; sha256:string; page_count:number; chunk_count:number }
type Catalog = {documents:Manual[];jobs:{id:string;status:string;error:string|null;created_at:string}[]}

export default function ManualsPage({report}:{report:(e:unknown)=>void}) {
  const [catalog,setCatalog]=useState<Catalog|null>(null)
  const [system,setSystem]=useState('depositaria')
  const [query,setQuery]=useState('')
  const [chunks,setChunks]=useState<Chunk[]>([])
  const [busy,setBusy]=useState(false)
  const reload=useCallback(async()=>setCatalog(await api<Catalog>('/normatives')),[])
  useEffect(()=>{reload().catch(report); const timer=setInterval(()=>reload().catch(report),5000);return()=>clearInterval(timer)},[reload,report])
  async function refresh() {setBusy(true);try{await api('/normatives/refresh',{method:'POST'});await reload()}catch(e){report(e)}finally{setBusy(false)}}
  return <><div className="page-heading"><div className="eyebrow">FONTES PÚBLICAS RASTREÁVEIS</div><h1>Manuais operacionais B3</h1><p>Câmara e Central Depositária são sistemas distintos. Atualização verifica a página oficial, a capa do PDF e a vigência antes da indexação.</p><button className="primary" disabled={busy||catalog?.jobs.some(j=>['queued','running'].includes(j.status))} onClick={refresh}>Verificar e atualizar manuais públicos</button></div>{catalog?.jobs.slice(0,1).map(j=><div className="info-strip" key={j.id}>Atualização: {j.status}{j.error && <span className="danger-text"> · {j.error}</span>}</div>)}{catalog?.documents.map(m=><article className="source-panel manual-card" key={m.id}><h2>{m.title}</h2><p>{m.system} · {m.status} · Versão {m.version} · Vigência {m.effective_from}</p><p>{m.page_count} páginas · {m.chunk_count} trechos · Verificado em {new Date(m.verified_at).toLocaleString('pt-BR')}</p><a href={m.url} target="_blank" rel="noreferrer">PDF oficial</a><details><summary>SHA-256 e identificação</summary><code>{m.sha256}</code><p>{m.id}</p></details>{m.status==='active'&&<button className="text-button" onClick={async()=>{try{await api(`/normatives/${m.id}/deactivate`,{method:'POST'});await reload()}catch(e){report(e)}}}>Desativar da recuperação, preservando o documento</button>}</article>)}{catalog&&!catalog.documents.length&&<div className="empty-panel">Nenhum manual ingerido. Atualize as fontes públicas; falhas de acesso serão registradas.</div>}<form className="rag-search" onSubmit={async e=>{e.preventDefault();try{setChunks(await api<Chunk[]>(`/normatives/search?system=${system}&q=${encodeURIComponent(query)}`))}catch(error){report(error)}}}><select aria-label="Sistema normativo" value={system} onChange={e=>{setSystem(e.target.value);setChunks([])}}><option value="depositaria">Central Depositária</option><option value="camara">Câmara B3</option></select><input required minLength={3} maxLength={500} aria-label="Pesquisar normativos" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Tema ou procedimento"/><button className="primary small">Buscar no sistema selecionado</button></form>{chunks.map(c=><article className="chunk-card" key={c.id}><h3>{c.source_name}</h3><p>{c.text}</p><small>{c.system} · {c.location} · v{c.source_version}</small><code>{c.id}</code></article>)}</>
}
