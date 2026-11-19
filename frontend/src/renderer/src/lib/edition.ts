import { getApiToken } from './backend'

/** Which studio a visitor gets.
 *
 *  Customers of the web app (signed in with an account, so their session
 *  token starts "sc_") get the simple studio: make clips, see them, edit
 *  them. Everything that runs the service — models, AI providers, plugins,
 *  server load, donations — stays with the owner, who signs in with the
 *  admin token and sees the full studio. The desktop app is always full.
 *
 *  Read at render time: the browser shim installs window.studio after the
 *  modules load.
 */
export function isSimple(): boolean {
  if (window.studio?.platform !== 'browser') return false
  // Dev preview of the customer view: /app?studio-preview&simple
  if (window.location.search.includes('simple')) return true
  return (getApiToken() ?? '').startsWith('sc_')
}

/** The add-video options a customer sees. */
export const SIMPLE_TOGGLES = new Set(['long_clips', 'gaming'])
