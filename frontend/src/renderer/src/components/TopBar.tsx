import { useEffect, useRef, useState } from 'react'
import { API_BASE, logout, type SpikeUser } from '../lib/backend'
import { t } from '../lib/i18n'

/** Web build: a greeting, the early-access badge and the account menu. */
export default function TopBar(): JSX.Element {
  const [user, setUser] = useState<SpikeUser | null>(null)
  const [open, setOpen] = useState(false)
  const menu = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetch(`${API_BASE}/auth/me`)
      .then((r) => (r.ok ? r.json() : { user: null }))
      .then((d: { user: SpikeUser | null }) => setUser(d.user))
      .catch(() => setUser(null))
  }, [])

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

  return (
    <header className="vc-topbar">
      <div className="min-w-0">
        <p className="vc-topbar-hi">
          {t('Hey')}, <span className="vc-topbar-name">{name.split(' ')[0]}</span> {wave}
        </p>
        <p className="vc-topbar-date">{today}</p>
      </div>
      <div className="flex items-center gap-3">
        <span className="vc-pill-badge" title={t('You are using an early version of SpikeClip')}>
          <span className="vc-pill-dot" />
          {t('Early access')}
        </span>
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
                </div>
              </div>
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
    </header>
  )
}
