/** Drawn props that peek out from behind the pricing cards. Original art. */

export function BigPalm(): JSX.Element {
  return (
    <svg viewBox="0 0 200 260" aria-hidden="true">
      <defs>
        <linearGradient id="dc-palm" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#5effc1" />
          <stop offset="1" stopColor="#1a8f6c" />
        </linearGradient>
        <linearGradient id="dc-trunk" x1="0" x2="1">
          <stop offset="0" stopColor="#8a5a3c" />
          <stop offset="1" stopColor="#5a3524" />
        </linearGradient>
      </defs>
      <path d="M88 260 C 92 200, 100 140, 118 92 L 128 95 C 112 142, 104 200, 104 260 Z" fill="url(#dc-trunk)" />
      {[110, 130, 150, 170, 190, 210, 230].map((y) => (
        <path key={y} d={`M${92 + (260 - y) * 0.12} ${y} l14 -3`} stroke="#3e2418" strokeWidth="2" opacity="0.6" />
      ))}
      <g fill="url(#dc-palm)">
        <path d="M122 92 c26 -22 60 -18 76 6 c-26 -10 -52 -8 -76 -6z" />
        <path d="M122 92 c-24 -22 -58 -22 -74 -2 c24 -8 50 -4 74 2z" />
        <path d="M122 92 c6 -30 30 -46 58 -46 c-24 12 -44 28 -58 46z" />
        <path d="M122 92 c-10 -28 -34 -40 -54 -40 c22 12 40 26 54 40z" />
        <path d="M122 92 c22 6 38 26 40 52 c-12 -22 -26 -36 -40 -52z" />
        <path d="M122 92 c-20 8 -34 28 -34 52 c10 -22 22 -38 34 -52z" />
      </g>
      <circle cx="118" cy="98" r="7" fill="#6b3d1f" />
      <circle cx="128" cy="100" r="6" fill="#7a4626" />
    </svg>
  )
}

export function MoneyBag(): JSX.Element {
  return (
    <svg viewBox="0 0 160 180" aria-hidden="true">
      <defs>
        <radialGradient id="dc-bag" cx="0.4" cy="0.35" r="0.75">
          <stop offset="0" stopColor="#f3e7c9" />
          <stop offset="0.7" stopColor="#c9b48a" />
          <stop offset="1" stopColor="#8f7a52" />
        </radialGradient>
      </defs>
      <path d="M58 40 C 50 30, 52 18, 62 14 C 72 22, 88 22, 98 14 C 108 18, 110 30, 102 40 Z" fill="#b39a6a" />
      <path d="M60 44 C 20 70, 8 110, 22 142 C 34 168, 126 168, 138 142 C 152 110, 140 70, 100 44 Z" fill="url(#dc-bag)" stroke="#1b0730" strokeWidth="4" />
      <path d="M56 42 h48" stroke="#5a3a1a" strokeWidth="8" strokeLinecap="round" />
      <text
        x="80"
        y="128"
        textAnchor="middle"
        fontFamily="'Alfa Slab One', serif"
        fontSize="64"
        fill="#72d35a"
        stroke="#000"
        strokeWidth="4"
        paintOrder="stroke"
      >
        $
      </text>
    </svg>
  )
}

export function CashStack(): JSX.Element {
  return (
    <svg viewBox="0 0 170 110" aria-hidden="true">
      {[0, 1, 2, 3].map((i) => (
        <g key={i} transform={`translate(${i * 3} ${70 - i * 14})`}>
          <rect x="6" y="0" width="150" height="34" rx="4" fill="#5fae4a" stroke="#1b0730" strokeWidth="3" />
          <rect x="16" y="6" width="130" height="22" rx="3" fill="none" stroke="#2f6b25" strokeWidth="2" />
          <circle cx="81" cy="17" r="9" fill="#3f8a33" />
          <text x="81" y="22" textAnchor="middle" fontFamily="'Alfa Slab One', serif" fontSize="14" fill="#cdf5c0">
            $
          </text>
        </g>
      ))}
      <rect x="70" y="20" width="24" height="88" fill="#f2e3b3" stroke="#1b0730" strokeWidth="3" />
    </svg>
  )
}

export function Coin({ size = 1 }: { size?: number }): JSX.Element {
  return (
    <svg viewBox="0 0 60 60" style={{ transform: `scale(${size})` }} aria-hidden="true">
      <circle cx="30" cy="30" r="26" fill="#ffd56b" stroke="#1b0730" strokeWidth="4" />
      <circle cx="30" cy="30" r="18" fill="none" stroke="#c8961f" strokeWidth="3" />
      <text x="30" y="40" textAnchor="middle" fontFamily="'Alfa Slab One', serif" fontSize="26" fill="#a0700c">
        $
      </text>
    </svg>
  )
}

export function GoldBars(): JSX.Element {
  const bar = (x: number, y: number): JSX.Element => (
    <g key={`${x}-${y}`} transform={`translate(${x} ${y})`}>
      <path d="M10 0 h50 l10 24 h-70 z" fill="#ffd56b" stroke="#1b0730" strokeWidth="3" />
      <path d="M14 4 h42" stroke="#fff3c4" strokeWidth="3" strokeLinecap="round" />
    </g>
  )
  return (
    <svg viewBox="0 0 170 90" aria-hidden="true">
      {bar(0, 60)}
      {bar(76, 60)}
      {bar(38, 34)}
      {bar(76, 8)}
    </svg>
  )
}

export function Diamond(): JSX.Element {
  return (
    <svg viewBox="0 0 80 70" aria-hidden="true">
      <path d="M16 4 h48 l14 20 l-38 42 l-38 -42 z" fill="#7df9ff" stroke="#1b0730" strokeWidth="3" />
      <path d="M2 24 h76 M16 4 l12 20 l12 -20 l12 20 l12 -20 M28 24 l12 42 l12 -42" fill="none" stroke="#1b6f8a" strokeWidth="2" />
      <path d="M22 8 l6 10" stroke="#fff" strokeWidth="3" strokeLinecap="round" />
    </svg>
  )
}

export function BigHeli(): JSX.Element {
  return (
    <svg viewBox="0 0 220 120" aria-hidden="true">
      <rect className="vc-plan-rotor" x="20" y="6" width="180" height="6" rx="3" fill="#1b0730" />
      <rect x="104" y="10" width="10" height="16" fill="#1b0730" />
      <path d="M60 52 c0 -16 18 -26 42 -26 h28 c26 0 44 16 44 36 c0 18 -16 30 -36 30 h-40 c-22 0 -38 -18 -38 -40z" fill="#a855f7" stroke="#1b0730" strokeWidth="4" />
      <path d="M128 34 h10 c16 0 26 10 30 22 h-40z" fill="#c9f3ff" stroke="#1b0730" strokeWidth="3" />
      <path d="M60 52 h-44 l-8 -14 h-6 v26 h58z" fill="#7a3fd0" stroke="#1b0730" strokeWidth="4" />
      <circle className="vc-beacon" cx="6" cy="46" r="5" fill="#ff2147" />
      <path d="M78 106 h88 M92 92 v14 M150 92 v14" stroke="#1b0730" strokeWidth="5" strokeLinecap="round" />
    </svg>
  )
}

export function Bill(): JSX.Element {
  return (
    <svg viewBox="0 0 90 44" aria-hidden="true">
      <rect x="2" y="2" width="86" height="40" rx="5" fill="#5fae4a" stroke="#1b0730" strokeWidth="3" />
      <rect x="9" y="8" width="72" height="28" rx="3" fill="none" stroke="#2f6b25" strokeWidth="2" />
      <circle cx="45" cy="22" r="10" fill="#3f8a33" />
      <text x="45" y="28" textAnchor="middle" fontFamily="'Alfa Slab One', serif" fontSize="16" fill="#cdf5c0">
        $
      </text>
    </svg>
  )
}
