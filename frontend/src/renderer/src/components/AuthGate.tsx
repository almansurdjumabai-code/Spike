import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { checkBackendAccess, type BackendAccess } from '../lib/backend'
import Landing from './landing/Landing'

export const STUDIO_PATH = '/app'

/** The welcome page at /. Signed-in visitors see "Open studio" instead of
 *  sign up / log in; signing in goes straight to the studio. */
export function LandingRoute(): JSX.Element {
  const [access, setAccess] = useState<BackendAccess | 'checking'>('checking')
  useEffect(() => {
    void checkBackendAccess().then(setAccess)
  }, [])
  return (
    <Landing
      notice={null}
      signedIn={access === 'ok'}
      onAuthed={() => window.location.assign(STUDIO_PATH)}
    />
  )
}

/** Web build only, at /app: the landing page until the visitor is signed in.
 *
 *  A backend with no token configured (local development) lets everyone
 *  straight into the studio. A cloud backend answers 401 until the visitor
 *  signs up, logs in, or pastes the owner's access token. A backend that
 *  doesn't answer (a free Render instance waking up) is retried quietly.
 */
export default function AuthGate({ children }: { children: ReactNode }): JSX.Element {
  const [access, setAccess] = useState<BackendAccess | 'checking'>('checking')

  const check = useCallback(async () => {
    setAccess(await checkBackendAccess())
  }, [])

  useEffect(() => {
    void check()
  }, [check])

  useEffect(() => {
    if (access !== 'unreachable') return
    const t = setTimeout(() => void check(), 8000)
    return () => clearTimeout(t)
  }, [access, check])

  if (access === 'ok') return <>{children}</>

  return (
    <Landing
      notice={access === 'unreachable' ? 'Waking up the clip engine… this can take up to a minute.' : null}
      onAuthed={() => void check()}
    />
  )
}
