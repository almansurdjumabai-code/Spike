import { useEffect, useState, type CSSProperties } from 'react'

/** Short-video flavour for the desktop landing: tilted stickers, a hashtag
 *  strip with the split-colour glitch, app-style toasts that narrate what the
 *  app does, and a burst of reactions on click.
 *
 *  All of it is desktop-only (CSS hides it on phones and touch screens, and
 *  the JS parts don't start there), so the phone build stays light. The toasts
 *  describe product actions; they never claim real users, views or sales.
 */

const DESKTOP = '(min-width: 761px) and (hover: hover)'
const isDesktop = (): boolean => window.matchMedia(DESKTOP).matches && !window.matchMedia('(prefers-reduced-motion: reduce)').matches

type StickerTone = 'pink' | 'cyan' | 'gold' | 'mint' | 'white' | 'black'

export function Sticker({ children, tone = 'pink', rot = -6, style }: {
  children: React.ReactNode
  tone?: StickerTone
  rot?: number
  style?: CSSProperties
}): React.JSX.Element {
  return (
    <span className={`vc-sticker t-${tone}`} style={{ '--rot': `${rot}deg`, ...style } as CSSProperties} aria-hidden="true">
      {children}
    </span>
  )
}

const TAGS = ['#fyp', '#gta6', '#clipit', '#streamer', '#viral', '#twitchclips', '#w', '#nocap', '#foryou', '#kickstreaming', '#reaction', '#chatwentcrazy']

export function HashtagStrip(): React.JSX.Element {
  const row = [...TAGS, ...TAGS]
  return (
    <div className="vc-tags" aria-hidden="true">
      <div className="vc-tags-track">
        {row.map((t, i) => (
          <span key={i} className={i % 3 === 1 ? 'big' : ''}>
            {t}
          </span>
        ))}
      </div>
    </div>
  )
}

const TOASTS = [
  { ico: '⚡', t: 'Spike found', s: '02:14:07 · chat ×9' },
  { ico: '✂️', t: 'clip_012.mp4 ready', s: '0:30 · 1080×1920 · captions on' },
  { ico: '📤', t: 'Exported for TikTok', s: 'saved to /SpikeClip/exports' },
  { ico: '🎯', t: 'Facecam framed', s: 'layout: split · auto-detected' },
  { ico: '💬', t: 'Chat replay synced', s: '48,210 messages read' },
  { ico: '🔥', t: 'Biggest spike of the stream', s: '“NO SHOT” ×412 in 6 s' }
]

export function SpikeToasts(): React.JSX.Element | null {
  const [on] = useState(isDesktop)
  const [list, setList] = useState<{ id: number; k: number }[]>([])
  useEffect(() => {
    if (!on) return
    let n = 0
    let id = 0
    const push = (): void => {
      if (document.hidden || window.scrollY < 300) return // not over the hero, not in background tabs
      const item = { id: ++id, k: n++ % TOASTS.length }
      setList((l) => [...l.slice(-1), item])
      window.setTimeout(() => setList((l) => l.filter((x) => x.id !== item.id)), 5200)
    }
    const first = window.setTimeout(push, 7000)
    const every = window.setInterval(push, 9000)
    return () => {
      window.clearTimeout(first)
      window.clearInterval(every)
    }
  }, [on])
  if (!on) return null
  return (
    <div className="vc-toasts" aria-live="off">
      {list.map((x) => {
        const t = TOASTS[x.k]
        return (
          <div key={x.id} className="vc-toast-card">
            <span className="vc-toast-ico">{t.ico}</span>
            <span>
              <b>{t.t}</b>
              <small>{t.s}</small>
            </span>
            <span className="vc-toast-app">SpikeClip · now</span>
          </div>
        )
      })}
    </div>
  )
}

const BURST = ['❤️', '🔥', '💀', 'W', '😭', '⚡', '💯']

/** Click anywhere (not on a control) on desktop: a little spray of reactions. */
export function useClickBurst(): void {
  useEffect(() => {
    if (!isDesktop()) return
    const onClick = (e: MouseEvent): void => {
      const target = e.target as HTMLElement
      if (target.closest('a, button, input, summary, video, .vc-modal')) return
      for (let i = 0; i < 7; i++) {
        const s = document.createElement('span')
        s.className = 'vc-burst'
        s.textContent = BURST[Math.floor(Math.random() * BURST.length)]
        const a = (Math.PI * 2 * i) / 7 + Math.random() * 0.6
        const d = 50 + Math.random() * 60
        s.style.left = `${e.clientX}px`
        s.style.top = `${e.clientY}px`
        s.style.setProperty('--dx', `${Math.cos(a) * d}px`)
        s.style.setProperty('--dy', `${Math.sin(a) * d - 40}px`)
        s.style.setProperty('--r', `${(Math.random() - 0.5) * 60}deg`)
        document.body.appendChild(s)
        s.addEventListener('animationend', () => s.remove())
      }
    }
    window.addEventListener('click', onClick)
    return () => window.removeEventListener('click', onClick)
  }, [])
}
