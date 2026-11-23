import '@fontsource/anton/400.css'
import '@fontsource-variable/inter'
import './landing.css'
import './landing-extra.css'
import type { ReactNode } from 'react'

/** Terms, Privacy and Refund pages for the web app.
 *
 *  The payment provider (Whop, and Paddle if it is switched on) reviews these before switching payments
 *  on. Fill in LEGAL below with the seller's real details, and have the text
 *  checked by someone qualified: it is a sensible starting point, not legal
 *  advice.
 */
export const LEGAL = {
  product: 'SpikeClip',
  // The person or registered business that sells SpikeClip (e.g. your IP in Kazakhstan).
  seller: 'Djumabai Almansur Ardakovich',
  country: 'the Republic of Kazakhstan',
  email: 'almansurdjumabai@gmail.com', // support address shown on these pages
  updated: 'November 20, 2026'
}

export type LegalKind = 'terms' | 'privacy' | 'refund'

const contact = (): ReactNode =>
  LEGAL.email ? (
    <a className="vc-link" href={`mailto:${LEGAL.email}`}>
      {LEGAL.email}
    </a>
  ) : (
    'the support address on your Whop receipt'
  )

function Terms(): JSX.Element {
  return (
    <>
      <p>
        These terms govern your use of {LEGAL.product}, a desktop application for Windows and macOS that finds the
        moments chat reacts to in a stream and turns them into short vertical clips on your own computer, together
        with the website and account services that sell and activate it. {LEGAL.product} is operated by {LEGAL.seller}
        ("we", "us"). By creating an account, buying a license or using the app you agree to these terms.
      </p>
      <h2>1. Your account</h2>
      <p>
        You must be at least 16 and give accurate information. Keep your password safe; you are responsible for what
        happens under your account. We may suspend accounts that break these terms.
      </p>
      <h2>2. Your content</h2>
      <p>
        The app processes videos on your computer; we do not receive, store or process your videos or clips. You may
        only clip videos you own or have permission to use, and you keep all rights to your content and to the clips
        made from it. Do not use {LEGAL.product} for content that is illegal, infringes anyone's rights, or breaks the
        rules of the platform it came from.
      </p>
      <h2>3. Plans and payment</h2>
      <p>
        {LEGAL.product} is sold as paid subscriptions with the features shown on our pricing page. A paid
        plan comes with a license key that unlocks the app on the number of computers your plan allows; keys are
        personal and may not be shared or resold. Payments are processed by Whop (whop.com): you pay on Whop's checkout, and your card details go to Whop,
        never to us. Subscriptions renew
        automatically each month or year until cancelled; you can cancel at any time and keep access until the end of
        the paid period. Prices may change with at least 30 days' notice before your next renewal.
      </p>
      <h2>4. Fair use and availability</h2>
      <p>
        Plan limits apply per calendar month. The app checks your license with our servers from time to time and keeps
        working offline for a limited period. How fast clips are made depends on your computer. Clips are produced
        automatically, so their selection may contain mistakes. We work to keep our license servers
        available but do not guarantee they will be uninterrupted.
      </p>
      <h2>5. Liability</h2>
      <p>
        The service is provided "as is". To the extent the law allows, our total liability is limited to the amount you
        paid us in the 12 months before the claim. Nothing here limits rights you have as a consumer under applicable law.
      </p>
      <h2>6. Ending</h2>
      <p>
        You can stop using the service and delete your account at any time by contacting us. We may end or change the
        service with reasonable notice.
      </p>
      <h2>7. Law and contact</h2>
      <p>
        These terms are governed by the laws of {LEGAL.country}, without affecting mandatory consumer protections where
        you live. Questions: {contact()}.
      </p>
    </>
  )
}

function Privacy(): JSX.Element {
  return (
    <>
      <p>
        This policy explains what {LEGAL.product}, operated by {LEGAL.seller}, collects and why. We collect as little as
        we can and never sell your data.
      </p>
      <h2>What we collect</h2>
      <ul>
        <li>
          <b>Account:</b> your email, display name and a hashed password (we never store it in plain text).
        </li>
        <li>
          <b>License:</b> your license key, your plan and the computers you activated it on (a one-way hash of a
          random device id, the device name you see in your account, the platform and the app version).
        </li>
        <li>
          <b>Billing:</b> handled by Whop. We receive your email, your plan, the membership status and a Whop
          membership ID — never your card details.
        </li>
        <li>
          <b>Technical:</b> your sign-in session is kept in your browser's local storage. We do not use advertising or
          tracking cookies.
        </li>
      </ul>
      <h2>Why</h2>
      <p>
        To sell and activate the app, manage your subscription and support you. Your videos and clips are processed on
        your own computer and are never sent to us. If you choose to use a cloud AI provider inside the app, the data
        you send goes to that provider under your own account and its terms.
      </p>
      <h2>How long</h2>
      <p>
        We keep your account and license records while your account exists. When you delete your account, we delete
        your data within 30 days, except what the law requires us to keep (for example, records of payments).
      </p>
      <h2>Your rights</h2>
      <p>
        You can ask to see, correct, export or delete your data, or object to how we use it. Write to {contact()}. If
        you are in the EU/UK you can also complain to your data protection authority.
      </p>
      <h2>Payments</h2>
      <p>
        Whop processes payments under its own privacy policy:{' '}
        <a className="vc-link" href="https://whop.com/privacy" target="_blank" rel="noreferrer">
          whop.com/privacy
        </a>
        .
      </p>
    </>
  )
}

function Refund(): JSX.Element {
  return (
    <>
      <p>We want you to be happy with {LEGAL.product}. If you are not, you can get your money back.</p>
      <h2>14-day money-back guarantee</h2>
      <p>
        If you are not satisfied, request a full refund within 14 days of your first payment for a subscription, or of
        a renewal charge, and we will refund it — no questions asked.
      </p>
      <h2>How to request a refund</h2>
      <p>
        Orders are processed by Whop. Request a refund from your Whop account at{' '}
        <a className="vc-link" href="https://whop.com/orders" target="_blank" rel="noreferrer">
          whop.com
        </a>{' '}
        (your orders and memberships), or write to {contact()}. Refunds go back to the original
        payment method, usually within 5–10 business days.
      </p>
      <h2>Cancelling</h2>
      <p>
        You can cancel any time from your Whop account (your memberships at whop.com). You keep your plan until the end of the period
        you paid for, and you will not be charged again.
      </p>
    </>
  )
}

const TITLES: Record<LegalKind, string> = {
  terms: 'Terms of Service',
  privacy: 'Privacy Policy',
  refund: 'Refund Policy'
}

export default function Legal({ kind }: { kind: LegalKind }): JSX.Element {
  return (
    <div className="vc">
      <nav className="vc-nav is-scrolled">
        <a className="vc-logo" translate="no" href="/">
          <span className="vc-logo-mark">⚡</span>
          <span>
            Spike<span className="vc-gradient-text">Clip</span>
          </span>
        </a>
        <div className="vc-nav-links">
          <a href="/terms">Terms</a>
          <a href="/privacy">Privacy</a>
          <a href="/refund">Refunds</a>
        </div>
        <a className="vc-btn vc-btn-glass vc-btn-sm" href="/">
          ← Back
        </a>
      </nav>
      <main className="vc-section vc-legal">
        <div className="vc-kicker">Legal</div>
        <h1 className="vc-display vc-h2">
          <span className="vc-gradient-text">{TITLES[kind]}</span>
        </h1>
        <p className="vc-note">Last updated: {LEGAL.updated}</p>
        <article className="vc-glass vc-legal-body">
          {kind === 'terms' ? <Terms /> : kind === 'privacy' ? <Privacy /> : <Refund />}
        </article>
      </main>
    </div>
  )
}
