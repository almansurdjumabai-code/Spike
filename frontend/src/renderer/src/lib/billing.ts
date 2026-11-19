import { API_BASE, getApiToken } from './backend'

/** Paid plans through Paddle (checkout overlay) — see backend/server/billing.py. */

export type PaidPlan = 'pro' | 'max'
export type Period = 'monthly' | 'yearly'

export interface BillingConfig {
  enabled: boolean
  environment: 'sandbox' | 'production'
  client_token: string
  prices: Record<string, string>
}

export interface MyPlan {
  plan: 'free' | 'pro' | 'max'
  status: string
  renews_at: string | null
  cancel_url: string | null
  update_url: string | null
  owner: boolean
}

interface PaddleGlobal {
  Environment: { set: (env: string) => void }
  Initialize: (o: { token: string }) => void
  Checkout: { open: (o: Record<string, unknown>) => void }
}
declare global {
  interface Window {
    Paddle?: PaddleGlobal
  }
}

const PENDING_KEY = 'spikeclip.pendingPlan'

export async function billingConfig(): Promise<BillingConfig | null> {
  try {
    const r = await fetch(`${API_BASE}/billing/config`)
    return r.ok ? ((await r.json()) as BillingConfig) : null
  } catch {
    return null
  }
}

export async function myPlan(): Promise<MyPlan | null> {
  try {
    const r = await fetch(`${API_BASE}/billing/me`)
    return r.ok ? ((await r.json()) as MyPlan) : null
  } catch {
    return null
  }
}

let ready: Promise<PaddleGlobal> | null = null

function loadPaddle(cfg: BillingConfig): Promise<PaddleGlobal> {
  if (ready) return ready
  ready = new Promise((resolve, reject) => {
    const done = (): void => {
      const P = window.Paddle
      if (!P) return reject(new Error('Paddle did not load'))
      if (cfg.environment === 'sandbox') P.Environment.set('sandbox')
      P.Initialize({ token: cfg.client_token })
      resolve(P)
    }
    if (window.Paddle) return done()
    const s = document.createElement('script')
    s.src = 'https://cdn.paddle.com/paddle/v2/paddle.js'
    s.async = true
    s.onload = done
    s.onerror = () => {
      ready = null
      reject(new Error('Could not reach Paddle. Check your connection or ad blocker.'))
    }
    document.head.appendChild(s)
  })
  return ready
}

/** Remember a plan picked before signing in; the studio opens checkout for it. */
export function setPendingPlan(plan: PaidPlan, period: Period): void {
  try {
    sessionStorage.setItem(PENDING_KEY, JSON.stringify({ plan, period }))
  } catch {
    /* storage blocked: the visitor picks the plan again from the studio */
  }
}

export function takePendingPlan(): { plan: PaidPlan; period: Period } | null {
  try {
    const raw = sessionStorage.getItem(PENDING_KEY)
    sessionStorage.removeItem(PENDING_KEY)
    return raw ? (JSON.parse(raw) as { plan: PaidPlan; period: Period }) : null
  } catch {
    return null
  }
}

/** Open Paddle's checkout for the signed-in user. */
export async function openCheckout(plan: PaidPlan, period: Period): Promise<void> {
  const cfg = await billingConfig()
  if (!cfg?.enabled) throw new Error('Payments are not switched on yet. Try again soon.')
  const priceId = cfg.prices[`${plan}_${period}`]
  const meRes = await fetch(`${API_BASE}/auth/me`)
  const me = meRes.ok ? ((await meRes.json()) as { user: { id: number; email: string } | null }).user : null
  if (!me || !getApiToken()) throw new Error('Sign in first.')
  const Paddle = await loadPaddle(cfg)
  Paddle.Checkout.open({
    items: [{ priceId, quantity: 1 }],
    customer: { email: me.email },
    customData: { user_id: me.id },
    settings: {
      displayMode: 'overlay',
      theme: 'dark',
      successUrl: `${window.location.origin}/app?upgraded=${plan}`
    }
  })
}
