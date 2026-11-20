import '@fontsource/anton/400.css'
import '@fontsource-variable/inter'
import './landing.css'
import './landing-extra.css'
import { useCallback, useEffect, useState } from 'react'
import { API_BASE, getApiToken, logout, type SpikeUser } from '../../lib/backend'
import { openCheckout, takePendingPlan, type Period } from '../../lib/billing'
import { downloadLink, downloads, myLicenses, releaseDevice, type Downloads, type License } from '../../lib/licenses'
import AuthModal from './AuthModal'

/** /app on the website: the buyer's license key, downloads and setup steps.
 *  The clipping itself happens in the desktop app on their PC. */

const STATE_LABEL: Record<License['state'], string> = {
  ok: 'Active',
  expired: 'Expired',
  inactive: 'Paused / cancelled',
  revoked: 'Revoked'
}

function KeyCard({ lic, onChange }: { lic: License; onChange: () => void }): JSX.Element {
  const [copied, setCopied] = useState(false)
  const [busy, setBusy] = useState<string | null>(null)
  const copy = (): void => {
    void navigator.clipboard?.writeText(lic.key).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1800)
    })
  }
  const release = async (device: string): Promise<void> => {
    setBusy(device)
    try {
      await releaseDevice(lic.key, device)
      onChange()
    } finally {
      setBusy(null)
    }
  }
  return (
    <div className={`vc-glass vc-key-card is-${lic.plan}`}>
      <div className="vc-key-top">
        <span className={`vc-key-plan is-${lic.plan}`}>{lic.plan === 'max' ? '🚁' : '🏎️'} {lic.plan_label}</span>
        <span className={`vc-key-state is-${lic.state}`}>{STATE_LABEL[lic.state]}</span>
      </div>
      <p className="vc-note" style={{ marginTop: 18 }}>Your license key</p>
      <div className="vc-key-row">
        <code className="vc-key" translate="no">
          {lic.key}
        </code>
        <button className="vc-btn vc-btn-primary vc-btn-sm" onClick={copy}>
          {copied ? '✓ Copied' : '📋 Copy'}
        </button>
      </div>
      <div className="vc-key-meta">
        <span>
          💻 {lic.activations_used} / {lic.max_activations} computers
        </span>
        {lic.expires_at && (
          <span>
            {lic.state === 'ok' ? '🔁 Renews' : '⏳ Ended'} {lic.expires_at.slice(0, 10)}
          </span>
        )}
      </div>
      {lic.devices.length > 0 && (
        <ul className="vc-devices">
          {lic.devices.map((d) => (
            <li key={d.device}>
              <span>
                {d.platform === 'macos' ? '🍎' : '⊞'} <b>{d.name || 'Computer'}</b>
                <em>last seen {d.last_seen?.slice(0, 10) ?? '—'}</em>
              </span>
              <button className="vc-link" disabled={busy === d.device} onClick={() => void release(d.device)}>
                {busy === d.device ? 'Releasing…' : 'Release'}
              </button>
            </li>
          ))}
        </ul>
      )}
      {(lic.manage.update_url || lic.manage.cancel_url) && (
        <div className="vc-key-manage">
          {lic.manage.update_url && (
            <a className="vc-link" href={lic.manage.update_url} target="_blank" rel="noreferrer">
              💳 Update payment method
            </a>
          )}
          {lic.manage.cancel_url && (
            <a className="vc-link" href={lic.manage.cancel_url} target="_blank" rel="noreferrer">
              ✖ Cancel subscription
            </a>
          )}
        </div>
      )}
    </div>
  )
}

function Setup({ dl }: { dl: Downloads }): JSX.Element {
  const [os, setOs] = useState<'windows' | 'mac'>(navigator.userAgent.includes('Mac') ? 'mac' : 'windows')
  const steps =
    os === 'windows'
      ? [
          'Download the Windows installer above and run it.',
          'If Windows SmartScreen appears, click “More info” → “Run anyway”.',
          'Open SpikeClip from the Start menu. First launch sets up the AI models (a few minutes).',
          'Go to Settings → License, paste your key and press Activate.',
          'Paste a stream link, let it find the chat peaks, and your 9:16 clips appear in the library.'
        ]
      : [
          'Download the macOS build above and open the .dmg file.',
          'Drag SpikeClip into Applications.',
          'First launch: right-click SpikeClip → Open, then confirm (macOS asks once for apps from the internet).',
          'Go to Settings → License, paste your key and press Activate.',
          'Paste a stream link, let it find the chat peaks, and your 9:16 clips appear in the library.'
        ]
  return (
    <div className="vc-glass vc-setup">
      <div className="vc-tabs" style={{ margin: '0 0 18px', maxWidth: 320 }}>
        <button className={os === 'windows' ? 'on' : ''} onClick={() => setOs('windows')}>
          ⊞ Windows
        </button>
        <button className={os === 'mac' ? 'on' : ''} onClick={() => setOs('mac')}>
          🍎 macOS
        </button>
      </div>
      <ol className="vc-setup-steps">
        {steps.map((s, i) => (
          <li key={i}>
            <span>{i + 1}</span>
            {s}
          </li>
        ))}
      </ol>
      <p className="vc-note" style={{ marginTop: 14 }}>
        Needs {os === 'windows' ? 'Windows 10/11 (64-bit)' : 'macOS 12 or newer'}, 8 GB RAM (16 GB recommended).
        Everything runs on your computer: nothing is uploaded to our servers.{dl.version ? ` Current version: ${dl.version}.` : ''}
      </p>
    </div>
  )
}

export default function Account(): JSX.Element {
  const [user, setUser] = useState<SpikeUser | null | undefined>(undefined)
  const [lics, setLics] = useState<License[] | null>(null)
  const [dl, setDl] = useState<Downloads>({ version: '', windows: false, mac: false })
  const [error, setError] = useState<string | null>(null)
  const purchased = new URLSearchParams(window.location.search).get('upgraded')

  const load = useCallback(async () => {
    if (!getApiToken()) return setUser(null)
    try {
      const r = await fetch(`${API_BASE}/auth/me`)
      const me = r.ok ? ((await r.json()) as { user: SpikeUser | null }).user : null
      setUser(me)
      if (me) setLics(await myLicenses())
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
      setUser(null)
    }
  }, [])

  useEffect(() => {
    void load()
    void downloads().then(setDl)
  }, [load])

  // A plan picked on the website before signing up: open its checkout now.
  useEffect(() => {
    if (!user) return
    const pending = takePendingPlan()
    if (pending) openCheckout(pending.plan, pending.period).catch((e: Error) => setError(e.message))
  }, [user])

  // Back from checkout: the key appears once Paddle's webhook arrives.
  useEffect(() => {
    if (!purchased || !user || (lics && lics.length > 0)) return
    let tries = 0
    const id = setInterval(() => {
      tries += 1
      void myLicenses()
        .then(setLics)
        .catch(() => undefined)
      if (tries > 20) clearInterval(id)
    }, 3000)
    return () => clearInterval(id)
  }, [purchased, user, lics])

  const buy = (period: Period): void => {
    openCheckout('pro', period).catch((e: Error) => setError(e.message))
  }

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
          <a href="/#how">How it works</a>
          <a href="/#pricing">Pricing</a>
          <a href="/#faq">FAQ</a>
        </div>
        {user ? (
          <button className="vc-btn vc-btn-glass vc-btn-sm" onClick={() => void logout().then(() => window.location.assign('/'))}>
            Log out
          </button>
        ) : (
          <a className="vc-btn vc-btn-glass vc-btn-sm" href="/">
            ← Website
          </a>
        )}
      </nav>

      <main className="vc-section vc-account">
        {user === undefined ? (
          <p className="vc-note">Loading…</p>
        ) : user === null ? (
          <>
            <div className="vc-kicker">Your account</div>
            <h1 className="vc-display vc-h2">
              Log in to get <span className="vc-gradient-text">your key</span>
            </h1>
            <p className="vc-lead">Your license key, the desktop downloads and setup steps live here.</p>
            <AuthModal initial="login" onClose={() => window.location.assign('/')} onDone={() => void load()} />
          </>
        ) : (
          <>
            <div className="vc-kicker">Your account</div>
            <h1 className="vc-display vc-h2">
              Hey, <span className="vc-gradient-text">{user.name.split(' ')[0]}</span>
            </h1>
            {purchased && (
              <div className="vc-success">
                🎉 Payment received — welcome to {purchased === 'max' ? 'Max' : 'Pro'}!{' '}
                {lics && lics.length > 0 ? 'Your key is below.' : 'Your key will appear here in a few seconds…'}
              </div>
            )}
            {error && (
              <div className="vc-error" onClick={() => setError(null)}>
                {error}
              </div>
            )}

            <h2 className="vc-account-h">🔑 License</h2>
            {lics === null ? (
              <p className="vc-note">Loading your licenses…</p>
            ) : lics.length === 0 ? (
              <div className="vc-glass vc-key-card">
                <p className="font-bold" style={{ fontSize: 18 }}>
                  No license yet
                </p>
                <p className="vc-note" style={{ marginTop: 6 }}>
                  SpikeClip needs a license key to run. Pro unlocks unlimited clips in 1080p with no watermark on your
                  computer. The download and your personal key appear here right after payment.
                </p>
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 16 }}>
                  <button className="vc-btn vc-btn-primary" onClick={() => buy('monthly')}>
                    Go Pro — $14/month
                  </button>
                  <button className="vc-btn vc-btn-glass" onClick={() => buy('yearly')}>
                    $132/year (save 20%)
                  </button>
                </div>
              </div>
            ) : (
              <div className="vc-keys">
                {lics.map((l) => (
                  <KeyCard key={l.key} lic={l} onChange={() => void load()} />
                ))}
              </div>
            )}

            <h2 className="vc-account-h">⬇ Download the app</h2>
            <div className="vc-downloads">
              {(['windows', 'mac'] as const).map((os) => {
                const ready = dl[os]
                const licensed = !!lics?.some((l) => l.state === 'ok')
                return (
                  <button
                    key={os}
                    className={`vc-dl${ready && licensed ? '' : ' is-soon'}`}
                    disabled={!ready || !licensed}
                    onClick={() =>
                      void downloadLink(os)
                        .then((url) => window.location.assign(url))
                        .catch((e: Error) => setError(e.message))
                    }
                  >
                    <span className="vc-dl-ico">{os === 'windows' ? '⊞' : '🍎'}</span>
                    <span>
                      <b>{os === 'windows' ? 'Windows' : 'macOS'}</b>
                      <em>
                        {!ready
                          ? 'Coming soon'
                          : !licensed
                            ? '🔒 For subscribers'
                            : `${os === 'windows' ? 'Installer' : '.dmg'}${dl.version ? ` · v${dl.version}` : ''}`}
                      </em>
                    </span>
                  </button>
                )
              })}
            </div>

            <h2 className="vc-account-h">🛠 Install &amp; activate</h2>
            <Setup dl={dl} />
          </>
        )}
      </main>
    </div>
  )
}
