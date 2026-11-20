import { useEffect, useState, type FormEvent } from 'react'
import { checkBackendAccess, login, register, setApiToken, signupMode, type SignupMode } from '../../lib/backend'

export type AuthTab = 'signup' | 'login'

/** Sign up / log in. On success the session token is stored and onDone runs. */
export default function AuthModal({
  initial,
  onClose,
  onDone
}: {
  initial: AuthTab
  onClose: () => void
  onDone: () => void
}): JSX.Element {
  const [tab, setTab] = useState<AuthTab>(initial)
  const [mode, setMode] = useState<SignupMode | null>(null)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [invite, setInvite] = useState('')
  const [adminToken, setAdminToken] = useState('')
  const [useAdmin, setUseAdmin] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    void signupMode().then(setMode)
  }, [])

  useEffect(() => {
    const onKey = (e: KeyboardEvent): void => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const submit = async (e: FormEvent): Promise<void> => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      if (useAdmin) {
        setApiToken(adminToken.trim())
        if ((await checkBackendAccess()) !== 'ok') {
          setApiToken(null)
          throw new Error('That access token was not accepted.')
        }
      } else if (tab === 'signup') {
        await register({ name, email, password, invite })
      } else {
        await login(email, password)
      }
      onDone()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setBusy(false)
    }
  }

  const signupClosed = tab === 'signup' && mode === 'closed' && !useAdmin

  return (
    <div className="vc-modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="vc-modal" role="dialog" aria-modal="true" aria-labelledby="vc-auth-title">
        <button className="vc-close" onClick={onClose} aria-label="Close">
          ×
        </button>
        <div className="vc-logo" translate="no">
          <span className="vc-logo-mark">⚡</span>
          <span>
            Spike<span className="vc-gradient-text">Clip</span>
          </span>
        </div>
        <h2 id="vc-auth-title" className="vc-display" style={{ fontSize: 40, marginTop: 18 }}>
          {useAdmin ? 'Owner access' : tab === 'signup' ? 'Join the crew' : 'Welcome back'}
        </h2>
        <p className="vc-note" style={{ marginTop: 6 }}>
          {useAdmin
            ? 'Paste the SPIKECLIP_API_TOKEN from your server.'
            : tab === 'signup'
              ? 'Create your account and start turning streams into clips.'
              : 'Log in to get your license key and downloads.'}
        </p>

        {!useAdmin && (
          <div className="vc-tabs" role="tablist">
            <button type="button" className={tab === 'signup' ? 'on' : ''} onClick={() => setTab('signup')}>
              Sign up
            </button>
            <button type="button" className={tab === 'login' ? 'on' : ''} onClick={() => setTab('login')}>
              Log in
            </button>
          </div>
        )}

        {signupClosed ? (
          <div className="vc-error" style={{ marginTop: 20 }}>
            Sign-up is invite-only and not open yet. Already have an account? <span className="vc-link" onClick={() => setTab('login')}>Log in</span>.
          </div>
        ) : (
          <form onSubmit={(e) => void submit(e)} style={{ marginTop: useAdmin ? 20 : 0 }}>
            {useAdmin ? (
              <label className="vc-field">
                <span>Access token</span>
                <input type="password" value={adminToken} onChange={(e) => setAdminToken(e.target.value)} autoFocus />
              </label>
            ) : (
              <>
                {tab === 'signup' && (
                  <label className="vc-field">
                    <span>Creator name</span>
                    <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. NovaRush" autoComplete="nickname" />
                  </label>
                )}
                <label className="vc-field">
                  <span>Email</span>
                  <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" autoFocus />
                </label>
                <label className="vc-field">
                  <span>Password</span>
                  <input
                    type="password"
                    required
                    minLength={tab === 'signup' ? 8 : undefined}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete={tab === 'signup' ? 'new-password' : 'current-password'}
                  />
                </label>
                {tab === 'signup' && mode === 'invite' && (
                  <label className="vc-field">
                    <span>Invite code</span>
                    <input value={invite} required onChange={(e) => setInvite(e.target.value)} />
                  </label>
                )}
              </>
            )}

            {error && <div className="vc-error">{error}</div>}

            <button className="vc-btn vc-btn-primary" type="submit" disabled={busy} style={{ width: '100%', marginTop: 6 }}>
              {busy ? 'One sec…' : useAdmin ? 'Enter studio' : tab === 'signup' ? 'Create account →' : 'Log in →'}
            </button>
          </form>
        )}

        {tab === 'signup' && !useAdmin && !signupClosed && (
          <p className="vc-note" style={{ marginTop: 14, textAlign: 'center' }}>
            By signing up you agree to the{' '}
            <a className="vc-link" href="/terms" target="_blank" rel="noreferrer">
              Terms
            </a>{' '}
            and{' '}
            <a className="vc-link" href="/privacy" target="_blank" rel="noreferrer">
              Privacy Policy
            </a>
            .
          </p>
        )}
        <p className="vc-note" style={{ marginTop: 18, textAlign: 'center' }}>
          <span className="vc-link" onClick={() => setUseAdmin((v) => !v)}>
            {useAdmin ? '← Back to sign up' : 'Owner? Use an access token'}
          </span>
        </p>
      </div>
    </div>
  )
}
