import assert from 'node:assert/strict'
import { test } from 'node:test'

globalThis.sessionStorage = { getItem: () => null, setItem: () => {} }
const { api } = await import('../src/api.ts')

test('a failed event read is actionable and a new attempt can recover', async t => {
  let calls = 0
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(url, '/api/events/fictitious-event')
    assert.equal(options.headers.get('X-SimplFAQ'), 'local-poc')
    calls++
    if (calls === 1) throw new TypeError('Failed to fetch')
    return Response.json({ id: 'fictitious-event', result: { items: [] } })
  })
  await assert.rejects(api('/events/fictitious-event'), /Verifique se o SimpliFAQ está em execução/)
  assert.equal((await api('/events/fictitious-event')).id, 'fictitious-event')
  assert.equal(calls, 2)
})

test('failed writes are never automatically resent', async t => {
  let calls = 0
  t.mock.method(globalThis, 'fetch', async () => { calls++; throw new TypeError('Failed to fetch') })
  await assert.rejects(api('/events', { method: 'POST', body: '{}' }), /Não foi possível conectar/)
  assert.equal(calls, 1)
})

test('a proxy HTML error is translated without exposing the HTML', async t => {
  t.mock.method(globalThis, 'fetch', async () => new Response('<h1>Bad Gateway</h1>', { status: 502 }))
  await assert.rejects(api('/events/fictitious-event'), /Não foi possível acessar o servidor/)
})

test('HTTP application errors and explicit cancellation are preserved', async t => {
  t.mock.method(globalThis, 'fetch', async () => Response.json({ detail: 'Evento não encontrado' }, { status: 404 }))
  await assert.rejects(api('/events/fictitious-event'), /Evento não encontrado/)
  t.mock.method(globalThis, 'fetch', async () => { throw new DOMException('Cancelled', 'AbortError') })
  await assert.rejects(api('/events/fictitious-event'), { name: 'AbortError' })
})
