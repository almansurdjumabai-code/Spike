import { useEffect, useRef, useState, type CSSProperties } from 'react'

/** The scroll film: a pre-rendered Blender sequence scrubbed by scroll.
 *
 *  The scene (film/bay_scene.py: dusk over the bay, a lit skyline, the pink
 *  causeway, a SpikeClip speedboat, then a phone playing a clip rising out of
 *  the water) is rendered offline into FRAMES WebP stills under /media/film. Scrolling through the pinned section picks the frame to draw
 *  on a canvas, so the page shows film-quality graphics while the browser only
 *  ever paints one image: no WebGL, almost no GPU work.
 *
 *  Frames load coarse-to-fine (every 16th, then 8th, 4th, 2nd, all), and the
 *  nearest loaded frame is drawn, so the scrub works within a second and gets
 *  smoother as the rest arrives.
 *
 *  Beats: 1. the stream plays (aerial over the bay)  2. chat explodes (coins
 *  burst out of the phone)  3. the clip lands (the phone, front and centre).
 */

const FRAMES = 180
const src = (i: number): string => `/media/film/f_${String(i + 1).padStart(4, '0')}.webp`

const BEATS = [
  { n: '01', title: 'Your stream plays', text: 'Point SpikeClip at a VOD. It reads every chat message on your PC.' },
  { n: '02', title: 'Chat explodes', text: 'W spam, “NO SHOT”, 💀 — the peak is found the second chat loses it.' },
  { n: '03', title: 'The clip lands', text: '20 s before the spike, 10 s after. Vertical, captioned, ready to post.' }
]

export default function Scene3D(): React.JSX.Element {
  const section = useRef<HTMLElement>(null)
  const canvas = useRef<HTMLCanvasElement>(null)
  const [beat, setBeat] = useState(0)

  useEffect(() => {
    const el = section.current
    const cv = canvas.current
    if (!el || !cv) return
    const ctx = cv.getContext('2d')
    if (!ctx) return

    const images: (HTMLImageElement | null)[] = new Array(FRAMES).fill(null)
    let cancelled = false
    let drawn = -1
    let target = 0
    let shown = 0
    let raf = 0
    let visible = false
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    // Coarse-to-fine load order.
    const order: number[] = []
    for (const step of [16, 8, 4, 2, 1]) for (let i = 0; i < FRAMES; i += step) if (!order.includes(i)) order.push(i)
    if (!order.includes(FRAMES - 1)) order.splice(1, 0, FRAMES - 1)
    let next = 0
    const loadMore = (): void => {
      if (cancelled || next >= order.length) return
      const i = order[next++]
      const img = new Image()
      img.decoding = 'async'
      img.onload = () => {
        images[i] = img
        drawn = -1 // a closer frame may exist now
        loadMore()
      }
      img.onerror = () => loadMore()
      img.src = src(i)
    }
    // Four parallel lanes.
    for (let k = 0; k < 4; k++) loadMore()

    const nearest = (i: number): HTMLImageElement | null => {
      for (let d = 0; d < FRAMES; d++) {
        const a = images[i - d]
        if (a) return a
        const b = images[i + d]
        if (b) return b
      }
      return null
    }

    const resize = (): void => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      cv.width = Math.round(cv.clientWidth * dpr)
      cv.height = Math.round(cv.clientHeight * dpr)
      drawn = -1
    }

    const draw = (i: number): void => {
      const img = nearest(i)
      if (!img) return
      // object-fit: cover. The phone drifts right of centre in the last
      // beat; on narrow screens keep it in view by following it.
      const s = Math.max(cv.width / img.naturalWidth, cv.height / img.naturalHeight)
      const w = img.naturalWidth * s
      const h = img.naturalHeight * s
      const t = Math.min(1, Math.max(0, (i / (FRAMES - 1) - 0.55) / 0.45))
      const focus = 0.5 + 0.13 * t * t * (3 - 2 * t)
      const x = Math.min(0, Math.max(cv.width - w, cv.width / 2 - focus * w))
      ctx.drawImage(img, x, (cv.height - h) / 2, w, h)
    }

    const progress = (): number => {
      const r = el.getBoundingClientRect()
      const total = r.height - window.innerHeight
      return total > 0 ? Math.min(1, Math.max(0, -r.top / total)) : 0
    }

    const frame = (): void => {
      raf = requestAnimationFrame(frame)
      if (!visible) return
      target = progress()
      shown = reduce ? target : shown + (target - shown) * 0.18
      const i = Math.round(shown * (FRAMES - 1))
      if (i !== drawn) {
        draw(i)
        drawn = i
      }
      const b = target < 0.33 ? 0 : target < 0.64 ? 1 : 2
      setBeat((old) => (old === b ? old : b))
    }

    const io = new IntersectionObserver(([e]) => {
      visible = e.isIntersecting
      if (visible) drawn = -1
    })
    io.observe(el)
    resize()
    window.addEventListener('resize', resize)
    raf = requestAnimationFrame(frame)

    return () => {
      cancelled = true
      cancelAnimationFrame(raf)
      io.disconnect()
      window.removeEventListener('resize', resize)
    }
  }, [])

  return (
    <section className="vc-3d" ref={section} id="showcase" aria-label="How SpikeClip turns a stream into a clip">
      <div className="vc-3d-sticky">
        <canvas ref={canvas} className="vc-3d-canvas" />
        <div className="vc-3d-shade" />
        <div className="vc-3d-copy">
          <div className="vc-kicker">On your PC</div>
          {BEATS.map((b, i) => (
            <div key={b.n} className={`vc-3d-beat${beat === i ? ' on' : ''}`}>
              <span className="vc-3d-n">{b.n}</span>
              <h2 className="vc-display">{b.title}</h2>
              <p>{b.text}</p>
            </div>
          ))}
          <div className="vc-3d-dots">
            {BEATS.map((b, i) => (
              <span key={b.n} className={beat === i ? 'on' : ''} />
            ))}
          </div>
        </div>
        <div className={`vc-3d-chat${beat === 1 ? ' on' : ''}`} aria-hidden="true">
          {['W', 'W W W', 'NO SHOT 😭', 'CLIP IT 🔥', 'WWWWW', '💀💀💀', 'W'].map((m, i) => (
            <span key={i} style={{ '--i': i } as CSSProperties}>
              {m}
            </span>
          ))}
        </div>
      </div>
    </section>
  )
}
