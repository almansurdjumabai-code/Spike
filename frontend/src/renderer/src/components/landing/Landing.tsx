import '@fontsource/anton/400.css'
import { openCheckout, setPendingPlan } from '../../lib/billing'
import '@fontsource-variable/inter'
import './landing.css'
import './landing-extra.css'
import { useEffect, useRef, useState } from 'react'
import AuthModal, { type AuthTab } from './AuthModal'
import ClipCard, { type ClipSpec } from './ClipCard'
import Pricing from './Pricing'
import LiveStats from './LiveStats'
import { CLIP_FROM, PLATFORMS, POST_TO, PlatformIcon } from './Platforms'
import ViceScene from './ViceScene'

/** The public welcome page of the web app: what the clips look like, where
 *  they go, how it works, and the way in (sign up / log in). */

const M = '/media/clips'

const CLIPS: (ClipSpec & { meta: string })[] = [
  { src: `${M}/c1.mp4`, poster: `${M}/c1.jpg`, title: 'First streamer to play GTA 6, flew across the world for it', views: '4.3M', likes: '612K', comments: '18.4K', accent: '#ff9a52', meta: 'IRL · GTA 6 launch' },
  { src: `${M}/c2.mp4`, poster: `${M}/c2.jpg`, title: 'Spends the first 45 minutes of GTA 6 renovating a house', views: '2.4M', likes: '301K', comments: '9.2K', accent: '#39f0ff', meta: 'Gameplay · Funny' },
  { src: `${M}/c3.mp4`, poster: `${M}/c3.jpg`, title: "Can't believe there's a baby in GTA 6", views: '6.7M', likes: '1.1M', comments: '31K', accent: '#ff4fa3', meta: 'Reaction · Viral' },
  { src: `${M}/c4.mp4`, poster: `${M}/c4.jpg`, title: 'NPCs he fought earlier remembered him and tried to jump him', views: '3.9M', likes: '540K', comments: '14K', accent: '#a855f7', meta: 'Gameplay · Shock' },
  { src: `${M}/c5.mp4`, poster: `${M}/c5.jpg`, title: 'Reacting to the GTA 6 trailer, chat lost it', views: '8.2M', likes: '1.4M', comments: '47K', accent: '#ffd56b', meta: 'Reaction · Trailer' },
  { src: `${M}/c6.mp4`, poster: `${M}/c6.jpg`, title: "Gets upset finding out you can't steal cars in GTA 6", views: '5.6M', likes: '870K', comments: '22K', accent: '#5effc1', meta: 'Rage · Gameplay' }
]
const HERO = [CLIPS[2], CLIPS[4], CLIPS[5]]

const MARQUEE = ['W chat', 'Clip it', 'No shot', 'Goated', 'Run it back', 'W streamer', 'Spike detected', 'He is cooked', 'Vice City nights']

const FEATURES = [
  { ico: '💸', title: 'No server bills', text: 'Clips render on your own PC. No per-minute cloud rendering, no credits that run out mid-stream.' },
  { ico: '⚡', title: 'Fast on your hardware', text: "Uses your CPU and GPU directly. No uploading hours of footage, no waiting in someone else's queue." },
  { ico: '🎛️', title: 'You control the limits', text: 'Clip as many streams as your plan allows, whenever you want. What you pay is what you get.' },
  { ico: '📈', title: 'Chat-spike detection', text: 'Finds the moments chat explodes and cuts from 20 seconds before the peak to 10 seconds after.' },
  { ico: '📱', title: 'Vertical 9:16, captioned', text: 'Facecam and gameplay framed for TikTok, Shorts and Reels, with captions burned in.' },
  { ico: '🔒', title: 'Your footage stays yours', text: 'Videos never leave your computer. Our servers only know your account and your license key.' }
]

const FAQ = [
  { q: 'Where is the video processed?', a: 'On your computer. SpikeClip is a desktop app for Windows and Mac: downloading the stream, finding chat peaks and rendering the clips all happen locally. Nothing is uploaded to our servers, which only handle your account, payment and license key.' },
  { q: 'How does it pick the moments?', a: 'It measures chat activity across the whole stream and finds the spikes. Each clip starts 20 seconds before a peak and ends 10 seconds after, so you get the build-up and the reaction.' },
  { q: 'What do I need to run it?', a: 'A Windows 10/11 or macOS computer with at least 8 GB of RAM (16 GB recommended) and free disk space for the streams you clip. A dedicated graphics card makes rendering faster but is not required.' },
  { q: 'How does the license key work?', a: 'After you buy, a key like CLIP-XXXX-XXXX-XXXX appears in your account. Paste it into the app to unlock it. Every key is unique and bound to one computer, so it cannot be shared; moving to a new PC takes one click in your account.' },
  { q: 'Does it work offline?', a: 'Yes. Once activated, the app checks your key every few days and keeps working for up to 7 days without internet. Downloading streams of course needs a connection.' },
  { q: 'Can I cancel or get a refund?', a: 'Cancel anytime from your account and keep your plan until the end of the period you paid for. Not happy? Full refund within 14 days.' }
]

function useReveal(): void {
  useEffect(() => {
    const els = document.querySelectorAll('.vc-reveal, .vc-graph')
    if (!('IntersectionObserver' in window)) {
      els.forEach((e) => e.classList.add('in-view'))
      return
    }
    const io = new IntersectionObserver(
      (entries) => entries.forEach((e) => e.isIntersecting && e.target.classList.add('in-view')),
      { threshold: 0.15 }
    )
    els.forEach((e) => io.observe(e))
    return () => io.disconnect()
  }, [])
}

function VideoWall(): JSX.Element {
  // Each column: one moving clip and two stills, repeated so the loop is seamless.
  const cols = [
    [1, 3, 5],
    [4, 6, 2],
    [5, 1, 3],
    [2, 4, 6]
  ]
  return (
    <>
      <div className="vc-wall" aria-hidden="true">
        {cols.map((col, ci) => (
          <div key={ci} className="vc-wall-col">
            <div className="vc-wall-track" style={{ animationDelay: `${-ci * 9}s` }}>
              {[0, 1].map((rep) =>
                col.map((n, k) =>
                  k === 0 ? (
                    <video key={`${rep}-${k}`} src={`${M}/w${n}.mp4`} poster={`${M}/c${n}.jpg`} autoPlay muted loop playsInline preload="auto" />
                  ) : (
                    <img key={`${rep}-${k}`} src={`${M}/c${n}.jpg`} alt="" loading="lazy" style={{ width: '100%', aspectRatio: '9/16', objectFit: 'cover', borderRadius: 16 }} />
                  )
                )
              )}
            </div>
          </div>
        ))}
      </div>
      <div className="vc-wall-tint" />
    </>
  )
}

function Pipeline(): JSX.Element {
  const spikes = [
    { at: 12, w: 4 },
    { at: 31, w: 5 },
    { at: 50, w: 3 },
    { at: 68, w: 6 },
    { at: 86, w: 4 }
  ]
  return (
    <div className="vc-glass vc-pipeline vc-reveal">
      <div className="vc-pipe-head">
        <span>
          <b>stream_vod_2026-11-19.mp4</b> · 8h 12m
        </span>
        <span>⚡ 5 spikes found · 5 clips ready</span>
      </div>
      <div className="vc-pipe-thumbs">
        {spikes.map((s, i) => (
          <div key={s.at} className="vc-pipe-thumb" style={{ left: `${s.at + s.w / 2}%`, animationDelay: `${((s.at + s.w / 2) * 0.081).toFixed(2)}s` }}>
            <img src={`${M}/c${i + 1}.jpg`} alt="" loading="lazy" />
          </div>
        ))}
      </div>
      <div className="vc-pipe-track">
        {spikes.map((s) => (
          <div key={s.at} className="vc-pipe-spike" style={{ left: `${s.at}%`, width: `${s.w}%`, animationDelay: `${(s.at * 0.081).toFixed(2)}s` }} />
        ))}
        <div className="vc-pipe-scan" />
      </div>
      <div className="vc-pipe-scale">
        <span>0:00</span>
        <span>2:00</span>
        <span>4:00</span>
        <span>6:00</span>
        <span>8:12</span>
      </div>
    </div>
  )
}

function HypeGraph(): JSX.Element {
  const pts = [8, 9, 7, 10, 12, 9, 11, 30, 64, 22, 12, 10, 11, 9, 13, 15, 12, 41, 88, 35, 14, 12, 10, 11, 16, 13, 11, 52, 70, 26, 12, 10, 9, 12]
  const w = 1100
  const h = 260
  const step = w / (pts.length - 1)
  const y = (v: number): number => h - 20 - (v / 95) * (h - 50)
  const d = pts.map((v, i) => `${i ? 'L' : 'M'}${(i * step).toFixed(1)} ${y(v).toFixed(1)}`).join(' ')
  const peaks = [
    { i: 8, label: 'COP CHASE' },
    { i: 18, label: 'TRAILER DROP' },
    { i: 28, label: 'W SPAM' }
  ]
  return (
    <div className="vc-glass vc-graph vc-reveal">
      <svg viewBox={`-10 -30 ${w + 20} ${h + 50}`}>
        <defs>
          <linearGradient id="vc-line" x1="0" x2="1">
            <stop offset="0" stopColor="#39f0ff" />
            <stop offset="0.5" stopColor="#ff4fa3" />
            <stop offset="1" stopColor="#ffd56b" />
          </linearGradient>
          <linearGradient id="vc-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#ff4fa3" stopOpacity="0.35" />
            <stop offset="1" stopColor="#ff4fa3" stopOpacity="0" />
          </linearGradient>
        </defs>
        {peaks.map((p) => (
          <rect key={p.i} x={(p.i - 1.2) * step} y={0} width={step * 2.4} height={h - 20} rx="10" fill="#ff4fa3" opacity="0.12" />
        ))}
        <path d={`${d} L ${w} ${h - 20} L 0 ${h - 20} Z`} fill="url(#vc-fill)" />
        <path className="vc-graph-line" d={d} fill="none" stroke="url(#vc-line)" strokeWidth="4" strokeLinejoin="round" strokeLinecap="round" />
        {peaks.map((p, k) => (
          <g key={p.i} className="vc-peak" style={{ animationDelay: `${1 + k * 0.6}s` }}>
            <circle cx={p.i * step} cy={y(pts[p.i])} r="7" fill="#fff" stroke="#ff4fa3" strokeWidth="4" />
            <rect x={p.i * step - 70} y={y(pts[p.i]) - 46} width="140" height="30" rx="15" fill="#ff4fa3" />
            <text x={p.i * step} y={y(pts[p.i]) - 26} textAnchor="middle" fontFamily="Anton, sans-serif" fontSize="16" fill="#1b0730">
              {p.label}
            </text>
          </g>
        ))}
      </svg>
      <div className="vc-legend">
        <span><i style={{ background: 'linear-gradient(90deg,#39f0ff,#ff4fa3)' }} />Chat activity + voice + game events</span>
        <span><i style={{ background: '#ff4fa355' }} />Moments SpikeClip turns into clips</span>
      </div>
    </div>
  )
}

export default function Landing({
  notice,
  onAuthed,
  signedIn = false
}: {
  notice: string | null
  onAuthed: () => void
  signedIn?: boolean
}): JSX.Element {
  const [auth, setAuth] = useState<AuthTab | null>(null)
  const [toast, setToast] = useState<string | null>(null)
  const [scrolled, setScrolled] = useState(false)
  const cursor = useRef<HTMLDivElement>(null)
  useReveal()

  const root = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const onScroll = (): void => {
      setScrolled(window.scrollY > 20)
      root.current?.style.setProperty('--sy', String(Math.min(window.scrollY, 1200)))
    }
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    const prev = document.body.style.overflow
    document.body.style.overflow = 'auto'
    return () => {
      document.body.style.overflow = prev
    }
  }, [])

  useEffect(() => {
    const onMove = (e: PointerEvent): void => {
      if (cursor.current) cursor.current.style.transform = `translate(${e.clientX}px, ${e.clientY}px)`
    }
    window.addEventListener('pointermove', onMove)
    return () => window.removeEventListener('pointermove', onMove)
  }, [])

  const go = (id: string) => (): void => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })

  return (
    <div className="vc" ref={root}>
      <div className="vc-cursor" ref={cursor} aria-hidden="true" />

      <nav className={`vc-nav${scrolled ? ' is-scrolled' : ''}`}>
        <a className="vc-logo" translate="no" href="#top">
          <span className="vc-logo-mark">⚡</span>
          <span>
            Spike<span className="vc-gradient-text">Clip</span>
          </span>
        </a>
        <div className="vc-nav-links">
          <a href="#clips">Clips</a>
          <a href="#how">How it works</a>
          <a href="#features">Features</a>
          <a href="#pricing" className="vc-nav-hot">
            💸 Pricing<b>−20%</b>
          </a>
          <a href="#faq">FAQ</a>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          {signedIn ? (
            <button className="vc-btn vc-btn-primary vc-btn-sm" onClick={onAuthed}>
              My account →
            </button>
          ) : (
            <>
              <button className="vc-btn vc-btn-glass vc-btn-sm" onClick={() => setAuth('login')}>
                Log in
              </button>
              <button className="vc-btn vc-btn-primary vc-btn-sm" onClick={() => setAuth('signup')}>
                Sign up
              </button>
            </>
          )}
        </div>
      </nav>

      <header className="vc-hero" id="top">
        <ViceScene>
          <VideoWall />
        </ViceScene>
        <div className="vc-hero-inner">
          <div>
            <span className="vc-eyebrow">
              <span className="vc-live-dot">NEW</span>
              Desktop app for Windows &amp; Mac
            </span>
            <h1 className="vc-display vc-hero-title">
              <span className="line"><span>Every stream</span></span>
              <span className="line"><span>has a</span></span>
              <span className="line"><span className="vc-gradient-text">viral spike.</span></span>
            </h1>
            <p className="vc-hero-sub">
              SpikeClip reads your stream&apos;s chat, finds every moment it explodes and cuts it into a
              vertical 9:16 clip — 20 seconds before the peak, 10 after. It runs on your own PC, so you
              never pay for cloud rendering.
            </p>
            <div className="vc-hero-ctas">
              <button className="vc-btn vc-btn-primary" onClick={() => (signedIn ? onAuthed() : setAuth('signup'))}>
                {signedIn ? 'My license & downloads →' : '⬇ Get SpikeClip for PC'}
              </button>
              <button className="vc-btn vc-btn-glass" onClick={go('clips')}>
                ▶ Watch clips
              </button>
            </div>
            <div className="vc-os-row">
              <span className="vc-os">⊞ Windows 10/11</span>
              <span className="vc-os">🍎 macOS</span>
              <span className="vc-os">💻 Runs 100% on your PC</span>
            </div>
            <div className="vc-post-to">
              <span>Post to</span>
              {POST_TO.map((p, i) => (
                <PlatformIcon key={p} id={p} delay={-i * 0.6} />
              ))}
            </div>
          </div>
          <div className="vc-hero-stage">
            {HERO.map((s, i) => (
              <div key={s.src} className={`vc-stage-card c${i}`}>
                <div className="vc-float">
                  <ClipCard spec={s} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </header>

      <div className="vc-marquee" aria-hidden="true">
        <div className="vc-marquee-track">
          {[0, 1].map((k) => (
            <span key={k}>
              {MARQUEE.map((m) => (
                <span key={m}>{m}</span>
              ))}
            </span>
          ))}
        </div>
      </div>

      <LiveStats />

      <section className="vc-section" id="clips">
        <div className="vc-reveal">
          <div className="vc-kicker">Clips that went off</div>
          <h2 className="vc-display vc-h2">
            Straight off the <span className="vc-gradient-text">For You page</span>
          </h2>
          <p className="vc-lead">GTA 6 moments the way SpikeClip delivers them: vertical, captioned, cut on the spike. Hit 🔇 on any clip for sound.</p>
        </div>
        <div className="vc-gallery">
          {CLIPS.map((c, i) => (
            <div key={c.src} className="vc-gallery-item vc-reveal" style={{ transitionDelay: `${(i % 3) * 0.08}s` }}>
              <ClipCard spec={c} />
              <h3>{c.title}</h3>
              <div className="vc-gallery-meta">
                <span>▶ {c.views} views</span>
                <span>{c.meta}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="vc-section" id="how">
        <div className="vc-reveal">
          <div className="vc-kicker">How it works</div>
          <h2 className="vc-display vc-h2">
            Chat explodes. <span className="vc-gradient-text">You get the clip.</span>
          </h2>
        </div>
        <div className="vc-steps vc-steps-4">
          {[
            { n: '01', t: 'Pick a stream', p: 'Paste a Twitch, Kick or YouTube VOD link, or open a recording on your PC. SpikeClip grabs the chat replay with it.' },
            { n: '02', t: 'Find the peaks', p: 'The app scans chat activity across the whole stream on your computer and marks every spike.' },
            { n: '03', t: 'Cut 9:16 clips', p: 'Each peak becomes a vertical clip, from 20 s before to 10 s after, with captions. Your PC does the rendering.' },
            { n: '04', t: 'Polish & post', p: 'Trim, fix captions and switch layouts in the built-in editor, then export for TikTok, Shorts and Reels.' }
          ].map((s, i) => (
            <div key={s.n} className="vc-glass vc-step vc-reveal" style={{ transitionDelay: `${i * 0.1}s` }}>
              <div className="vc-step-num">{s.n}</div>
              <h3>{s.t}</h3>
              <p>{s.p}</p>
            </div>
          ))}
        </div>
        <Pipeline />
        <HypeGraph />
      </section>

      <section className="vc-section" id="features">
        <div className="vc-reveal">
          <div className="vc-kicker">Why a desktop app</div>
          <h2 className="vc-display vc-h2">
            Your PC is <span className="vc-gradient-text">the render farm</span>
          </h2>
        </div>
        <div className="vc-features">
          {FEATURES.map((f, i) => (
            <div key={f.title} className="vc-glass vc-feature vc-reveal" style={{ transitionDelay: `${(i % 3) * 0.08}s` }}>
              <div className="ico">{f.ico}</div>
              <h3>{f.title}</h3>
              <p>{f.text}</p>
            </div>
          ))}
        </div>
      </section>

      <Pricing
        onChoose={(plan, period) => {
          if (!signedIn) {
            // Sign up first; the account page opens checkout for this plan.
            setPendingPlan(plan, period)
            return setAuth('signup')
          }
          openCheckout(plan, period).catch((e: Error) => setToast(e.message))
        }}
      />

      <section className="vc-section" id="faq">
        <div className="vc-reveal">
          <div className="vc-kicker">FAQ</div>
          <h2 className="vc-display vc-h2">
            Questions, <span className="vc-gradient-text">answered</span>
          </h2>
        </div>
        <div className="vc-faq">
          {FAQ.map((f, i) => (
            <details key={f.q} className="vc-reveal" open={i === 0}>
              <summary>{f.q}</summary>
              <p>{f.a}</p>
            </details>
          ))}
        </div>
      </section>

      <section className="vc-section">
        <div className="vc-final vc-reveal">
          <h2 className="vc-display vc-h2">Stop paying for cloud renders.</h2>
          <p className="vc-lead" style={{ margin: '0 auto 24px', color: '#ffe9f4' }}>
            Download SpikeClip, point it at a stream and let your own PC cut the clips.
          </p>
          <div className="vc-post-to" style={{ justifyContent: 'center', marginTop: 0, marginBottom: 28 }}>
            {POST_TO.map((p, i) => (
              <PlatformIcon key={p} id={p} delay={-i * 0.6} />
            ))}
          </div>
          <button
            className="vc-btn vc-btn-primary"
            style={{ background: '#fff', color: '#1b0730' }}
            onClick={() => (signedIn ? onAuthed() : setAuth('signup'))}
          >
            ⬇ Get SpikeClip for PC
          </button>
        </div>
      </section>

      <div className="vc-footer-grid">
        <div>
          <a className="vc-logo" translate="no" href="#top" style={{ fontSize: 24 }}>
            <span className="vc-logo-mark">⚡</span>
            <span>
              Spike<span className="vc-gradient-text">Clip</span>
            </span>
          </a>
          <p className="vc-note" style={{ marginTop: 12, maxWidth: 300 }}>
            AI that turns long streams into viral vertical clips.
          </p>
        </div>
        <div>
          <h4>Product</h4>
          <a href="#clips">Clips</a>
          <a href="#how">How it works</a>
          <a href="#features">Features</a>
          <a href="#pricing">Pricing</a>
          <a href="#faq">FAQ</a>
        </div>
        <div>
          <h4>Post to</h4>
          {POST_TO.map((p) => (
            <a key={p} href="#top">{PLATFORMS[p].label}</a>
          ))}
        </div>
        <div>
          <h4>Account</h4>
          <a href="#top" onClick={(e) => { e.preventDefault(); setAuth('signup') }}>Sign up</a>
          <a href="#top" onClick={(e) => { e.preventDefault(); setAuth('login') }}>Log in</a>
        </div>
      </div>
      <footer className="vc-footer">
        <span className="vc-legal-links">
          © 2026 SpikeClip
          <a href="/terms">Terms</a>
          <a href="/privacy">Privacy</a>
          <a href="/refund">Refunds</a>
        </span>
        <span>Example clips belong to their creators. Not affiliated with Rockstar Games, the streamers shown or the platforms named.</span>
      </footer>

      {(toast || notice) && (
        <div className="vc-banner" onClick={() => setToast(null)}>
          {toast || notice}
        </div>
      )}
      {auth && <AuthModal initial={auth} onClose={() => setAuth(null)} onDone={onAuthed} />}
    </div>
  )
}
