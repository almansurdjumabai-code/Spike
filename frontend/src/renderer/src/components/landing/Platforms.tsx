import type { CSSProperties } from 'react'

/** Where clips come from and where they go, as simple brand-coloured glyphs. */

export type PlatformId = 'tiktok' | 'shorts' | 'reels' | 'x' | 'facebook' | 'twitch' | 'kick' | 'youtube'

interface Platform {
  label: string
  bg: string
  glow: string
  icon: JSX.Element
}

export const PLATFORMS: Record<PlatformId, Platform> = {
  tiktok: {
    label: 'TikTok',
    bg: '#111',
    glow: 'rgb(255 0 80 / 0.55)',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.6">
        <path d="M13.2 4v10.2a3.4 3.4 0 1 1-3.4-3.4" stroke="#25f4ee" transform="translate(-0.8 -0.6)" />
        <path d="M13.2 4c.4 2.4 2.1 4 4.6 4.2" stroke="#25f4ee" transform="translate(-0.8 -0.6)" />
        <path d="M13.2 4v10.2a3.4 3.4 0 1 1-3.4-3.4" stroke="#fe2c55" transform="translate(0.8 0.6)" />
        <path d="M13.2 4c.4 2.4 2.1 4 4.6 4.2" stroke="#fe2c55" transform="translate(0.8 0.6)" />
        <path d="M13.2 4v10.2a3.4 3.4 0 1 1-3.4-3.4" stroke="#fff" />
        <path d="M13.2 4c.4 2.4 2.1 4 4.6 4.2" stroke="#fff" />
      </svg>
    )
  },
  shorts: {
    label: 'YouTube Shorts',
    bg: 'linear-gradient(135deg, #ff3b3b, #d90000)',
    glow: 'rgb(255 40 40 / 0.6)',
    icon: (
      <svg viewBox="0 0 24 24">
        <path
          d="M15.8 3.6a3.6 3.6 0 0 1 3.4 6.2l-1.5.8 1.3.6a3.6 3.6 0 0 1-.2 6.6l-7.6 3.6a3.6 3.6 0 0 1-3.4-6.2l1.5-.8-1.3-.6a3.6 3.6 0 0 1 .2-6.6Z"
          fill="#fff"
        />
        <path d="M10.4 9.2v5.6l4.6-2.8Z" fill="#e00" />
      </svg>
    )
  },
  reels: {
    label: 'Instagram Reels',
    bg: 'radial-gradient(circle at 30% 110%, #ffd600, #ff7a00 25%, #ff0069 55%, #d300c5 75%, #7638fa)',
    glow: 'rgb(255 0 105 / 0.55)',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2">
        <rect x="4" y="4" width="16" height="16" rx="5" />
        <circle cx="12" cy="12" r="3.6" />
        <circle cx="16.8" cy="7.2" r="1" fill="#fff" stroke="none" />
      </svg>
    )
  },
  x: {
    label: 'X',
    bg: '#000',
    glow: 'rgb(255 255 255 / 0.3)',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.4" strokeLinecap="round">
        <path d="M5 5l14 14M19 5L5 19" />
      </svg>
    )
  },
  facebook: {
    label: 'Facebook',
    bg: '#1877f2',
    glow: 'rgb(24 119 242 / 0.6)',
    icon: (
      <svg viewBox="0 0 24 24">
        <path d="M13.4 21v-7.2h2.5l.4-2.9h-2.9V9.1c0-.8.3-1.4 1.4-1.4h1.6V5.1a20 20 0 0 0-2.3-.1c-2.3 0-3.8 1.4-3.8 3.9v2h-2.5v2.9h2.5V21Z" fill="#fff" />
      </svg>
    )
  },
  twitch: {
    label: 'Twitch',
    bg: '#9146ff',
    glow: 'rgb(145 70 255 / 0.6)',
    icon: (
      <svg viewBox="0 0 24 24">
        <path d="M6 3 4 7v12h4v2h2.5l2-2H16l4-4V3Zm12 11-2.5 2.5H12l-2 2v-2H7V5h11Z" fill="#fff" />
        <path d="M11 8h1.8v4.4H11Zm4 0h1.8v4.4H15Z" fill="#fff" />
      </svg>
    )
  },
  kick: {
    label: 'Kick',
    bg: '#0b0e0f',
    glow: 'rgb(83 252 24 / 0.5)',
    icon: (
      <svg viewBox="0 0 24 24">
        <path d="M5 4h4v5h2V7h2V5h6v5h-2v2h-2v1h2v2h2v5h-6v-2h-2v-2h-2v4H5Z" fill="#53fc18" />
      </svg>
    )
  },
  youtube: {
    label: 'YouTube',
    bg: '#ff0000',
    glow: 'rgb(255 0 0 / 0.55)',
    icon: (
      <svg viewBox="0 0 24 24">
        <rect x="2.5" y="5.5" width="19" height="13" rx="4" fill="#fff" />
        <path d="M10 9v6l5.2-3Z" fill="#f00" />
      </svg>
    )
  }
}

export function PlatformIcon({ id, delay = 0 }: { id: PlatformId; delay?: number }): JSX.Element {
  const p = PLATFORMS[id]
  return (
    <span
      className="vc-pf"
      data-label={p.label}
      title={p.label}
      style={{ '--pf-bg': p.bg, '--pf-glow': p.glow, '--pf-delay': `${delay}s` } as CSSProperties}
    >
      {p.icon}
    </span>
  )
}

export const POST_TO: PlatformId[] = ['tiktok', 'shorts', 'reels', 'x', 'facebook']
export const CLIP_FROM: PlatformId[] = ['twitch', 'kick', 'youtube']
