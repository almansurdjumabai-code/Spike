import './landing/landing-extra.css'
import { POST_TO, PlatformIcon } from './landing/Platforms'
import { t } from '../lib/i18n'

/** What a brand-new library shows: how it works, and where the clips go. */
export default function EmptyStart(): JSX.Element {
  const steps = [
    { n: '01', ico: '🔗', title: t('Paste a stream link'), text: t('A Twitch, Kick or YouTube VOD in the box above. Long streams are fine.') },
    { n: '02', ico: '⚡', title: t('We find the spikes'), text: t('Chat, voice and game audio are scored together to catch the moments.') },
    { n: '03', ico: '🚀', title: t('Post your clips'), text: t('Vertical, captioned and ready for every platform below.') }
  ]
  return (
    <div className="vc-empty">
      <div className="vc-empty-glow" aria-hidden />
      <p className="vc-empty-kicker">{t('Your library is empty')}</p>
      <h3 className="vc-empty-title">{t('Drop your first stream')}</h3>
      <div className="vc-empty-steps">
        {steps.map((s) => (
          <div key={s.n} className="vc-empty-step">
            <span className="vc-empty-ico" aria-hidden>
              {s.ico}
            </span>
            <span className="vc-empty-n">{s.n}</span>
            <p className="font-bold mt-2">{s.title}</p>
            <p className="text-sm text-muted mt-1 leading-relaxed">{s.text}</p>
          </div>
        ))}
      </div>
      <div className="vc-empty-platforms">
        <span>{t('Ready for')}</span>
        {POST_TO.map((p, i) => (
          <PlatformIcon key={p} id={p} delay={-i * 0.6} />
        ))}
      </div>
    </div>
  )
}
