import '@fontsource/alfa-slab-one/400.css'
import { useState, type MouseEvent } from 'react'
import { BigHeli, BigPalm, Bill, CashStack, Coin, Diamond, GoldBars, MoneyBag } from './Decor'

/** Plans: Pro (on sale) and Max (coming soon) — priced like GTA cash. */

function PalmIcon(): JSX.Element {
  return (
    <svg viewBox="0 0 64 64" aria-hidden="true">
      <path d="M30 60 C 31 46, 33 34, 38 24 L 41 25 C 37 35, 35 47, 35 60 Z" fill="#1b0730" />
      <g fill="#1b0730">
        <path d="M39 24 c8 -7 18 -6 23 1 c-8 -3 -16 -2 -23 -1z" />
        <path d="M39 24 c-7 -7 -17 -7 -22 -1 c7 -2 15 -1 22 1z" />
        <path d="M39 24 c2 -9 9 -14 17 -14 c-7 4 -13 9 -17 14z" />
        <path d="M39 24 c-3 -8 -10 -12 -16 -12 c6 4 12 8 16 12z" />
        <path d="M39 24 c6 2 11 8 12 16 c-4 -7 -8 -11 -12 -16z" />
        <circle cx="38" cy="26" r="3" />
      </g>
    </svg>
  )
}

function CarIcon(): JSX.Element {
  return (
    <svg viewBox="0 0 64 64" aria-hidden="true">
      <path
        d="M6 40 c0 -5 3 -8 8 -9 l9 -2 l8 -8 c2 -2 5 -3 8 -3 h8 c3 0 6 2 7 5 l3 7 c4 1 7 4 7 8 v4 c0 1 -1 2 -2 2 h-4 a7 7 0 0 0 -14 0 h-16 a7 7 0 0 0 -14 0 h-6 c-1 0 -2 -1 -2 -2z"
        fill="#1b0730"
      />
      <path d="M27 29 l6 -6 c1 -1 3 -2 5 -2 h6 c2 0 3 1 4 3 l2 5z" fill="#fff" opacity="0.85" />
      <circle cx="17" cy="46" r="5" fill="#1b0730" />
      <circle cx="17" cy="46" r="2" fill="#fff" />
      <circle cx="47" cy="46" r="5" fill="#1b0730" />
      <circle cx="47" cy="46" r="2" fill="#fff" />
    </svg>
  )
}

function HeliIcon(): JSX.Element {
  return (
    <svg viewBox="0 0 64 64" aria-hidden="true">
      <rect className="vc-plan-rotor" x="8" y="14" width="48" height="3.5" rx="1.75" fill="#1b0730" />
      <rect x="30" y="16" width="4" height="6" fill="#1b0730" />
      <path d="M14 30 c0 -6 6 -9 14 -9 h10 c8 0 14 5 14 12 c0 6 -5 10 -12 10 h-14 c-7 0 -12 -6 -12 -13z" fill="#1b0730" />
      <path d="M36 25 h4 c5 0 8 3 9 7 h-13z" fill="#fff" opacity="0.85" />
      <path d="M14 30 h-8 l-2 -4 h-2 v8 h12z" fill="#1b0730" />
      <path d="M20 48 h28 M24 43 v5 M44 43 v5" stroke="#1b0730" strokeWidth="3" strokeLinecap="round" />
    </svg>
  )
}

interface Plan {
  id: 'pro' | 'max'
  name: string
  tagline: string
  monthly: number
  yearly: number
  icon: JSX.Element
  iconBg: string
  cta: string
  popular?: boolean
  soon?: boolean
  perks: { text: string; hot?: boolean }[]
}

const PLANS: Plan[] = [
  {
    id: 'pro',
    name: 'Pro',
    tagline: 'For streamers and clippers who post daily',
    monthly: 14,
    yearly: 11,
    icon: <CarIcon />,
    iconBg: 'linear-gradient(135deg, #ffd56b, #ff9a52 45%, #ff4fa3)',
    cta: 'Go Pro',
    popular: true,
    perks: [
      { text: 'Unlimited clips — your PC does the work', hot: true },
      { text: '1080p export, no watermark', hot: true },
      { text: 'License key for 2 computers' },
      { text: 'Gaming / Reaction facecam layouts' },
      { text: 'Every caption style + the clip editor' },
      { text: 'All updates while subscribed' }
    ]
  },
  {
    id: 'max',
    name: 'Max',
    tagline: 'For teams and full-time clippers',
    monthly: 29,
    yearly: 23,
    icon: <HeliIcon />,
    iconBg: 'linear-gradient(135deg, #a855f7, #6d3bf2 50%, #39f0ff)',
    cta: 'Coming soon',
    soon: true,
    perks: [
      { text: 'Everything in Pro' },
      { text: 'License key for 5 computers', hot: true },
      { text: 'Up to 4K export', hot: true },
      { text: 'Batch-clip several streams at once' },
      { text: 'Priority support' },
      { text: 'Early access to new features' }
    ]
  }
]

/** Props behind each card: they peek out past its edges. */
const DECOR: Record<Plan['id'], JSX.Element> = {
  pro: (
    <>
      <span className="vc-deco d-bag"><MoneyBag /></span>
      <span className="vc-deco d-cash"><CashStack /></span>
      <span className="vc-deco d-coin3"><Coin /></span>
    </>
  ),
  max: (
    <>
      <span className="vc-deco d-heli"><BigHeli /></span>
      <span className="vc-deco d-gold"><GoldBars /></span>
      <span className="vc-deco d-diamond"><Diamond /></span>
    </>
  )
}

/** Tilt a card toward the pointer. */
function tilt(e: MouseEvent<HTMLDivElement>): void {
  const el = e.currentTarget
  const r = el.getBoundingClientRect()
  const x = (e.clientX - r.left) / r.width - 0.5
  const y = (e.clientY - r.top) / r.height - 0.5
  el.style.setProperty('--ry', `${(x * 10).toFixed(2)}deg`)
  el.style.setProperty('--rx', `${(-y * 8).toFixed(2)}deg`)
}
function untilt(e: MouseEvent<HTMLDivElement>): void {
  e.currentTarget.style.setProperty('--ry', '0deg')
  e.currentTarget.style.setProperty('--rx', '0deg')
}

export default function Pricing({
  onChoose
}: {
  onChoose: (plan: Plan['id'], period: 'monthly' | 'yearly') => void
}): JSX.Element {
  const [yearly, setYearly] = useState(false)
  return (
    <section className="vc-section vc-pricing" id="pricing">
      <div className="vc-money-rain" aria-hidden="true">
        {Array.from({ length: 14 }, (_, i) => (
          <span
            key={i}
            style={{
              left: `${(i * 7.3 + 3) % 100}%`,
              animationDelay: `${-i * 1.7}s`,
              animationDuration: `${11 + (i % 5) * 2.5}s`,
              transform: `scale(${0.6 + (i % 4) * 0.15})`
            }}
          >
            <Bill />
          </span>
        ))}
      </div>
      <div className="vc-spotlight" aria-hidden="true" />
      <div className="vc-reveal" style={{ textAlign: 'center' }}>
        <div className="vc-kicker">Pricing</div>
        <h2 className="vc-display vc-h2">
          Pick your <span className="vc-gradient-text">ride</span>
        </h2>
        <p className="vc-lead" style={{ margin: '0 auto' }}>
          One license, everything unlocked. Your PC does the rendering, so there are no cloud fees on top.
        </p>
        <div className="vc-billing" role="group" aria-label="Billing period">
          <button className={!yearly ? 'on' : ''} onClick={() => setYearly(false)}>
            Monthly
          </button>
          <button className={yearly ? 'on' : ''} onClick={() => setYearly(true)}>
            Yearly <span className="vc-save">−20%</span>
          </button>
        </div>
      </div>

      <div className="vc-plans vc-plans-2">
        {PLANS.map((p, i) => {
          const price = yearly ? p.yearly : p.monthly
          return (
            <div
              key={p.id}
              className={`vc-plan vc-plan-${p.id} vc-reveal${p.popular ? ' is-popular' : ''}`}
              style={{ transitionDelay: `${i * 0.1}s` }}
              onMouseMove={tilt}
              onMouseLeave={untilt}
            >
              <div className="vc-deco-layer" aria-hidden="true">
                {DECOR[p.id]}
              </div>
              {p.popular && <div className="vc-plan-ribbon">🔥 Most popular</div>}
              {p.soon && <div className="vc-plan-ribbon soon">🚧 Coming soon</div>}
              <div className="vc-plan-inner">
                <div className="vc-plan-head">
                  <span className="vc-plan-icon" style={{ background: p.iconBg }}>
                    {p.icon}
                  </span>
                  <div>
                    <h3 className="vc-plan-name">{p.name}</h3>
                    <p className="vc-plan-tag">{p.tagline}</p>
                  </div>
                </div>

                <div className="vc-plan-price">
                  <span className="vc-cash" key={`${p.id}-${price}`}>
                    ${price}
                  </span>
                  <span className="vc-per">
                    / month
                    {yearly && <em>billed ${price * 12}/yr</em>}
                  </span>
                </div>

                <button
                  className={`vc-btn ${p.popular ? 'vc-btn-primary' : 'vc-btn-glass'} vc-plan-cta`}
                  onClick={() => onChoose(p.id, yearly ? 'yearly' : 'monthly')}
                  disabled={p.soon}
                >
                  {p.cta}
                  {!p.soon && ' →'}
                </button>

                <ul className="vc-perks">
                  {p.perks.map((perk) => (
                    <li key={perk.text} className={perk.hot ? 'hot' : ''}>
                      <span className="vc-check" aria-hidden>
                        ✓
                      </span>
                      {perk.text}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )
        })}
      </div>
      <p className="vc-plans-note vc-reveal">
        Cancel anytime · Prices in USD · Sales tax and VAT handled at checkout · Clips render on your PC — no cloud fees
      </p>
    </section>
  )
}
