import type { PublicClientApplication } from '@azure/msal-browser'
import type { Config } from './types'

let token = sessionStorage.getItem('simplfaq-token') || ''
let msal: PublicClientApplication | null = null
let authConfig: Config | null = null

export async function login(config: Config) {
  authConfig = config
  if (!msal) {
    const { PublicClientApplication } = await import('@azure/msal-browser')
    msal = new PublicClientApplication({ auth: { clientId: config.client_id, authority: `https://login.microsoftonline.com/${config.tenant_id}`, redirectUri: window.location.origin }, cache: { cacheLocation: 'sessionStorage' } })
    await msal.initialize()
  }
  const result = await msal.loginPopup({ scopes: [config.scope] })
  token = result.accessToken
}
export function setToken(value: string) { token = value; sessionStorage.setItem('simplfaq-token', value) }

export async function request(path: string, options: RequestInit = {}) {
  if (msal && authConfig) {
    const account = msal.getAllAccounts()[0]
    if (account) {
      const result = await msal.acquireTokenSilent({ scopes: [authConfig.scope], account })
      token = result.accessToken
    }
  }
  const headers = new Headers(options.headers)
  headers.set('X-SimplFAQ', 'local-poc')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  let response: Response
  try {
    response = await fetch('/api' + path, { ...options, headers })
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') throw error
    throw new Error('Não foi possível conectar ao servidor. Verifique se o SimpliFAQ está em execução e tente novamente.')
  }
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Não foi possível acessar o servidor' }))
    throw new Error(typeof error.detail === 'string' ? error.detail : 'Confira os campos informados e tente novamente.')
  }
  return response
}
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> { return (await request(path, options)).json() }
export async function download(path: string, name: string) {
  const blob = await (await request(path)).blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a'); link.href = url; link.download = name; link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
