/** Small looping illustrations for the four "How it works" cards and line
 *  icons for the feature cards. Pure CSS animation (landing-extra.css,
 *  "how it works art"), no images. */

export function StepArt({ n }: { n: number }): React.JSX.Element {
  if (n === 0)
    return (
      <div className="vc-art vc-art-link" aria-hidden="true">
        <span className="vc-art-url">
          <i>twitch.tv/videos/</i>
          <b>2291847756</b>
        </span>
        <span className="vc-art-go">GO</span>
      </div>
    )
  if (n === 1)
    return (
      <div className="vc-art vc-art-scan" aria-hidden="true">
        {Array.from({ length: 22 }, (_, i) => (
          <i key={i} style={{ height: `${[18, 22, 16, 26, 20, 30, 24, 90, 60, 28, 18, 22, 20, 26, 74, 96, 40, 22, 18, 24, 20, 16][i]}%` }} className={[7, 8, 14, 15].includes(i) ? 'pk' : ''} />
        ))}
        <span className="vc-art-sweep" />
      </div>
    )
  if (n === 2)
    return (
      <div className="vc-art vc-art-crop" aria-hidden="true">
        <span className="vc-art-wide">
          <span className="vc-art-face" />
          <span className="vc-art-game" />
        </span>
        <span className="vc-art-frame">
          <em>9:16</em>
        </span>
      </div>
    )
  return (
    <div className="vc-art vc-art-post" aria-hidden="true">
      <span className="vc-art-bar">
        <i />
      </span>
      <span className="vc-art-dests">
        <b style={{ background: '#111' }}>TikTok</b>
        <b style={{ background: '#e62117' }}>Shorts</b>
        <b style={{ background: 'linear-gradient(45deg,#f9a03c,#e1306c,#833ab4)' }}>Reels</b>
      </span>
    </div>
  )
}

const P = { fill: 'none', stroke: 'currentColor', strokeWidth: 2, strokeLinecap: 'round', strokeLinejoin: 'round' } as const

/** Line icons for the feature cards, by index in FEATURES. */
export function FeatureIcon({ i }: { i: number }): React.JSX.Element {
  const paths = [
    // no server bills: a server with a slash
    <>
      <rect x="5" y="4" width="14" height="6" rx="1.5" {...P} />
      <rect x="5" y="14" width="14" height="6" rx="1.5" {...P} />
      <path d="M8 7h.01M8 17h.01M3 21L21 3" {...P} />
    </>,
    // fast on your hardware: a chip with a bolt
    <>
      <rect x="6" y="6" width="12" height="12" rx="2" {...P} />
      <path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3M12.5 8.5L10.5 12h3l-2 3.5" {...P} />
    </>,
    // you control the limits: sliders
    <>
      <path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0" {...P} />
      <circle cx="16" cy="6" r="2" {...P} />
      <circle cx="10" cy="12" r="2" {...P} />
      <circle cx="18" cy="18" r="2" {...P} />
    </>,
    // chat-spike detection: a spike on a line
    <path d="M2 17h5l2-3 3 7 4-18 3 14h3" {...P} />,
    // vertical 9:16, captioned: a phone with caption lines
    <>
      <rect x="7" y="2" width="10" height="20" rx="2" {...P} />
      <path d="M9.5 15h5M10.5 17.5h3" {...P} />
    </>,
    // footage stays yours: a lock
    <>
      <rect x="5" y="11" width="14" height="10" rx="2" {...P} />
      <path d="M8 11V8a4 4 0 0 1 8 0v3M12 15v2" {...P} />
    </>
  ]
  return (
    <svg viewBox="0 0 24 24" width="26" height="26" aria-hidden="true">
      {paths[i % paths.length]}
    </svg>
  )
}
