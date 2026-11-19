import { useEffect, useRef, useState, type CSSProperties } from 'react'

/** One animated 9:16 clip template, the kind SpikeClip renders: gameplay,
 *  a streamer's facecam, karaoke captions, live chat and floating reactions.
 *  The streamers are made-up personas; the "gameplay" is drawn, not footage. */

export type ClipLayout = 'cam-top' | 'bubble' | 'full'

export interface ClipSpec {
  layout: ClipLayout
  handle: string
  initials: string
  accent: string
  highlight: string
  views: string
  tag: string
  caption: string
  sky: [string, string, string]
  durationS?: number
}

const CHAT_USERS = ['vicefan22', 'neonpalms', 'jetski_jay', 'lucky7', 'clipfarmer', 'mintyfresh', 'bigvibes', 'oceandrive']
const CHAT_COLORS = ['#5effc1', '#39f0ff', '#ffd56b', '#ff9a52', '#ff4fa3', '#c4a1ff']
const CHAT_LINES = [
  'W', 'W W W', 'LMAOOO', 'NO SHOT 😭', 'CLIP IT 🔥', 'L take', "he's cooked 💀", 'GOATED',
  'W streamer', 'chat is this real', '+2', 'bro is HIM', 'AINT NO WAY', 'W W', 'run it back'
]
const REACTS = ['W', 'W', 'W', 'L', '🔥', '😭', '💀', 'W']

function Skyline({ color }: { color: string }): JSX.Element {
  return (
    <svg viewBox="0 0 200 60" preserveAspectRatio="none" style={{ width: '50%', height: '100%', display: 'block' }}>
      <path
        fill={color}
        d="M0 60 V38 h10 V22 h12 v16 h6 V12 h14 v26 h8 V30 h10 V18 h6 V8 h10 v52 Z M86 60 V26 h12 V14 h8 v12 h10 V34 h14 V20 h10 v40 Z M150 60 V30 h8 V10 h14 v20 h8 V24 h10 V36 h10 v24 Z"
      />
    </svg>
  )
}

function Car({ accent }: { accent: string }): JSX.Element {
  return (
    <svg className="vc-run-car" viewBox="0 0 120 60">
      <path d="M14 34 C 18 18, 34 12, 60 12 C 86 12, 102 18, 106 34 L 110 46 H 10 Z" fill={accent} />
      <path d="M30 30 C 34 20, 44 17, 60 17 C 76 17, 86 20, 90 30 Z" fill="#1b0730" opacity="0.85" />
      <rect x="10" y="40" width="100" height="10" rx="4" fill="#1b0730" />
      <rect x="14" y="36" width="22" height="6" rx="3" fill="#ff2147" />
      <rect x="84" y="36" width="22" height="6" rx="3" fill="#ff2147" />
      <rect x="16" y="48" width="18" height="10" rx="3" fill="#0b0418" />
      <rect x="86" y="48" width="18" height="10" rx="3" fill="#0b0418" />
    </svg>
  )
}

function Gameplay({ spec }: { spec: ClipSpec }): JSX.Element {
  const [a, b, c] = spec.sky
  return (
    <div className="vc-run">
      <div className="vc-run-sky" style={{ background: `linear-gradient(${a}, ${b} 60%, ${c})` }} />
      <div className="vc-run-city" style={{ display: 'flex' }}>
        <Skyline color="#2a1050" />
        <Skyline color="#2a1050" />
      </div>
      <div className="vc-run-road" />
      <div className="vc-speedlines" />
      <Car accent={spec.accent} />
    </div>
  )
}

function Facecam({ spec, bubble }: { spec: ClipSpec; bubble: boolean }): JSX.Element {
  return (
    <div
      className={`vc-clip-cam ${bubble ? 'bubble' : 'top'}`}
      style={{
        background: bubble
          ? `radial-gradient(circle at 50% 35%, #3b1d6e, #12051f)`
          : `radial-gradient(circle at 50% 40%, ${spec.accent}55, transparent 60%), linear-gradient(135deg, #1b0a3d, #3a1265)`
      }}
    >
      {!bubble && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: `repeating-linear-gradient(90deg, transparent 0 22px, ${spec.accent}22 22px 23px)`,
            opacity: 0.6
          }}
        />
      )}
      <div className="vc-avatar" style={{ background: `linear-gradient(135deg, ${spec.accent}, #6d3bf2)` }}>
        {spec.initials}
      </div>
    </div>
  )
}

export default function ClipCard({ spec, style }: { spec: ClipSpec; style?: CSSProperties }): JSX.Element {
  const words = spec.caption.split(' ')
  const dur = spec.durationS ?? 9
  const [word, setWord] = useState(0)
  const [chat, setChat] = useState<{ id: number; user: string; color: string; text: string }[]>([])
  const [reacts, setReacts] = useState<{ id: number; text: string; dx: number }[]>([])
  const seq = useRef(0)
  const host = useRef<HTMLDivElement>(null)
  const [visible, setVisible] = useState(true)

  // Only animate while on screen: a page of these must stay light.
  useEffect(() => {
    const el = host.current
    if (!el || !('IntersectionObserver' in window)) return
    const io = new IntersectionObserver(([e]) => setVisible(e.isIntersecting), { rootMargin: '100px' })
    io.observe(el)
    return () => io.disconnect()
  }, [])

  useEffect(() => {
    if (!visible) return
    const t = setInterval(() => setWord((w) => (w + 1) % (words.length + 3)), 360)
    return () => clearInterval(t)
  }, [visible, words.length])

  useEffect(() => {
    if (!visible) return
    const add = (): void => {
      const id = ++seq.current
      const user = CHAT_USERS[Math.floor(Math.random() * CHAT_USERS.length)]
      setChat((c) => [
        ...c.slice(-4),
        {
          id,
          user,
          color: CHAT_COLORS[user.length % CHAT_COLORS.length],
          text: CHAT_LINES[Math.floor(Math.random() * CHAT_LINES.length)]
        }
      ])
    }
    const t = setInterval(add, 700 + Math.random() * 500)
    return () => clearInterval(t)
  }, [visible])

  useEffect(() => {
    if (!visible) return
    const t = setInterval(() => {
      const id = ++seq.current
      setReacts((r) => [...r.slice(-6), { id, text: REACTS[Math.floor(Math.random() * REACTS.length)], dx: Math.random() * 30 - 15 }])
      setTimeout(() => setReacts((r) => r.filter((x) => x.id !== id)), 2600)
    }, 520)
    return () => clearInterval(t)
  }, [visible])

  const vars = { '--accent': spec.accent, '--hl': spec.highlight, '--glow': `${spec.accent}99`, '--dur': `${dur}s`, ...style } as CSSProperties

  return (
    <div className="vc-clip" style={vars} ref={host}>
      <div className={`vc-clip-game${spec.layout === 'cam-top' ? ' split' : ''}`}>
        <Gameplay spec={spec} />
      </div>
      {spec.layout !== 'full' && <Facecam spec={spec} bubble={spec.layout === 'bubble'} />}
      <div className="vc-flash" />

      <div className="vc-clip-top">
        <span className="vc-handle">
          <i />@{spec.handle}
        </span>
        <span className="vc-views">▶ {spec.views}</span>
      </div>
      <div className="vc-spike-badge">⚡ SPIKE 98</div>

      <div className="vc-caption">
        {words.map((w, i) => (
          <span key={i} className={`w${i === word ? ' on' : ''}`}>
            {w}
          </span>
        ))}
      </div>

      <div className="vc-chat">
        {chat.map((m) => (
          <div key={m.id} className="vc-chat-line">
            <b style={{ color: m.color }}>{m.user}</b>
            {m.text}
          </div>
        ))}
      </div>

      <div className="vc-reacts">
        {reacts.map((r) => (
          <span
            key={r.id}
            className="vc-react"
            style={{ '--dx': `${r.dx}px`, color: r.text === 'L' ? '#ff4d6d' : r.text === 'W' ? '#5effc1' : undefined } as CSSProperties}
          >
            {r.text}
          </span>
        ))}
      </div>

      <div className="vc-clip-bottom">
        <span className="vc-tag">{spec.tag}</span>
        <div className="vc-progress">
          <i />
        </div>
      </div>
    </div>
  )
}
