import '@fontsource/dela-gothic-one/400.css'
import { useEffect, useRef, useState, type CSSProperties } from 'react'
import { CLIP_FROM, PLATFORMS, POST_TO, PlatformIcon } from './Platforms'

/** The block under the marquee: the pipeline (where clips come from and go),
 *  a live demo of the spike detector, and four big numbers that count up.
 *
 *  Everything in the monitor is a simulation and is labelled "Demo": a fake
 *  stream's chat rate wiggles, a spike rises every few seconds, the detector
 *  brackets it (20 s before, 10 s after) and the clip counter ticks. Nothing
 *  here claims real usage numbers.
 */

const BARS = 56
const BEFORE = 10 // bars before the peak inside the clip window (≈20 s)
const AFTER = 5 // bars after it (≈10 s)

const NAMES = ['xqcFan', 'kaiW', 'clipgod', 'nightowl', 'speedrun', 'vicecity', 'lilmoney', 'jynxi', 'ttvGhost', 'mia_lol']
const CALM = ['lol', 'gg', 'true', 'bro 😭', 'nah', 'chat is this real', 'W', 'LMAO', 'ok ok', 'first']
const HYPE = ['W W W W', 'NO SHOT 😭', 'CLIP IT 🔥', 'HE IS COOKED 💀', 'WWWWWWW', 'BROOO', 'RUN IT BACK', '💀💀💀']
const COLORS = ['#ff4fa3', '#39f0ff', '#ffd56b', '#5effc1', '#a855f7', '#ff9a52']

type Msg = { id: number; name: string; text: string; color: string; hype: boolean }

function useInView<T extends Element>(): [React.RefObject<T>, boolean] {
  const ref = useRef<T>(null)
  const [on, setOn] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const io = new IntersectionObserver(([e]) => setOn(e.isIntersecting), { threshold: 0.15 })
    io.observe(el)
    return () => io.disconnect()
  }, [])
  return [ref, on]
}

const reduced = (): boolean => window.matchMedia('(prefers-reduced-motion: reduce)').matches

/** Rolls a number up (or down) once the element is on screen, with an overshoot. */
function Roll({ from = 0, to, decimals = 0, prefix = '', suffix = '', ms = 1600 }: {
  from?: number
  to: number
  decimals?: number
  prefix?: string
  suffix?: string
  ms?: number
}): React.JSX.Element {
  const [ref, on] = useInView<HTMLSpanElement>()
  const [v, setV] = useState(from)
  const done = useRef(false)
  useEffect(() => {
    if (!on || done.current) return
    done.current = true
    if (reduced()) return setV(to)
    let raf = 0
    const t0 = performance.now()
    const step = (t: number): void => {
      const k = Math.min(1, (t - t0) / ms)
      // easeOutBack: a little past the target, then settle.
      const c = 1.7
      const e = 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2)
      setV(from + (to - from) * e)
      if (k < 1) raf = requestAnimationFrame(step)
    }
    raf = requestAnimationFrame(step)
    return () => cancelAnimationFrame(raf)
  }, [on, from, to, ms])
  const settled = Math.abs(v - to) < 0.004
  const shown = decimals && !settled ? Math.max(0, v).toFixed(decimals) : String(Math.round(settled ? to : v))
  return (
    <span ref={ref} className="vc-roll">
      {prefix}
      {shown}
      {suffix}
    </span>
  )
}

/** A number that keeps ticking while visible (messages scanned in the demo). */
function Ticker({ base, perSec, on }: { base: number; perSec: number; on: boolean }): React.JSX.Element {
  const [v, setV] = useState(base)
  useEffect(() => {
    if (!on) return
    const id = window.setInterval(() => setV((x) => x + Math.round(perSec / 10 + Math.random() * perSec / 10)), 100)
    return () => window.clearInterval(id)
  }, [on, perSec])
  return <>{v.toLocaleString('en-US')}</>
}

function SpikeMonitor(): React.JSX.Element {
  const [ref, on] = useInView<HTMLDivElement>()
  const [bars, setBars] = useState<number[]>(() => Array.from({ length: BARS }, () => 0.15 + Math.random() * 0.2))
  const [peaks, setPeaks] = useState<number[]>([]) // bar index of each tracked peak
  const [clips, setClips] = useState(0)
  const [flash, setFlash] = useState(0)
  const [rate, setRate] = useState(840)
  const [chat, setChat] = useState<Msg[]>([])
  const phase = useRef({ spikeIn: 18, rising: -1 })
  const mid = useRef(0)

  useEffect(() => {
    if (!on) return
    const still = reduced()
    const tick = window.setInterval(() => {
      const p = phase.current
      let next = 0.14 + Math.random() * 0.22
      let hype = false
      if (p.rising >= 0) {
        // Rise over 5 bars, peak, then fall back over 6.
        const curve = [0.35, 0.5, 0.68, 0.84, 1, 0.82, 0.62, 0.46, 0.34, 0.26, 0.2]
        next = curve[p.rising] + Math.random() * 0.06
        hype = p.rising < 9
        if (p.rising === 4) {
          setPeaks((ps) => [...ps, BARS - 1])
          setClips((c) => c + 1)
          setFlash((f) => f + 1)
        }
        p.rising = p.rising + 1 < curve.length ? p.rising + 1 : -1
      } else if (--p.spikeIn <= 0) {
        p.rising = 0
        p.spikeIn = 26 + Math.floor(Math.random() * 14)
      }
      setBars((b) => [...b.slice(1), Math.min(1, next)])
      setPeaks((ps) => ps.map((i) => i - 1).filter((i) => i + AFTER > -2))
      setRate(Math.round(600 + next * 4200 + Math.random() * 120))
      if (!still && (hype || Math.random() < 0.45)) {
        const m: Msg = {
          id: ++mid.current,
          name: NAMES[Math.floor(Math.random() * NAMES.length)],
          text: hype ? HYPE[Math.floor(Math.random() * HYPE.length)] : CALM[Math.floor(Math.random() * CALM.length)],
          color: COLORS[Math.floor(Math.random() * COLORS.length)],
          hype
        }
        setChat((c) => [...c.slice(-7), m])
      }
    }, still ? 600 : 160)
    return () => window.clearInterval(tick)
  }, [on])

  const peak = peaks.length ? peaks[peaks.length - 1] : null
  const hot = bars[BARS - 1] > 0.6

  return (
    <div ref={ref} className={`vc-glass vc-monitor${hot ? ' hot' : ''}`}>
      <div className="vc-monitor-head">
        <span className="vc-mon-dot" />
        <b>SPIKE MONITOR</b>
        <span className="vc-monitor-tag">Demo stream</span>
        <span className="vc-monitor-rate">
          <b>{rate.toLocaleString('en-US')}</b> <small>msg / min</small>
        </span>
      </div>
      <div className="vc-monitor-body">
        <div className="vc-mon-graph">
          <div className="vc-mon-grid" />
          {bars.map((h, i) => (
            <i key={i} style={{ '--h': h } as CSSProperties} className={h > 0.6 ? 'hot' : ''} />
          ))}
          {peak !== null && (
            <div
              className="vc-mon-window"
              style={{
                left: `${(Math.max(0, peak - BEFORE) / BARS) * 100}%`,
                width: `${((Math.min(BARS, peak + AFTER + 1) - Math.max(0, peak - BEFORE)) / BARS) * 100}%`
              }}
            >
              <span className="vc-mon-l">−20s</span>
              <span className="vc-mon-peak" style={{ left: `${((peak - Math.max(0, peak - BEFORE)) / (Math.min(BARS, peak + AFTER + 1) - Math.max(0, peak - BEFORE))) * 100}%` }} />
              <span className="vc-mon-r">+10s</span>
            </div>
          )}
          {flash > 0 && (
            <div key={flash} className="vc-spike-badge">
              SPIKE DETECTED
            </div>
          )}
        </div>
        <div className="vc-chatfeed" aria-hidden="true">
          {chat.map((m) => (
            <div key={m.id} className={m.hype ? 'hype' : ''}>
              <b style={{ color: m.color }}>{m.name}</b> {m.text}
            </div>
          ))}
        </div>
      </div>
      <div className="vc-monitor-foot">
        <div>
          <b className="vc-big-num">{clips}</b>
          <span>clips cut in this demo</span>
        </div>
        <div>
          <b className="vc-big-num">
            <Ticker base={0} perSec={140} on={on} />
          </b>
          <span>chat messages read</span>
        </div>
        <div className="vc-monitor-last">
          {clips > 0 ? (
            <>
              <span className="vc-saved">✓ clip_{String(clips).padStart(3, '0')}.mp4</span>
              <span>0:30 · 1080×1920 · captions on</span>
            </>
          ) : (
            <span>waiting for chat to lose it…</span>
          )}
        </div>
      </div>
    </div>
  )
}

function Pipeline(): React.JSX.Element {
  return (
    <div className="vc-glass vc-pipe">
      <div className="vc-pipe-col">
        <h4>Clip from</h4>
        {CLIP_FROM.map((p, i) => (
          <span key={p} className="vc-board-tile" style={{ '--d': `${i * 0.5}s` } as CSSProperties}>
            <PlatformIcon id={p} />
            {PLATFORMS[p].label}
            <em className="vc-pipe-wire" />
          </span>
        ))}
      </div>
      <div className="vc-pipe-hub">
        <div className="vc-hub-ring" />
        <div className="vc-hub-core">
          <span>⚡</span>
          <b>SpikeClip</b>
          <small>on your PC</small>
        </div>
      </div>
      <div className="vc-pipe-col out">
        <h4>Post to</h4>
        {POST_TO.map((p, i) => (
          <span key={p} className="vc-board-tile" style={{ '--d': `${i * 0.4 + 0.3}s` } as CSSProperties}>
            <em className="vc-pipe-wire" />
            <PlatformIcon id={p} />
            {PLATFORMS[p].label}
          </span>
        ))}
      </div>
    </div>
  )
}

export default function LiveStats(): React.JSX.Element {
  return (
    <section className="vc-section vc-live" style={{ paddingTop: 40, paddingBottom: 40 }}>
      <Pipeline />
      <SpikeMonitor />
      <div className="vc-stats">
        <div className="vc-glass vc-stat vc-stat-pre">
          <div className="vc-stat-num">
            <Roll to={20} suffix="s" />
          </div>
          <div className="vc-stat-label">before every chat peak</div>
          <div className="vc-stat-bar"><i /></div>
        </div>
        <div className="vc-glass vc-stat vc-stat-post">
          <div className="vc-stat-num">
            <Roll to={10} suffix="s" />
          </div>
          <div className="vc-stat-label">after it, for the reaction</div>
          <svg className="vc-stat-ring" viewBox="0 0 40 40" aria-hidden="true">
            <circle cx="20" cy="20" r="16" />
            <circle cx="20" cy="20" r="16" className="run" />
          </svg>
        </div>
        <div className="vc-glass vc-stat vc-stat-free">
          <div className="vc-stat-num">
            <Roll from={0.42} to={0} decimals={2} prefix="$" ms={2200} />
          </div>
          <div className="vc-stat-label">cloud render fees, ever</div>
          <div className="vc-stat-strike">no per-minute cloud billing</div>
        </div>
        <div className="vc-glass vc-stat vc-stat-ratio">
          <div className="vc-stat-num">
            <span className="vc-roll">9:16</span>
          </div>
          <div className="vc-stat-label">vertical, captions burned in</div>
          <div className="vc-stat-phone"><i /></div>
        </div>
      </div>
    </section>
  )
}
