import { useCallback, useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { API_BASE, checkBackendAccess, setApiToken, type BackendAccess } from '../lib/backend'

/** Web build only: holds the app back until the backend lets us in.
 *
 *  A cloud backend with SPIKECLIP_API_TOKEN set answers 401 to everything
 *  but /health; this asks for the token once, keeps it in the browser, and
 *  then gets out of the way. A backend with no token passes straight through.
 */
export default function TokenGate({ children }: { children: ReactNode }): JSX.Element {
  const [access, setAccess] = useState<BackendAccess | 'checking'>('checking')
  const [token, setToken] = useState('')
  const [wrong, setWrong] = useState(false)

  const check = useCallback(async () => {
    setAccess('checking')
    setAccess(await checkBackendAccess())
  }, [])

  useEffect(() => {
    void check()
  }, [check])

  const submit = async (e: FormEvent): Promise<void> => {
    e.preventDefault()
    setApiToken(token.trim())
    const result = await checkBackendAccess()
    setWrong(result === 'needs-token')
    if (result === 'needs-token') setApiToken(null)
    setAccess(result)
  }

  if (access === 'ok') return <>{children}</>

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-base text-ink">
      <div className="w-full max-w-sm rounded-xl border border-white/10 p-6 space-y-4">
        <h1 className="text-xl font-bold">
          Spike<span className="text-accent">Clip</span>
        </h1>
        {access === 'checking' && <p className="text-sm text-muted">Connecting to {API_BASE}…</p>}
        {access === 'unreachable' && (
          <>
            <p className="text-sm">
              Can't reach the SpikeClip backend at <code>{API_BASE}</code>. Check that it is running and that
              this site's address is in its SPIKECLIP_CORS_ORIGINS.
            </p>
            <button className="btn-accent" onClick={() => void check()}>
              Try again
            </button>
          </>
        )}
        {access === 'needs-token' && (
          <form className="space-y-3" onSubmit={(e) => void submit(e)}>
            <label className="block text-sm" htmlFor="spikeclip-token">
              Access token (SPIKECLIP_API_TOKEN on the backend)
            </label>
            <input
              id="spikeclip-token"
              type="password"
              autoComplete="current-password"
              className="w-full rounded-md border border-white/20 bg-transparent px-3 py-2"
              value={token}
              onChange={(e) => setToken(e.target.value)}
            />
            {wrong && <p className="text-sm text-red-400">That token was not accepted.</p>}
            <button className="btn-accent" type="submit" disabled={!token.trim()}>
              Continue
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
