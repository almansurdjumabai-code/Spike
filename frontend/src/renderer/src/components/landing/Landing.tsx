import '@fontsource/anton/400.css'
import '@fontsource-variable/inter'
import './landing.css'
import { useEffect, useRef, useState } from 'react'
import AuthModal, { type AuthTab } from './AuthModal'
import ClipCard, { type ClipSpec } from './ClipCard'
import ViceScene from './ViceScene'

/** The public welcome page of the web app: who SpikeClip is for, what the
 *  clips look like, and the way in (sign up / log in). */

const HERO: ClipSpec[] = [
  {
    layout: 'bubble', handle: 'turbotrey', initials: 'TT', accent: '#ff9a52', highlight: '#ffd56b',
    views: '2.4M', tag: 'Bubble cam', caption: 'NAH HE REALLY JUST DID THAT 😭',
    sky: ['#3b1d8f', '#ff4fa3', '#ffb36b'], durationS: 8
  },
  {
    layout: 'cam-top', handle: 'novarush', initials: 'NR', accent: '#ff4fa3', highlight: '#5effc1',
    views: '5.1M', tag: 'Facecam top', caption: 'CHAT WE ARE SO BACK 🔥',
    sky: ['#140838', '#7a2fb5', '#ff7a9c'], durationS: 10
  },
  {
    layout: 'full', handle: 'bigdeuce', initials: 'BD', accent: '#39f0ff', highlight: '#ffd56b',
    views: '980K', tag: 'Full action', caption: 'BRO HIT THE 360 ON A JETSKI',
    sky: ['#2a6bd1', '#a855f7', '#ffd56b'], durationS: 7
  }
]

const TEMPLATES: { spec: ClipSpec; title: string; text: string }[] = [
  { spec: { ...HERO[1], handle: 'kingkash', initials: 'KK' }, title: 'Facecam Top', text: 'Reaction on top, the chaos below. The streamer stays centred, tracked shot by shot.' },
  { spec: HERO[0], title: 'Bubble Cam', text: 'Full-screen gameplay with a round cam that never covers the action.' },
  { spec: HERO[2], title: 'Full Action', text: 'Pure gameplay, reframed to 9:16 so the car, the boat or the chase stays in frame.' },
  {
    spec: {
      layout: 'cam-top', handle: 'sunsetsav', initials: 'SS', accent: '#ffd56b', highlight: '#ff4fa3',
      views: '1.3M', tag: 'Karaoke captions', caption: 'THIS IS NOT REAL LIFE 💀', sky: ['#1d0b4a', '#c03ab8', '#ff9a52'], durationS: 9
    },
    title: 'Karaoke Captions',
    text: 'Word-by-word captions that pop on the beat, in the style Shorts and TikTok reward.'
  }
]

const MARQUEE = ['W chat', 'Clip it', 'No shot', 'Goated', 'Run it back', 'W streamer', 'Spike detected', 'He is cooked', 'Vice City nights']

const FEATURES = [
  { ico: '⚡', title: 'Spike detection', text: 'Chat floods, voice peaks, kills, crashes and laughs scored together, so the clip starts before the moment, not after.' },
  { ico: '🎮', title: 'Built for gameplay', text: 'Reads what the game shows on screen and hears what it sounds like: chases, wrecks, wins and fails.' },
  { ico: '📱', title: 'Auto 9:16 reframe', text: 'Facecam and game split, tracked and composed for Shorts, Reels and TikTok without touching an editor.' },
  { ico: '💬', title: 'Captions that pop', text: 'Word-synced karaoke captions, titles, descriptions and hashtags written for each clip.' },
  { ico: '🔗', title: 'Paste a link', text: 'Twitch, Kick or YouTube VOD. Drop the link, get a stack of ready-to-post clips back.' },
  { ico: '🚀', title: 'Post everywhere', text: 'Send clips to YouTube and other platforms straight from the studio when you are ready.' }
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

function HypeGraph(): JSX.Element {
  // Chat messages per second over a 3-hour stream, with the spikes SpikeClip cuts.
  const pts = [8, 9, 7, 10, 12, 9, 11, 30, 64, 22, 12, 10, 11, 9, 13, 15, 12, 41, 88, 35, 14, 12, 10, 11, 16, 13, 11, 52, 70, 26, 12, 10, 9, 12]
  const w = 1100
  const h = 260
  const step = w / (pts.length - 1)
  const y = (v: number): number => h - 20 - (v / 95) * (h - 50)
  const d = pts.map((v, i) => `${i ? 'L' : 'M'}${(i * step).toFixed(1)} ${y(v).toFixed(1)}`).join(' ')
  const peaks = [
    { i: 8, label: 'COP CHASE' },
    { i: 18, label: 'JETSKI 360' },
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
            <rect x={p.i * step - 62} y={y(pts[p.i]) - 46} width="124" height="30" rx="15" fill="#ff4fa3" />
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

export default function Landing({ notice, onAuthed }: { notice: string | null; onAuthed: () => void }): JSX.Element {
  const [auth, setAuth] = useState<AuthTab | null>(null)
  const [scrolled, setScrolled] = useState(false)
  const templates = useRef<HTMLDivElement>(null)
  useReveal()

  useEffect(() => {
    const onScroll = (): void => setScrolled(window.scrollY > 20)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  // The app's own body styles are for the studio; the landing page scrolls.
  useEffect(() => {
    const prev = document.body.style.overflow
    document.body.style.overflow = 'auto'
    return () => {
      document.body.style.overflow = prev
    }
  }, [])

  return (
    <div className="vc">
      <nav className={`vc-nav${scrolled ? ' is-scrolled' : ''}`}>
        <a className="vc-logo" href="#top">
          <span className="vc-logo-mark">⚡</span>
          <span>
            Spike<span className="vc-gradient-text">Clip</span>
          </span>
        </a>
        <div className="vc-nav-links">
          <a href="#templates">Templates</a>
          <a href="#how">How it works</a>
          <a href="#features">Features</a>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="vc-btn vc-btn-glass vc-btn-sm" onClick={() => setAuth('login')}>
            Log in
          </button>
          <button className="vc-btn vc-btn-primary vc-btn-sm" onClick={() => setAuth('signup')}>
            Sign up
          </button>
        </div>
      </nav>

      <header className="vc-hero" id="top">
        <ViceScene />
        <div className="vc-hero-inner">
          <div>
            <span className="vc-eyebrow">
              <span className="vc-live-dot">LIVE</span>
              AI clipping for gaming streams
            </span>
            <h1 className="vc-display vc-hero-title">
              <span className="line"><span>Every stream</span></span>
              <span className="line"><span>has a</span></span>
              <span className="line"><span className="vc-gradient-text">viral spike.</span></span>
            </h1>
            <p className="vc-hero-sub">
              SpikeClip watches the whole VOD, catches the moments chat loses it, and cuts them into
              captioned 9:16 clips ready for Shorts, Reels and TikTok. Car chases, jetski stunts,
              rage quits, the W spam. All of it.
            </p>
            <div className="vc-hero-ctas">
              <button className="vc-btn vc-btn-primary" onClick={() => setAuth('signup')}>
                Start clipping free →
              </button>
              <button className="vc-btn vc-btn-glass" onClick={() => templates.current?.scrollIntoView({ behavior: 'smooth' })}>
                ▶ See templates
              </button>
            </div>
            <div className="vc-hero-proof">
              <div className="vc-proof"><b>40+</b><span>clips per stream</span></div>
              <div className="vc-proof"><b>9:16</b><span>auto reframe</span></div>
              <div className="vc-proof"><b>1 link</b><span>Twitch · Kick · YouTube</span></div>
            </div>
          </div>
          <div className="vc-hero-stage">
            {HERO.map((s, i) => (
              <div key={s.handle} className={`vc-stage-card c${i}`}>
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

      <section className="vc-section" id="templates" ref={templates}>
        <div className="vc-reveal">
          <div className="vc-kicker">Templates</div>
          <h2 className="vc-display vc-h2">
            Clips that look <span className="vc-gradient-text">straight off FYP</span>
          </h2>
          <p className="vc-lead">Pick a layout once. Every moment SpikeClip finds comes out in it, captioned and ready to post.</p>
        </div>
        <div className="vc-templates">
          {TEMPLATES.map((t, i) => (
            <div key={t.title} className="vc-template vc-reveal" style={{ transitionDelay: `${i * 0.08}s` }}>
              <ClipCard spec={t.spec} />
              <h3>{t.title}</h3>
              <p>{t.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="vc-section" id="how">
        <div className="vc-reveal">
          <div className="vc-kicker">How it works</div>
          <h2 className="vc-display vc-h2">
            Stream tonight. <span className="vc-gradient-text">Post tomorrow.</span>
          </h2>
        </div>
        <div className="vc-steps">
          {[
            { n: '01', t: 'Drop the VOD', p: 'Paste a Twitch, Kick or YouTube link. An 8-hour stream is fine.' },
            { n: '02', t: 'AI finds the spikes', p: 'Chat, voice, game audio and what is on screen are scored together to find the peaks.' },
            { n: '03', t: 'Post the bangers', p: 'Review, tweak captions in the editor, export or publish straight to your channels.' }
          ].map((s, i) => (
            <div key={s.n} className="vc-glass vc-step vc-reveal" style={{ transitionDelay: `${i * 0.1}s` }}>
              <div className="vc-step-num">{s.n}</div>
              <h3>{s.t}</h3>
              <p>{s.p}</p>
            </div>
          ))}
        </div>
        <HypeGraph />
      </section>

      <section className="vc-section" id="features">
        <div className="vc-reveal">
          <div className="vc-kicker">Features</div>
          <h2 className="vc-display vc-h2">
            Your editor <span className="vc-gradient-text">never sleeps</span>
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

      <section className="vc-section">
        <div className="vc-final vc-reveal">
          <h2 className="vc-display vc-h2">Stop scrubbing VODs.</h2>
          <p className="vc-lead" style={{ margin: '0 auto 28px', color: '#ffe9f4' }}>
            Make an account, paste your first stream and watch the clips stack up.
          </p>
          <button className="vc-btn vc-btn-primary" style={{ background: '#fff', color: '#1b0730' }} onClick={() => setAuth('signup')}>
            Create free account →
          </button>
        </div>
      </section>

      <footer className="vc-footer">
        <span>© 2026 SpikeClip</span>
        <span>Templates show fictional creators. Not affiliated with any game publisher or streamer.</span>
      </footer>

      {notice && <div className="vc-banner">{notice}</div>}
      {auth && <AuthModal initial={auth} onClose={() => setAuth(null)} onDone={onAuthed} />}
    </div>
  )
}
