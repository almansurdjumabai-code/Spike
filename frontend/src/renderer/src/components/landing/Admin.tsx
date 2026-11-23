import '@fontsource/anton/400.css'
import '@fontsource/alfa-slab-one/400.css'
import '@fontsource-variable/inter'
import './landing.css'
import './landing-extra.css'
import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { admin, type AdminLicense, type AdminStats, type AdminUser } from '../../lib/admin'
import { getApiToken, setApiToken } from '../../lib/backend'

/** /admin: the owner's dashboard — sales, keys, people. GTA 6 style. */

function Stat({ label, value, cash = false, sub }: { label: string; value: string | number; cash?: boolean; sub?: string }): JSX.Element {
  return (
    <div className="vc-glass vc-adm-stat">
      <span className="vc-adm-label">{label}</span>
      <b className={cash ? 'vc-cash vc-adm-cash' : 'vc-adm-num'}>{value}</b>
      {sub && <span className="vc-note">{sub}</span>}
    </div>
  )
}

function Wanted({ level }: { level: number }): JSX.Element {
  // GTA-style stars for how hot sales are this week.
  return (
    <span className="vc-wanted" title="New sign-ups this week">
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i} className={i <= level ? 'on' : ''}>
          ★
        </span>
      ))}
    </span>
  )
}

export default function Admin(): JSX.Element {
  const [authed, setAuthed] = useState<boolean | null>(null)
  const [token, setToken] = useState('')
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [keys, setKeys] = useState<AdminLicense[]>([])
  const [users, setUsers] = useState<AdminUser[]>([])
  const [tab, setTab] = useState<'keys' | 'users'>('keys')
  const [error, setError] = useState<string | null>(null)
  const [issued, setIssued] = useState<string | null>(null)
  const [form, setForm] = useState({ plan: 'pro', email: '', days: '30', note: '' })

  const load = useCallback(async () => {
    try {
      const [s, k, u] = await Promise.all([admin.stats(), admin.licenses(), admin.users()])
      setStats(s)
      setKeys(k)
      setUsers(u)
      setAuthed(true)
    } catch (e) {
      setAuthed(false)
      if (getApiToken()) setError(e instanceof Error ? e.message : String(e))
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const signIn = (e: FormEvent): void => {
    e.preventDefault()
    setApiToken(token.trim())
    setError(null)
    void load()
  }

  const issue = async (e: FormEvent): Promise<void> => {
    e.preventDefault()
    setError(null)
    try {
      const lic = await admin.issue(form.plan, form.email.trim(), form.days ? Number(form.days) : null, form.note)
      setIssued(lic.key)
      void load()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    }
  }

  const revoke = async (key: string): Promise<void> => {
    if (!window.confirm(`Revoke ${key}? The app will stop working for this key.`)) return
    try {
      await admin.revoke(key)
      void load()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    }
  }

  const wanted = Math.min(5, Math.ceil((stats?.users_last_7_days ?? 0) / 2))

  return (
    <div className="vc">
      <nav className="vc-nav is-scrolled">
        <a className="vc-logo" translate="no" href="/">
          <span className="vc-logo-mark">⚡</span>
          <span>
            Spike<span className="vc-gradient-text">Clip</span>
          </span>
        </a>
        <div className="vc-nav-links">
          <span style={{ color: '#ffd56b' }}>👑 Owner HQ</span>
        </div>
        {authed && (
          <button
            className="vc-btn vc-btn-glass vc-btn-sm"
            onClick={() => {
              setApiToken(null)
              window.location.assign('/')
            }}
          >
            Log out
          </button>
        )}
      </nav>

      <main className="vc-section vc-account" style={{ maxWidth: 1180 }}>
        <div className="vc-kicker">Owner HQ</div>
        <h1 className="vc-display vc-h2">
          The <span className="vc-gradient-text">heist board</span>
        </h1>

        {authed === null && <p className="vc-note">Loading…</p>}

        {authed === false && (
          <form className="vc-glass vc-key-card" style={{ maxWidth: 520 }} onSubmit={signIn}>
            <p className="font-bold" style={{ fontSize: 18 }}>
              Owner sign-in
            </p>
            <p className="vc-note" style={{ marginTop: 6 }}>
              Paste the owner token (ADMIN_TOKEN or SPIKECLIP_API_TOKEN on Render).
            </p>
            <label className="vc-field" style={{ marginTop: 16 }}>
              <span>Owner token</span>
              <input type="password" value={token} onChange={(e) => setToken(e.target.value)} autoFocus />
            </label>
            {error && <div className="vc-error">{error}</div>}
            <button className="vc-btn vc-btn-primary" type="submit" disabled={!token.trim()}>
              Enter HQ →
            </button>
          </form>
        )}

        {authed && stats && (
          <>
            <div className="vc-adm-stats">
              <Stat label="Monthly revenue" value={`$${stats.mrr_usd.toLocaleString('en-US')}`} cash sub="from active subscriptions" />
              <Stat label="Paying customers" value={stats.paid_active} sub={`Pro ${stats.by_plan.pro ?? 0} · Max ${stats.by_plan.max ?? 0}`} />
              <Stat label="Active keys" value={stats.licenses_active} sub={`${stats.licenses_total} issued in total`} />
              <div className="vc-glass vc-adm-stat">
                <span className="vc-adm-label">Accounts</span>
                <b className="vc-adm-num">{stats.users}</b>
                <span className="vc-note">
                  +{stats.users_last_7_days} this week <Wanted level={wanted} />
                </span>
              </div>
            </div>

            <div className="vc-adm-grid">
              <form className="vc-glass vc-key-card" onSubmit={(e) => void issue(e)}>
                <p className="font-bold" style={{ fontSize: 18 }}>
                  🔑 Issue a key
                </p>
                <p className="vc-note" style={{ marginTop: 4 }}>
                  For testers, giveaways or a payment provider&apos;s reviewer.
                </p>
                <div className="vc-adm-form">
                  <label className="vc-field">
                    <span>Plan</span>
                    <select value={form.plan} onChange={(e) => setForm({ ...form, plan: e.target.value })}>
                      <option value="pro">Pro</option>
                      <option value="max">Max</option>
                    </select>
                  </label>
                  <label className="vc-field">
                    <span>Days (empty = forever)</span>
                    <input value={form.days} inputMode="numeric" onChange={(e) => setForm({ ...form, days: e.target.value.replace(/\D/g, '') })} />
                  </label>
                </div>
                <label className="vc-field">
                  <span>Email (links it to their account)</span>
                  <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
                </label>
                <label className="vc-field">
                  <span>Note</span>
                  <input value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} />
                </label>
                <button className="vc-btn vc-btn-primary" type="submit">
                  Issue key →
                </button>
                {issued && (
                  <div className="vc-success" style={{ marginTop: 14 }}>
                    New key: <code translate="no">{issued}</code>
                  </div>
                )}
              </form>

              <div className="vc-glass vc-key-card vc-adm-table-card">
                <div className="vc-tabs" style={{ margin: '0 0 16px', maxWidth: 300 }}>
                  <button className={tab === 'keys' ? 'on' : ''} onClick={() => setTab('keys')}>
                    Keys ({keys.length})
                  </button>
                  <button className={tab === 'users' ? 'on' : ''} onClick={() => setTab('users')}>
                    People ({users.length})
                  </button>
                </div>
                {error && <div className="vc-error">{error}</div>}
                <div className="vc-adm-table-wrap">
                  {tab === 'keys' ? (
                    <table className="vc-adm-table">
                      <thead>
                        <tr>
                          <th>Key</th>
                          <th>Plan</th>
                          <th>Status</th>
                          <th>PCs</th>
                          <th>Email</th>
                          <th />
                        </tr>
                      </thead>
                      <tbody>
                        {keys.map((k) => (
                          <tr key={k.key}>
                            <td>
                              <code translate="no">{k.key}</code>
                            </td>
                            <td>{k.plan_label}</td>
                            <td>
                              <span className={`vc-key-state is-${k.state}`}>{k.state}</span>
                            </td>
                            <td>
                              {k.activations_used}/{k.max_activations}
                            </td>
                            <td className="vc-note">{k.email ?? '—'}</td>
                            <td>
                              {k.state !== 'revoked' && (
                                <button className="vc-link" onClick={() => void revoke(k.key)}>
                                  Revoke
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                        {keys.length === 0 && (
                          <tr>
                            <td colSpan={6} className="vc-note">
                              No keys yet. The first sale will show up here.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  ) : (
                    <table className="vc-adm-table">
                      <thead>
                        <tr>
                          <th>Name</th>
                          <th>Email</th>
                          <th>Plan</th>
                          <th>Joined</th>
                        </tr>
                      </thead>
                      <tbody>
                        {users.map((u) => (
                          <tr key={u.id}>
                            <td>{u.name}</td>
                            <td className="vc-note">{u.email}</td>
                            <td>{u.plan}</td>
                            <td className="vc-note">{u.created_at?.slice(0, 10)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
