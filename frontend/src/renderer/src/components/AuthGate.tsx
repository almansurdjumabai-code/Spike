import { useEffect, useState } from 'react'
import { checkBackendAccess, type BackendAccess } from '../lib/backend'
import Landing from './landing/Landing'

/** The account page: license key, desktop downloads, setup steps. */
export const ACCOUNT_PATH = '/app'

/** The welcome page at /. Signed-in visitors get "My account" instead of
 *  sign up / log in; signing in goes straight to the account page. */
export function LandingRoute(): JSX.Element {
  const [access, setAccess] = useState<BackendAccess | 'checking'>('checking')
  useEffect(() => {
    void checkBackendAccess().then(setAccess)
  }, [])
  return (
    <Landing
      notice={null}
      signedIn={access === 'ok'}
      onAuthed={() => window.location.assign(ACCOUNT_PATH)}
    />
  )
}
