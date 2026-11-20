import { API_BASE } from './backend'

/** Owner endpoints of the license API (backend/app/main.py, /admin/*). */

export interface AdminStats {
  users: number
  users_last_7_days: number
  licenses_total: number
  licenses_active: number
  paid_active: number
  by_plan: Record<string, number>
  activations: number
  mrr_usd: number
}

export interface AdminLicense {
  key: string
  plan: string
  plan_label: string
  status: string
  state: string
  expires_at: string | null
  max_activations: number
  activations_used: number
  email: string | null
  source: string
}

export interface AdminUser {
  id: number
  email: string
  name: string
  created_at: string | null
  plan: string
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) }
  })
  const data = (await r.json().catch(() => ({}))) as { detail?: string }
  if (!r.ok) throw new Error(r.status === 401 ? 'Owner token required.' : data.detail || `Request failed (${r.status}).`)
  return data as T
}

export const admin = {
  stats: () => call<AdminStats>('/admin/stats'),
  licenses: () => call<{ licenses: AdminLicense[] }>('/admin/licenses?limit=200').then((d) => d.licenses),
  users: () => call<{ users: AdminUser[] }>('/admin/users?limit=200').then((d) => d.users),
  issue: (plan: string, email: string, days: number | null, note: string) =>
    call<AdminLicense>('/admin/licenses', {
      method: 'POST',
      body: JSON.stringify({ plan, email: email || null, days, note: note || null })
    }),
  revoke: (key: string) => call<AdminLicense>(`/admin/licenses/${encodeURIComponent(key)}/revoke`, { method: 'POST' })
}
