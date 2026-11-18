/** Where the SpikeClip backend is, and how to prove we may use it.
 *
 *  Desktop (Electron): the engine runs on this PC at 127.0.0.1:8765 with no
 *  token, exactly as before — nothing here changes that.
 *
 *  Web (cloud): the frontend is a static site and the backend is a separate
 *  service. Its address comes from VITE_API_BASE at build time, and when the
 *  backend has SPIKECLIP_API_TOKEN set, the token is asked for once and kept
 *  in this browser. Ordinary requests carry it as a Bearer header; URLs used
 *  in <img>, <video>, <audio> and the WebSocket cannot send headers, so those
 *  carry it as `access_token` in the query (see backend/server/cloud.py).
 */

const env = (import.meta as unknown as { env?: Record<string, string | undefined> }).env ?? {}

export const API_BASE = (env.VITE_API_BASE || 'http://127.0.0.1:8765').replace(/\/+$/, '')

/** ws(s):// form of API_BASE. */
export const WS_BASE = API_BASE.replace(/^http/, 'ws')

const TOKEN_KEY = 'spikeclip.apiToken'

export function getApiToken(): string | null {
  try {
    return window.localStorage.getItem(TOKEN_KEY)
  } catch {
    return null // storage blocked (private mode, sandboxed frame): no token
  }
}

export function setApiToken(token: string | null): void {
  try {
    if (token) window.localStorage.setItem(TOKEN_KEY, token)
    else window.localStorage.removeItem(TOKEN_KEY)
  } catch {
    /* storage unavailable: the token lasts until the page is reloaded */
  }
}

/** `url` with the token in its query, for elements that cannot send headers. */
export function withToken(url: string): string {
  const token = getApiToken()
  if (!token) return url
  return `${url}${url.includes('?') ? '&' : '?'}access_token=${encodeURIComponent(token)}`
}

/** Add the Bearer header to every fetch addressed to the backend, so the
 *  many modules that call fetch(`${API_BASE}...`) need no changes. */
export function installAuthFetch(): void {
  const original = window.fetch.bind(window)
  window.fetch = (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url
    const token = getApiToken()
    if (!token || !url.startsWith(API_BASE)) return original(input, init)
    const headers = new Headers(init?.headers ?? (input instanceof Request ? input.headers : undefined))
    if (!headers.has('Authorization')) headers.set('Authorization', `Bearer ${token}`)
    return original(input, { ...init, headers })
  }
}

export type BackendAccess = 'ok' | 'needs-token' | 'unreachable'

/** Can this page use the backend as things stand? */
export async function checkBackendAccess(): Promise<BackendAccess> {
  try {
    const health = await fetch(`${API_BASE}/health`)
    if (!health.ok) return 'unreachable'
    const body = (await health.json()) as { auth?: boolean }
    if (!body.auth) return 'ok'
    const check = await fetch(`${API_BASE}/auth/check`)
    return check.ok ? 'ok' : 'needs-token'
  } catch {
    return 'unreachable'
  }
}
