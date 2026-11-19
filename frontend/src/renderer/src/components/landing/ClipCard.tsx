import { useEffect, useId, useRef, useState, type CSSProperties } from 'react'

/** A real 9:16 clip, dressed the way it would look on the feed: a side rail
 *  of views / likes / comments, live chat that blows up on the spike, W/L
 *  reactions, a progress bar in time with the video and a sound toggle. */

export interface ClipSpec {
  src: string
  poster: string
  title: string
  views: string
  likes: string
  comments: string
  accent: string
}

const CHAT_USERS = [
  'vicefan22', 'neonpalms', 'jetski_jay', 'lucky7', 'clipfarmer', 'mintyfresh', 'bigvibes', 'oceandrive',
  'tr3yway', 'leonida_kid', 'nightcrawlr', 'goatwatch', 'pinkflamingo', 'sunsetblvd', 'yungviper', 'brokeboy99'
]
const CHAT_COLORS = ['#5effc1', '#39f0ff', '#ffd56b', '#ff9a52', '#ff4fa3', '#c4a1ff', '#7dd3fc', '#fca5a5']
const CALM = [
  'LMAOOO', 'chat is this real', 'bro is HIM', 'run it back', 'he is cooked 💀', 'NAHHH', 'W stream', 'clip that',
  'L take tbh', 'ratio', 'we are so back', 'this game is insane', 'first', 'GOATED', 'he really did that 😭', '+2'
]
const SPAM = ['W', 'W W W', 'WWWWW', 'W', 'CLIP IT 🔥', 'W W', 'NO SHOT 😭', 'W', 'AINT NO WAY', 'WWW', 'L', 'W W W W', '💀💀💀', 'W']
const REACTS = ['W', 'W', 'W', 'W', 'L', '🔥', '😭', '💀', 'W', '❤️']

type Line = { id: number; user: string; color: string; text: string; hot: boolean }
type React = { id: number; text: string; dx: number; size: number }

const pick = <T,>(a: T[]): T => a[Math.floor(Math.random() * a.length)]

export default function ClipCard({ spec, style, compact = false }: { spec: ClipSpec; style?: CSSProperties; compact?: boolean }): JSX.Element {
  const id = useId()
  const host = useRef<HTMLDivElement>(null)
  const video = useRef<HTMLVideoElement>(null)
  const bar = useRef<HTMLElement>(null)
  const seq = useRef(0)
  const [visible, setVisible] = useState(false)
  const [muted, setMuted] = useState(true)
  const [spike, setSpike] = useState(false)
  const [chat, setChat] = useState<Line[]>([])
  const [reacts, setReacts] = useState<React[]>([])

  // Play only while on screen.
  useEffect(() => {
    const el = host.current
    if (!el) return
    if (!('IntersectionObserver' in window)) {
      setVisible(true)
      return
    }
    const io = new IntersectionObserver(([e]) => setVisible(e.isIntersecting), { threshold: 0.25 })
    io.observe(el)
    return () => io.disconnect()
  }, [])

  useEffect(() => {
    const v = video.current
    if (!v) return
    if (visible) void v.play().catch(() => undefined)
    else v.pause()
  }, [visible])

  // One clip with sound at a time.
  useEffect(() => {
    const onSound = (e: Event): void => {
      if ((e as CustomEvent<string>).detail !== id) setMuted(true)
    }
    window.addEventListener('spikeclip-sound', onSound)
    return () => window.removeEventListener('spikeclip-sound', onSound)
  }, [id])

  useEffect(() => {
    if (video.current) video.current.muted = muted
  }, [muted])

  const toggleSound = (): void => {
    if (muted) window.dispatchEvent(new CustomEvent('spikeclip-sound', { detail: id }))
    setMuted((m) => !m)
    void video.current?.play().catch(() => undefined)
  }

  // Progress bar in step with the video.
  useEffect(() => {
    const v = video.current
    if (!v) return
    let raf = 0
    const tick = (): void => {
      if (bar.current && v.duration) bar.current.style.transform = `scaleX(${v.currentTime / v.duration})`
      raf = requestAnimationFrame(tick)
    }
    if (visible) raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [visible])

  // Chat: calm, then a spike where it explodes.
  useEffect(() => {
    if (!visible) return
    let alive = true
    const timers: ReturnType<typeof setTimeout>[] = []
    const later = (fn: () => void, ms: number): void => {
      timers.push(setTimeout(() => alive && fn(), ms))
    }
    const say = (hot: boolean): void => {
      const user = pick(CHAT_USERS)
      setChat((c) => [...c.slice(compact ? -3 : -6), { id: ++seq.current, user, color: CHAT_COLORS[user.length % CHAT_COLORS.length], text: hot ? pick(SPAM) : pick(CALM), hot }])
    }
    const react = (big: boolean): void => {
      const r: React = { id: ++seq.current, text: big ? pick(['W', 'W', 'W', '🔥']) : pick(REACTS), dx: Math.random() * 40 - 20, size: big ? 1.4 + Math.random() * 0.6 : 1 }
      setReacts((x) => [...x.slice(-14), r])
      later(() => setReacts((x) => x.filter((y) => y.id !== r.id)), 2700)
    }
    const calm = (): void => {
      say(false)
      if (Math.random() < 0.5) react(false)
      later(calm, 900 + Math.random() * 700)
    }
    const burst = (): void => {
      setSpike(true)
      for (let i = 0; i < 12; i++) later(() => say(true), i * 110)
      for (let i = 0; i < 14; i++) later(() => react(true), i * 90)
      later(() => setSpike(false), 1800)
      later(burst, 4500 + Math.random() * 3500)
    }
    later(calm, 300)
    later(burst, 1500 + Math.random() * 2500)
    return () => {
      alive = false
      timers.forEach(clearTimeout)
    }
  }, [visible, compact])

  return (
    <div
      ref={host}
      className={`vc-clip${spike ? ' is-spiking' : ''}${compact ? ' is-compact' : ''}`}
      style={{ '--accent': spec.accent, '--glow': `${spec.accent}aa`, ...style } as CSSProperties}
    >
      <video
        ref={video}
        className="vc-clip-video"
        src={spec.src}
        poster={spec.poster}
        muted
        loop
        playsInline
        preload="metadata"
      />
      <div className="vc-clip-shade" />

      <div className="vc-clip-top">
        <span className={`vc-spike-badge${spike ? ' on' : ''}`}>⚡ {spike ? 'SPIKE DETECTED' : 'SPIKE 9X'}</span>
        <button className="vc-sound" onClick={toggleSound} aria-label={muted ? 'Unmute clip' : 'Mute clip'}>
          {muted ? '🔇' : '🔊'}
        </button>
      </div>

      <div className="vc-rail">
        <div className="vc-rail-item big">
          <span>▶</span>
          <b>{spec.views}</b>
        </div>
        <div className="vc-rail-item">
          <span>❤</span>
          <b>{spec.likes}</b>
        </div>
        <div className="vc-rail-item">
          <span>💬</span>
          <b>{spec.comments}</b>
        </div>
        <div className="vc-rail-item">
          <span>↗</span>
          <b>Share</b>
        </div>
      </div>

      <div className="vc-chat">
        {chat.map((m) => (
          <div key={m.id} className={`vc-chat-line${m.hot ? ' hot' : ''}`}>
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
            style={{
              '--dx': `${r.dx}px`,
              fontSize: `${20 * r.size}px`,
              color: r.text === 'L' ? '#ff4d6d' : r.text === 'W' ? '#5effc1' : undefined
            } as CSSProperties}
          >
            {r.text}
          </span>
        ))}
      </div>

      <div className="vc-clip-bottom">
        <div className="vc-progress">
          <i ref={bar} />
        </div>
      </div>
    </div>
  )
}
