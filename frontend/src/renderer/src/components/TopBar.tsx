import { useEffect, useRef, useState } from 'react'
import { API_BASE, logout, type SpikeUser } from '../lib/backend'
import { myPlan, openCheckout, takePendingPlan, type MyPlan } from '../lib/billing'
import { t } from '../lib/i18n'

const PLAN_LABEL: Record<MyPlan['plan'], string> = { free: 'Free', pro: 'Pro', max: 'Max' }

/** Web build: greeting, plan badge, upgrade, and the account menu. */
export default function TopBar(): JSX.Element {
  const [user, setUser] = useState<SpikeUser | null>(null)
  const [plan, setPlan] = useState<MyPlan | null>(null)
  const [open, setOpen] = useState(false)
  const [toast, setToast] = useState<string | null>(null)
  const menu = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetch(`${API_BASE}/auth/me`)
      .then((r) => (r.ok ? r.json() : { user: null }))
      .then((d: { user: SpikeUser | null }) => setUser(d.user))
      .catch(() => setUser(null))
    void myPlan().then(setPlan)

    // A plan picked on the website before signing up: open its checkout now.
    const pending = takePendingPlan()
    if (pending) openCheckout(pending.plan, pending.period).catch((e: Error) => setToast(e.message))

    // Back from a successful checkout: Paddle's webhook can take a few
    // seconds, so ask again until the new plan shows.
    const upgraded = new URLSearchParams(window.location.search).get('upgraded')
    if (upgraded) {
      setToast(`🎉 ${t('Welcome to')} ${upgraded === 'max' ? 'Max' : 'Pro'}!`)
      window.history.replaceState(null, '', window.location.pathname)
      let tries = 0
      const id = setInterval(() => {
        tries += 1
        void myPlan().then((p) => {
          if (p) setPlan(p)
          if ((p && p.plan !== 'free') || tries > 10) clearInterval(id)
        })
      }, 3000)
      return () => clearInterval(id)
    }
    return undefined
  }, [])

  useEffect(() => {
    if (!toast) return
    const id = setTimeout(() => setToast(null), 6000)
    return () => clearTimeout(id)
  }, [toast])

  useEffect(() => {
    if (!open) return
    const close = (e: MouseEvent): void => {
      if (menu.current && !menu.current.contains(e.target as Node)) setOpen(false)
    }
    window.addEventListener('mousedown', close)
    return () => window.removeEventListener('mousedown', close)
  }, [open])

  const name = user?.name || t('Owner')
  const initials = name
    .split(/\s+/)
    .map((w) => w[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
  const hour = new Date().getHours()
  const wave = hour < 5 ? '🌙' : hour < 12 ? '☀️' : hour < 18 ? '👋' : '🌆'
  const today = new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })
  const tier = plan?.plan ?? 'free'
  const isOwner = plan?.owner ?? !user

  return (
    <header className="vc-topbar">
      <div className="min-w-0">
        <p className="vc-topbar-hi">
          {t('Hey')}, <span className="vc-topbar-name">{name.split(' ')[0]}</span> {wave}
        </p>
        <p className="vc-topbar-date">{today}</p>
      </div>
      <div className="flex items-center gap-3">
        {!isOwner && tier !== 'max' && (
          <a className="btn-accent !py-1.5 !px-3.5 text-sm" href="/#pricing">
            ⚡ {t('Upgrade')}
          </a>
        )}
        {isOwner ? (
          <span className="vc-pill-badge">
            <span className="vc-pill-dot" />
            {t('Owner')}
          </span>
        ) : (
          <span className={`vc-plan-badge is-${tier}`} title={plan?.renews_at ? `${t('Renews')} ${plan.renews_at}` : undefined}>
            {tier === 'max' ? '🚁' : tier === 'pro' ? '🏎️' : '🌴'} {PLAN_LABEL[tier]}
          </span>
        )}
        <div className="relative" ref={menu}>
          <button className="vc-avatar-btn" onClick={() => setOpen((o) => !o)} aria-haspopup="menu" aria-expanded={open}>
            <span className="vc-avatar-circle">{initials || '⚡'}</span>
            <span className="vc-avatar-caret" aria-hidden>
              ▾
            </span>
          </button>
          {open && (
            <div className="vc-menu" role="menu">
              <div className="vc-menu-head">
                <span className="vc-avatar-circle lg">{initials || '⚡'}</span>
                <div className="min-w-0">
                  <p className="font-bold truncate">{name}</p>
                  <p className="text-xs text-muted truncate">{user?.email ?? t('Signed in with the access token')}</p>
                  {!isOwner && (
                    <p className="text-xs mt-1">
                      <span className={`vc-plan-badge sm is-${tier}`}>{PLAN_LABEL[tier]}</span>
                      {plan?.renews_at && (
                        <span className="text-muted ml-1.5">
                          {t('Renews')} {plan.renews_at}
                        </span>
                      )}
                    </p>
                  )}
                </div>
              </div>
              {!isOwner && tier !== 'max' && (
                <button className="vc-menu-item" role="menuitem" onClick={() => window.location.assign('/#pricing')}>
                  ⚡ {t('Upgrade plan')}
                </button>
              )}
              {plan?.update_url && (
                <a className="vc-menu-item block" role="menuitem" href={plan.update_url} target="_blank" rel="noreferrer">
                  💳 {t('Update payment method')}
                </a>
              )}
              {plan?.cancel_url && (
                <a className="vc-menu-item block" role="menuitem" href={plan.cancel_url} target="_blank" rel="noreferrer">
                  ✖ {t('Cancel subscription')}
                </a>
              )}
              <button className="vc-menu-item" role="menuitem" onClick={() => window.location.assign('/')}>
                🌴 {t('SpikeClip website')}
              </button>
              <button
                className="vc-menu-item danger"
                role="menuitem"
                onClick={() => void logout().then(() => window.location.assign('/'))}
              >
                🚪 {t('Log out')}
              </button>
            </div>
          )}
        </div>
      </div>
      {toast && (
        <div className="vc-toast" role="status" onClick={() => setToast(null)}>
          {toast}
        </div>
      )}
    </header>
  )
}
