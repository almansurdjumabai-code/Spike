import { API_BASE } from './backend'

/** The account page's view of the licence API (api/app/main.py). */

export interface Device {
  device: string
  name: string | null
  platform: string | null
  app_version: string | null
  first_seen: string | null
  last_seen: string | null
}

export interface License {
  key: string
  plan: 'pro' | 'max'
  plan_label: string
  status: string
  state: 'ok' | 'expired' | 'inactive' | 'revoked'
  expires_at: string | null
  max_activations: number
  activations_used: number
  devices: Device[]
  manage: { cancel_url: string | null; update_url: string | null }
}

export interface Downloads {
  version: string
  windows: string | null
  mac: string | null
}

export async function myLicenses(): Promise<License[]> {
  const r = await fetch(`${API_BASE}/licenses/me`)
  if (!r.ok) throw new Error(r.status === 401 ? 'Log in first.' : `Could not load your licenses (${r.status}).`)
  return ((await r.json()) as { licenses: License[] }).licenses
}

export async function releaseDevice(key: string, device: string): Promise<void> {
  const r = await fetch(`${API_BASE}/licenses/${encodeURIComponent(key)}/devices/${encodeURIComponent(device)}`, {
    method: 'DELETE'
  })
  if (!r.ok) throw new Error('Could not release that device. Try again.')
}

export async function downloads(): Promise<Downloads> {
  try {
    const r = await fetch(`${API_BASE}/downloads`)
    if (r.ok) return (await r.json()) as Downloads
  } catch {
    /* fall through */
  }
  return { version: '', windows: null, mac: null }
}
