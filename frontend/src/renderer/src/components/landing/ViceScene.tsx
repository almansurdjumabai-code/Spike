import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'

/** The hero's moving backdrop: a Vice-sunset skyline drawn in SVG.
 *
 *  Everything is original vector art, animated with CSS (landing.css):
 *  drifting clouds, a striped sun, twinkling windows, a neon bridge with
 *  traffic trails, swaying palms, a helicopter and birds, water shimmer.
 *  The layers follow the pointer at different depths for parallax.
 *
 *  An optional video plays on top if one is published at /media/hero.mp4
 *  (frontend/src/renderer/public/media/). Use footage you have the rights
 *  to; without it, the drawing is the background.
 */

// Deterministic "random" so the skyline is the same on every render.
function rng(seed: number): () => number {
  let s = seed
  return () => {
    s = (s * 16807) % 2147483647
    return (s - 1) / 2147483646
  }
}

interface Tower {
  x: number
  w: number
  h: number
  windows: { x: number; y: number; d: number }[]
}

function skyline(seed: number, count: number, baseY: number, minH: number, maxH: number, lit: number): Tower[] {
  const r = rng(seed)
  const out: Tower[] = []
  let x = -20
  for (let i = 0; i < count && x < 1640; i++) {
    const w = 38 + r() * 70
    const h = minH + r() * (maxH - minH)
    const windows: Tower['windows'] = []
    for (let wy = baseY - h + 14; wy < baseY - 10; wy += 13) {
      for (let wx = x + 6; wx < x + w - 8; wx += 11) {
        if (r() < lit) windows.push({ x: wx, y: wy, d: r() * 6 })
      }
    }
    out.push({ x, w, h, windows })
    x += w + 2 + r() * 10
  }
  return out
}

function Palm({ x, y, s, flip = false, slow = false }: { x: number; y: number; s: number; flip?: boolean; slow?: boolean }): JSX.Element {
  const frond = (rot: number, len: number): JSX.Element => (
    <path
      key={rot}
      transform={`rotate(${rot})`}
      d={`M0 0 C ${len * 0.3} -${len * 0.18}, ${len * 0.7} -${len * 0.16}, ${len} ${len * 0.12}
          C ${len * 0.82} ${len * 0.02}, ${len * 0.62} ${len * 0.02}, ${len * 0.5} ${len * 0.08}
          C ${len * 0.46} ${len * 0.03}, ${len * 0.32} 0, ${len * 0.22} ${len * 0.05} Z`}
    />
  )
  return (
    <g transform={`translate(${x} ${y}) scale(${flip ? -s : s} ${s})`} fill="#160627">
      <g className={`vc-palm-sway${slow ? ' slow' : ''}`}>
        <path d="M-7 0 C -4 -120, 10 -260, 34 -380 L 44 -378 C 22 -258, 10 -120, 9 0 Z" />
        <g transform="translate(40 -380)">
          {[-160, -130, -100, -70, -35, -10, 15, 40].map((r, i) => frond(r, 150 + (i % 3) * 30))}
          <circle r="10" />
        </g>
      </g>
    </g>
  )
}

export default function ViceScene({ children }: { children?: ReactNode }): JSX.Element {
  const root = useRef<HTMLDivElement>(null)
  const [videoReady, setVideoReady] = useState(false)
  const [videoFailed, setVideoFailed] = useState(false)

  const far = useMemo(() => skyline(7, 40, 640, 80, 210, 0.05), [])
  const near = useMemo(() => skyline(42, 34, 650, 120, 360, 0.18), [])
  const stars = useMemo(() => {
    const r = rng(99)
    return Array.from({ length: 60 }, () => ({ x: r() * 1600, y: r() * 260, s: 0.6 + r() * 1.4, d: r() * 4 }))
  }, [])

  // Pointer parallax: each [data-depth] layer moves by its depth.
  useEffect(() => {
    const el = root.current
    if (!el || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const layers = Array.from(el.querySelectorAll<SVGGElement>('[data-depth]'))
    let raf = 0
    let tx = 0
    let ty = 0
    let cx = 0
    let cy = 0
    const onMove = (e: PointerEvent): void => {
      tx = e.clientX / window.innerWidth - 0.5
      ty = e.clientY / window.innerHeight - 0.5
    }
    const tick = (): void => {
      cx += (tx - cx) * 0.06
      cy += (ty - cy) * 0.06
      for (const l of layers) {
        const d = Number(l.dataset.depth)
        l.setAttribute('transform', `translate(${(-cx * d).toFixed(2)} ${(-cy * d * 0.5).toFixed(2)})`)
      }
      raf = requestAnimationFrame(tick)
    }
    window.addEventListener('pointermove', onMove)
    raf = requestAnimationFrame(tick)
    return () => {
      window.removeEventListener('pointermove', onMove)
      cancelAnimationFrame(raf)
    }
  }, [])

  return (
    <div className="vc-scene" ref={root} aria-hidden="true">
      <svg viewBox="0 0 1600 900" preserveAspectRatio="xMidYMid slice">
        <defs>
          <linearGradient id="vc-sky" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#140838" />
            <stop offset="0.28" stopColor="#4b1fa8" />
            <stop offset="0.5" stopColor="#c03ab8" />
            <stop offset="0.62" stopColor="#ff5f8f" />
            <stop offset="0.7" stopColor="#ffa25a" />
          </linearGradient>
          <linearGradient id="vc-sun" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#ffe48a" />
            <stop offset="0.55" stopColor="#ff9a52" />
            <stop offset="1" stopColor="#ff3d8b" />
          </linearGradient>
          <mask id="vc-sun-stripes">
            <rect x="0" y="0" width="1600" height="900" fill="#fff" />
            {[0, 1, 2, 3, 4, 5].map((i) => (
              <rect key={i} x="700" y={520 + i * 22} width="700" height={4 + i * 2.2} fill="#000" />
            ))}
          </mask>
          <linearGradient id="vc-water" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#ff6f9c" />
            <stop offset="0.25" stopColor="#7a2fb5" />
            <stop offset="1" stopColor="#140838" />
          </linearGradient>
          <filter id="vc-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="6" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <radialGradient id="vc-haze" cx="0.65" cy="0.62" r="0.6">
            <stop offset="0" stopColor="#ffb36b" stopOpacity="0.55" />
            <stop offset="1" stopColor="#ff4fa3" stopOpacity="0" />
          </radialGradient>
        </defs>

        <rect width="1600" height="900" fill="url(#vc-sky)" />
        <rect width="1600" height="900" fill="url(#vc-haze)" />

        <g data-depth="6">
          {stars.map((s, i) => (
            <circle key={i} className="vc-window" cx={s.x} cy={s.y} r={s.s} fill="#fff" opacity="0.7" style={{ animationDelay: `${s.d}s` }} />
          ))}
        </g>

        <g data-depth="10" opacity="0.55">
          <g className="vc-cloud">
            <ellipse cx="200" cy="170" rx="210" ry="34" fill="#ff8fc6" />
            <ellipse cx="300" cy="150" rx="140" ry="40" fill="#f6a3d6" />
          </g>
          <g className="vc-cloud b">
            <ellipse cx="900" cy="250" rx="260" ry="30" fill="#ffb08a" />
            <ellipse cx="1010" cy="228" rx="150" ry="34" fill="#ffc3a3" />
          </g>
        </g>

        <g data-depth="14">
          <circle className="vc-sun" cx="1060" cy="520" r="190" fill="url(#vc-sun)" mask="url(#vc-sun-stripes)" filter="url(#vc-glow)" />
        </g>

        <g data-depth="20" className="vc-heli-wrap">
          <g className="vc-heli">
            <g transform="translate(120 200) scale(0.9)">
              <path d="M0 0 h46 a14 12 0 0 1 0 24 h-30 l-30 -6 h-30 v-6 h30 Z" fill="#1d0a3d" />
              <rect className="vc-rotor" x="-20" y="-8" width="90" height="3" rx="1.5" fill="#1d0a3d" />
              <rect x="20" y="-6" width="3" height="7" fill="#1d0a3d" />
              <path d="M0 28 h50 M10 24 v4 M40 24 v4" stroke="#1d0a3d" strokeWidth="2.5" />
              <circle className="vc-beacon" cx="-44" cy="14" r="3.2" fill="#ff2147" />
              <circle className="vc-beacon" cx="56" cy="12" r="2.2" fill="#39f0ff" style={{ animationDelay: '0.5s' }} />
            </g>
          </g>
        </g>

        <g data-depth="16">
          <g className="vc-birds">
          {[0, 1, 2].map((i) => (
            <path
              key={i}
              className="vc-flap"
              style={{ animationDelay: `${i * 0.15}s` }}
              d={`M${1300 + i * 34} ${130 + (i % 2) * 18} q 9 -9 18 0 q 9 -9 18 0`}
              stroke="#1d0a3d"
              strokeWidth="3"
              fill="none"
              strokeLinecap="round"
            />
          ))}
          </g>
        </g>

        <g data-depth="22" fill="#5a2a8e" opacity="0.85">
          {far.map((t, i) => (
            <rect key={i} x={t.x} y={640 - t.h} width={t.w} height={t.h} />
          ))}
        </g>

        <g data-depth="30">
          {near.map((t, i) => (
            <g key={i}>
              <rect x={t.x} y={650 - t.h} width={t.w} height={t.h} fill="#28104f" />
              {i % 5 === 2 && <rect x={t.x} y={650 - t.h} width={t.w} height="4" fill="#5effc1" filter="url(#vc-glow)" />}
              {i % 7 === 4 && <rect x={t.x} y={650 - t.h} width={t.w} height="4" fill="#ff4fa3" filter="url(#vc-glow)" />}
              {t.windows.map((w, j) => (
                <rect key={j} className="vc-window" x={w.x} y={w.y} width="5" height="7" fill="#ffd56b" style={{ animationDelay: `${w.d}s` }} />
              ))}
            </g>
          ))}
        </g>

        <g data-depth="38">
          {/* the neon causeway */}
          <rect x="560" y="606" width="1100" height="14" fill="#2a0f52" />
          {Array.from({ length: 11 }, (_, i) => (
            <path key={i} d={`M${580 + i * 100} 650 v-30 a 40 30 0 0 1 80 0 v30`} fill="none" stroke="#ff4fa3" strokeWidth="4" filter="url(#vc-glow)" opacity="0.9" />
          ))}
          <line className="vc-trail" x1="560" y1="604" x2="1660" y2="604" stroke="#ffe48a" strokeWidth="3" filter="url(#vc-glow)" />
          <line className="vc-trail r" x1="560" y1="611" x2="1660" y2="611" stroke="#ff2147" strokeWidth="3" filter="url(#vc-glow)" />
          <rect x="0" y="648" width="1600" height="252" fill="url(#vc-water)" />
          <g className="vc-water-shine">
            {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
              <rect key={i} x={1060 - (150 - i * 14)} y={668 + i * 26} width={(150 - i * 14) * 2} height={3 + i * 0.6} rx="2" fill="#ffd56b" opacity={0.75 - i * 0.07} />
            ))}
            {[0, 1, 2, 3, 4, 5].map((i) => (
              <rect key={`p${i}`} x={600 + i * 160} y={690 + (i % 3) * 30} width="70" height="2.5" rx="1.25" fill="#ff7fc2" opacity="0.6" />
            ))}
          </g>
        </g>

        <g data-depth="60">
          <Palm x={120} y={920} s={1.35} />
          <Palm x={300} y={940} s={0.95} flip slow />
          <Palm x={1500} y={930} s={1.25} flip />
          <Palm x={1380} y={950} s={0.8} slow />
        </g>
      </svg>

      {!videoFailed && (
        <video
          className={`vc-scene-video${videoReady ? ' ready' : ''}`}
          src="/media/hero.mp4"
          autoPlay
          muted
          loop
          playsInline
          preload="auto"
          onCanPlay={() => setVideoReady(true)}
          onError={() => setVideoFailed(true)}
        />
      )}
      {children}
      <div className="vc-shade" />
      <div className="vc-grain" />
    </div>
  )
}
