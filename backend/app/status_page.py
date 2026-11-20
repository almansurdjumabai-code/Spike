"""The page someone sees when they open the API's address in a browser:
a Vice-sunset status card instead of raw JSON. Self-contained (no assets)."""

STATUS_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SpikeClip API — online</title>
<style>
  :root { --pink:#ff4fa3; --gold:#ffd56b; --orange:#ff9a52; --violet:#a855f7; --cyan:#39f0ff; --ink:#fff6fb; }
  * { box-sizing: border-box; margin: 0; }
  body {
    min-height: 100vh; display: grid; place-items: center; overflow: hidden;
    font-family: Inter, "Segoe UI", system-ui, sans-serif; color: var(--ink);
    background: linear-gradient(#140838 0%, #4b1fa8 35%, #c03ab8 58%, #ff5f8f 70%, #ffa25a 78%, #140838 79%, #0d0722 100%);
  }
  .sun {
    position: fixed; left: 50%; top: 52%; width: 520px; height: 520px; margin: -260px 0 0 -260px; border-radius: 50%;
    background: linear-gradient(#ffe48a, #ff9a52 55%, #ff3d8b);
    -webkit-mask: linear-gradient(#000 0 60%, transparent 60% 63%, #000 63% 70%, transparent 70% 74%, #000 74% 80%, transparent 80% 85%, #000 85% 89%, transparent 89% 95%, #000 95%);
    mask: linear-gradient(#000 0 60%, transparent 60% 63%, #000 63% 70%, transparent 70% 74%, #000 74% 80%, transparent 80% 85%, #000 85% 89%, transparent 89% 95%, #000 95%);
    filter: drop-shadow(0 0 60px rgba(255,79,163,.6)); animation: rise 8s ease-in-out infinite alternate;
  }
  @keyframes rise { to { transform: translateY(-14px) scale(1.03); } }
  .grid {
    position: fixed; left: -50%; right: -50%; bottom: 0; height: 21%;
    background:
      repeating-linear-gradient(90deg, rgba(255,79,163,.55) 0 2px, transparent 2px 80px),
      repeating-linear-gradient(0deg, rgba(255,79,163,.55) 0 2px, transparent 2px 40px);
    transform: perspective(300px) rotateX(60deg); transform-origin: top; animation: drive 1.2s linear infinite;
  }
  @keyframes drive { to { background-position: 0 0, 0 40px; } }
  .palm { position: fixed; bottom: 18%; width: 180px; fill: #16062a; }
  .palm.l { left: 4%; } .palm.r { right: 4%; transform: scaleX(-1); }
  .card {
    position: relative; z-index: 2; width: min(560px, calc(100% - 32px)); padding: 34px 30px; border-radius: 28px;
    background: linear-gradient(160deg, rgba(255,255,255,.12), rgba(255,255,255,.03)), rgba(13,7,34,.72);
    border: 1px solid rgba(255,255,255,.16); backdrop-filter: blur(16px);
    box-shadow: 0 40px 120px -30px rgba(0,0,0,.9), 0 0 80px -20px rgba(255,79,163,.6);
  }
  .logo { display: flex; align-items: center; gap: 12px; font: 900 30px/1 Impact, "Anton", sans-serif; letter-spacing: .02em; text-transform: uppercase; }
  .mark { width: 42px; height: 42px; border-radius: 13px; display: grid; place-items: center; font-size: 22px;
          background: linear-gradient(135deg, var(--orange), var(--pink) 55%, #6d3bf2); box-shadow: 0 0 24px rgba(255,79,163,.6); }
  .clip { background: linear-gradient(100deg, var(--gold), var(--orange), var(--pink), var(--violet)); -webkit-background-clip: text; background-clip: text; color: transparent; }
  h1 { margin-top: 22px; font: 900 44px/1 Impact, "Anton", sans-serif; text-transform: uppercase; letter-spacing: .01em; }
  .ok { display: inline-flex; align-items: center; gap: 8px; margin-top: 14px; padding: 7px 14px; border-radius: 999px;
        font-weight: 800; font-size: 13px; color: #0b3a2a; background: #5effc1; box-shadow: 0 0 22px rgba(94,255,193,.6); }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: #0b3a2a; animation: blink 1.2s infinite; }
  @keyframes blink { 50% { opacity: .2; } }
  p { margin-top: 16px; line-height: 1.6; color: #e4d8ff; }
  .cash { font: 900 22px/1 "Alfa Slab One", Georgia, serif; color: #72d35a; -webkit-text-stroke: 1.5px #000; paint-order: stroke fill; text-shadow: 2px 2px 0 #000; }
  .links { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 22px; }
  a { padding: 11px 18px; border-radius: 999px; font-weight: 800; font-size: 14px; text-decoration: none; color: #1b0730;
      background: linear-gradient(100deg, var(--gold), var(--orange) 35%, var(--pink)); box-shadow: 0 10px 30px -10px rgba(255,79,163,.9); }
  a.ghost { color: var(--ink); background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.18); box-shadow: none; }
</style>
</head>
<body>
  <div class="sun"></div>
  <div class="grid"></div>
  <svg class="palm l" viewBox="0 0 120 200"><path d="M56 200 C58 150 64 100 76 64 L82 66 C72 102 66 150 66 200Z"/><path d="M79 64 c18 -14 40 -12 50 4 c-18 -6 -34 -6 -50 -4z M79 64 c-16 -14 -38 -14 -48 0 c16 -6 32 -4 48 0z M79 64 c4 -20 20 -30 38 -30 c-16 8 -28 18 -38 30z M79 64 c-6 -18 -22 -26 -36 -26 c14 8 26 16 36 26z"/></svg>
  <svg class="palm r" viewBox="0 0 120 200"><path d="M56 200 C58 150 64 100 76 64 L82 66 C72 102 66 150 66 200Z"/><path d="M79 64 c18 -14 40 -12 50 4 c-18 -6 -34 -6 -50 -4z M79 64 c-16 -14 -38 -14 -48 0 c16 -6 32 -4 48 0z M79 64 c4 -20 20 -30 38 -30 c-16 8 -28 18 -38 30z M79 64 c-6 -18 -22 -26 -36 -26 c14 8 26 16 36 26z"/></svg>
  <main class="card">
    <div class="logo"><span class="mark">⚡</span><span>Spike<span class="clip">Clip</span></span></div>
    <h1>License <span class="clip">HQ</span></h1>
    <span class="ok"><span class="dot"></span>All systems online</span>
    <p>This is the SpikeClip server: accounts, payments and license keys for the desktop app.
       Your clips are made on your own PC — no video ever comes here.</p>
    <p><span class="cash">$0</span> &nbsp;cloud render fees · keys bound to your computer · checked every few days</p>
    <div class="links">
      <a href="https://spikeclip-app.vercel.app">Open the website</a>
      <a class="ghost" href="https://spikeclip-app.vercel.app/app">My license</a>
      <a class="ghost" href="/docs">API docs</a>
    </div>
  </main>
</body>
</html>
"""
