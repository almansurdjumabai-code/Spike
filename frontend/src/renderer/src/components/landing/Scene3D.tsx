import { useEffect, useRef, useState, type CSSProperties } from 'react'
import * as THREE from 'three'

/** A scroll-driven 3D showcase in the Vice-sunset look.
 *
 *  Everything is built from primitives here (no downloaded models): a phone
 *  playing a real clip on its screen, a neon sports car, palms, floating
 *  coins and a money bag on a synthwave road. Scrolling through the section
 *  moves the camera and the props through three beats:
 *    1. the stream plays   2. chat explodes, a spike is found   3. the 9:16 clip lands
 */

const BEATS = [
  { n: '01', title: 'Your stream plays', text: 'Point SpikeClip at a VOD. It reads every chat message on your PC.' },
  { n: '02', title: 'Chat explodes', text: 'W spam, “NO SHOT”, 💀 — the peak is found the second chat loses it.' },
  { n: '03', title: 'The clip lands', text: '20 s before the spike, 10 s after. Vertical, captioned, ready to post.' }
]

const PINK = 0xff4fa3
const CYAN = 0x39f0ff
const GOLD = 0xffd56b

function gradientTexture(stops: [number, string][], w = 4, h = 256): THREE.CanvasTexture {
  const c = document.createElement('canvas')
  c.width = w
  c.height = h
  const g = c.getContext('2d')!
  const grad = g.createLinearGradient(0, 0, 0, h)
  stops.forEach(([o, col]) => grad.addColorStop(o, col))
  g.fillStyle = grad
  g.fillRect(0, 0, w, h)
  const t = new THREE.CanvasTexture(c)
  t.colorSpace = THREE.SRGBColorSpace
  return t
}

function sunTexture(): THREE.CanvasTexture {
  const s = 512
  const c = document.createElement('canvas')
  c.width = c.height = s
  const g = c.getContext('2d')!
  const grad = g.createLinearGradient(0, 0, 0, s)
  grad.addColorStop(0, '#ffe48a')
  grad.addColorStop(0.55, '#ff9a52')
  grad.addColorStop(1, '#ff3d8b')
  g.fillStyle = grad
  g.beginPath()
  g.arc(s / 2, s / 2, s / 2, 0, Math.PI * 2)
  g.fill()
  g.globalCompositeOperation = 'destination-out'
  for (let i = 0; i < 7; i++) g.fillRect(0, s * 0.56 + i * 30, s, 4 + i * 2.6)
  const t = new THREE.CanvasTexture(c)
  t.colorSpace = THREE.SRGBColorSpace
  return t
}

function dollarSprite(): THREE.Sprite {
  const c = document.createElement('canvas')
  c.width = c.height = 128
  const g = c.getContext('2d')!
  g.font = '900 96px "Alfa Slab One", Georgia, serif'
  g.textAlign = 'center'
  g.textBaseline = 'middle'
  g.lineWidth = 10
  g.strokeStyle = '#000'
  g.strokeText('$', 64, 70)
  g.fillStyle = '#72d35a'
  g.fillText('$', 64, 70)
  const t = new THREE.CanvasTexture(c)
  t.colorSpace = THREE.SRGBColorSpace
  return new THREE.Sprite(new THREE.SpriteMaterial({ map: t, transparent: true }))
}

function roundedRect(w: number, h: number, r: number): THREE.Shape {
  const s = new THREE.Shape()
  s.moveTo(-w / 2 + r, -h / 2)
  s.lineTo(w / 2 - r, -h / 2)
  s.quadraticCurveTo(w / 2, -h / 2, w / 2, -h / 2 + r)
  s.lineTo(w / 2, h / 2 - r)
  s.quadraticCurveTo(w / 2, h / 2, w / 2 - r, h / 2)
  s.lineTo(-w / 2 + r, h / 2)
  s.quadraticCurveTo(-w / 2, h / 2, -w / 2, h / 2 - r)
  s.lineTo(-w / 2, -h / 2 + r)
  s.quadraticCurveTo(-w / 2, -h / 2, -w / 2 + r, -h / 2)
  return s
}

function makePhone(video: HTMLVideoElement): THREE.Group {
  const g = new THREE.Group()
  const w = 2.2
  const h = w * (16 / 9) + 0.25
  const body = new THREE.Mesh(
    new THREE.ExtrudeGeometry(roundedRect(w, h, 0.32), { depth: 0.22, bevelEnabled: true, bevelThickness: 0.06, bevelSize: 0.06, bevelSegments: 4 }),
    new THREE.MeshStandardMaterial({ color: 0x120827, metalness: 0.7, roughness: 0.25 })
  )
  body.position.z = -0.11
  g.add(body)
  const rim = new THREE.Mesh(
    new THREE.ExtrudeGeometry(roundedRect(w + 0.08, h + 0.08, 0.36), { depth: 0.05, bevelEnabled: false }),
    new THREE.MeshBasicMaterial({ color: PINK })
  )
  rim.position.z = -0.16
  g.add(rim)
  const tex = new THREE.VideoTexture(video)
  tex.colorSpace = THREE.SRGBColorSpace
  const screen = new THREE.Mesh(new THREE.PlaneGeometry(w - 0.16, w * (16 / 9) - 0.1), new THREE.MeshBasicMaterial({ map: tex, toneMapped: false }))
  screen.position.z = 0.18
  g.add(screen)
  return g
}

function makeCar(): THREE.Group {
  const g = new THREE.Group()
  const side = new THREE.Shape()
  side.moveTo(-2.2, 0.25)
  side.lineTo(2.25, 0.25)
  side.quadraticCurveTo(2.45, 0.3, 2.4, 0.62)
  side.lineTo(1.2, 0.86)
  side.quadraticCurveTo(0.6, 1.42, -0.4, 1.36)
  side.quadraticCurveTo(-1.35, 1.28, -1.8, 0.95)
  side.lineTo(-2.25, 0.82)
  side.quadraticCurveTo(-2.4, 0.5, -2.2, 0.25)
  const body = new THREE.Mesh(
    new THREE.ExtrudeGeometry(side, { depth: 1.7, bevelEnabled: true, bevelThickness: 0.12, bevelSize: 0.1, bevelSegments: 3 }),
    new THREE.MeshStandardMaterial({ color: PINK, metalness: 0.65, roughness: 0.28 })
  )
  body.position.z = -0.85
  g.add(body)
  const glass = new THREE.Mesh(
    new THREE.BoxGeometry(1.5, 0.36, 1.6),
    new THREE.MeshStandardMaterial({ color: 0x1b0730, metalness: 0.9, roughness: 0.1 })
  )
  glass.position.set(-0.25, 1.12, 0)
  glass.rotation.z = -0.06
  g.add(glass)
  const wheelGeo = new THREE.CylinderGeometry(0.42, 0.42, 0.34, 24)
  wheelGeo.rotateX(Math.PI / 2)
  const wheelMat = new THREE.MeshStandardMaterial({ color: 0x0b0418, roughness: 0.6 })
  const rimMat = new THREE.MeshBasicMaterial({ color: CYAN })
  const wheels: THREE.Mesh[] = []
  for (const [x, z] of [[1.45, 0.92], [-1.45, 0.92], [1.45, -0.92], [-1.45, -0.92]]) {
    const w = new THREE.Mesh(wheelGeo, wheelMat)
    w.position.set(x, 0.42, z)
    const hub = new THREE.Mesh(new THREE.TorusGeometry(0.24, 0.04, 8, 24), rimMat)
    hub.position.z = z > 0 ? 0.18 : -0.18
    w.add(hub)
    g.add(w)
    wheels.push(w)
  }
  g.userData.wheels = wheels
  for (const z of [0.6, -0.6]) {
    const head = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.12, 0.42), new THREE.MeshBasicMaterial({ color: 0xfff3c4 }))
    head.position.set(2.42, 0.6, z)
    g.add(head)
    const tail = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.1, 0.5), new THREE.MeshBasicMaterial({ color: 0xff2147 }))
    tail.position.set(-2.3, 0.7, z)
    g.add(tail)
  }
  const glow = new THREE.Mesh(
    new THREE.PlaneGeometry(5.2, 2.6),
    new THREE.MeshBasicMaterial({ color: PINK, transparent: true, opacity: 0.45, blending: THREE.AdditiveBlending, depthWrite: false })
  )
  glow.rotation.x = -Math.PI / 2
  glow.position.y = 0.03
  g.add(glow)
  const under = new THREE.PointLight(PINK, 6, 6)
  under.position.y = 0.3
  g.add(under)
  return g
}

function makePalm(height: number): THREE.Group {
  const g = new THREE.Group()
  const trunkMat = new THREE.MeshStandardMaterial({ color: 0x3a1a3f, roughness: 0.9 })
  const segs = 7
  let y = 0
  let x = 0
  for (let i = 0; i < segs; i++) {
    const seg = new THREE.Mesh(new THREE.CylinderGeometry(0.16 - i * 0.012, 0.2 - i * 0.012, height / segs, 7), trunkMat)
    x += 0.06 * i * 0.3
    seg.position.set(x, y + height / segs / 2, 0)
    seg.rotation.z = -0.04 * i
    g.add(seg)
    y += height / segs
  }
  const leafMat = new THREE.MeshStandardMaterial({ color: 0x1a0b3d, emissive: 0x2b0f4a, roughness: 0.8, side: THREE.DoubleSide })
  const crown = new THREE.Group()
  crown.position.set(x, y, 0)
  for (let i = 0; i < 9; i++) {
    const leaf = new THREE.Mesh(new THREE.ConeGeometry(0.28, 2.4, 4, 1, true), leafMat)
    leaf.scale.z = 0.25
    leaf.geometry.translate(0, 1.2, 0)
    leaf.rotation.z = Math.PI / 2 + 0.55
    const pivot = new THREE.Group()
    pivot.rotation.y = (i / 9) * Math.PI * 2
    pivot.add(leaf)
    crown.add(pivot)
  }
  g.add(crown)
  g.userData.crown = crown
  return g
}

function makeCoin(): THREE.Mesh {
  const coin = new THREE.Mesh(
    new THREE.CylinderGeometry(0.42, 0.42, 0.09, 28),
    new THREE.MeshStandardMaterial({ color: GOLD, metalness: 0.95, roughness: 0.22, emissive: 0x3a2400 })
  )
  coin.rotation.x = Math.PI / 2
  return coin
}

function makeBag(): THREE.Group {
  const g = new THREE.Group()
  const mat = new THREE.MeshStandardMaterial({ color: 0xd9c49a, roughness: 0.85 })
  const sack = new THREE.Mesh(new THREE.SphereGeometry(0.9, 24, 18), mat)
  sack.scale.set(1, 1.1, 0.95)
  g.add(sack)
  const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.4, 0.4, 16), mat)
  neck.position.y = 1.05
  g.add(neck)
  const tie = new THREE.Mesh(new THREE.TorusGeometry(0.28, 0.06, 8, 20), new THREE.MeshStandardMaterial({ color: 0x5a3a1a }))
  tie.rotation.x = Math.PI / 2
  tie.position.y = 0.95
  g.add(tie)
  const dollar = dollarSprite()
  dollar.scale.set(1.1, 1.1, 1)
  dollar.position.set(0, 0, 0.92)
  g.add(dollar)
  return g
}

export default function Scene3D(): JSX.Element {
  const section = useRef<HTMLElement>(null)
  const canvas = useRef<HTMLCanvasElement>(null)
  const [beat, setBeat] = useState(0)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    const host = section.current
    const cv = canvas.current
    if (!host || !cv) return
    let renderer: THREE.WebGLRenderer
    try {
      renderer = new THREE.WebGLRenderer({ canvas: cv, antialias: true, powerPreference: 'high-performance' })
    } catch {
      setFailed(true)
      return
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75))
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.outputColorSpace = THREE.SRGBColorSpace

    const scene = new THREE.Scene()
    scene.background = gradientTexture([
      [0, '#140838'],
      [0.35, '#4b1fa8'],
      [0.62, '#c03ab8'],
      [0.8, '#ff6f8f'],
      [1, '#ffa25a']
    ])
    scene.fog = new THREE.Fog(0x3a1060, 22, 70)
    const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 200)

    scene.add(new THREE.HemisphereLight(0xffa3d8, 0x1a0b3d, 1.4))
    const sunLight = new THREE.DirectionalLight(0xffb36b, 2.2)
    sunLight.position.set(-6, 10, -20)
    scene.add(sunLight)
    const fill = new THREE.DirectionalLight(CYAN, 0.8)
    fill.position.set(8, 4, 10)
    scene.add(fill)

    const sun = new THREE.Mesh(new THREE.CircleGeometry(14, 64), new THREE.MeshBasicMaterial({ map: sunTexture(), transparent: true, fog: false }))
    sun.position.set(0, 9, -60)
    scene.add(sun)

    const ground = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), new THREE.MeshStandardMaterial({ color: 0x14062b, roughness: 0.35, metalness: 0.4 }))
    ground.rotation.x = -Math.PI / 2
    scene.add(ground)
    const grid = new THREE.GridHelper(400, 160, PINK, PINK)
    ;(grid.material as THREE.Material).transparent = true
    ;(grid.material as THREE.Material).opacity = 0.45
    grid.position.y = 0.01
    scene.add(grid)

    const video = document.createElement('video')
    video.src = '/media/clips/c5.mp4'
    video.muted = true
    video.loop = true
    video.playsInline = true
    video.crossOrigin = 'anonymous'
    const phone = makePhone(video)
    phone.position.set(0, 3.4, 0)
    scene.add(phone)

    const car = makeCar()
    car.position.set(-16, 0, 3.2)
    scene.add(car)

    const bag = makeBag()
    bag.position.set(5.6, 1.1, -3.5)
    scene.add(bag)

    const palms: THREE.Group[] = []
    for (let i = 0; i < 12; i++) {
      const palm = makePalm(5 + (i % 3) * 1.2)
      palm.position.set(i % 2 ? 9 + (i % 4) : -9 - (i % 4), 0, -i * 5 + 8)
      palm.rotation.y = i
      scene.add(palm)
      palms.push(palm)
    }

    const coins: THREE.Mesh[] = []
    for (let i = 0; i < 16; i++) {
      const coin = makeCoin()
      coin.userData.a = (i / 16) * Math.PI * 2
      coin.userData.r = 2.8 + (i % 3) * 0.6
      coin.userData.y = 1 + (i % 5) * 0.9
      scene.add(coin)
      coins.push(coin)
    }

    const resize = (): void => {
      const w = cv.clientWidth
      const h = cv.clientHeight
      renderer.setSize(w, h, false)
      camera.aspect = w / h
      camera.updateProjectionMatrix()
    }
    resize()
    window.addEventListener('resize', resize)

    let visible = false
    const io = new IntersectionObserver(([e]) => {
      visible = e.isIntersecting
      if (visible) void video.play().catch(() => undefined)
      else video.pause()
    })
    io.observe(host)

    const progress = (): number => {
      const r = host.getBoundingClientRect()
      const total = r.height - window.innerHeight
      return total > 0 ? Math.min(1, Math.max(0, -r.top / total)) : 0
    }
    const ease = (t: number): number => t * t * (3 - 2 * t)
    const target = new THREE.Vector3()
    let smooth = 0
    let lastBeat = -1
    let raf = 0
    const clock = new THREE.Clock()

    const frame = (): void => {
      raf = requestAnimationFrame(frame)
      if (!visible) return
      const t = clock.getElapsedTime()
      smooth += (progress() - smooth) * 0.08
      const p = smooth

      const b = p < 0.34 ? 0 : p < 0.67 ? 1 : 2
      if (b !== lastBeat) {
        lastBeat = b
        setBeat(b)
      }

      // Camera arcs around the scene as you scroll.
      const a = -0.35 + p * 1.5
      const radius = 15 - ease(Math.min(1, p * 1.4)) * 3
      camera.position.set(Math.sin(a) * radius, 3.2 + Math.sin(p * Math.PI) * 2.2, Math.cos(a) * radius)
      target.set(0, 2.9 + ease(Math.max(0, (p - 0.6) / 0.4)) * 0.7, 0)
      camera.lookAt(target)

      // 1: the phone turns to face you; 3: it rises, front and centre.
      phone.rotation.y = Math.sin(t * 0.6) * 0.18 + (1 - ease(Math.min(1, p * 2))) * 0.9 + a
      phone.position.y = 3.4 + Math.sin(t * 1.4) * 0.12 + ease(Math.max(0, (p - 0.6) / 0.4)) * 0.8
      const s = 1 + ease(Math.max(0, (p - 0.6) / 0.4)) * 0.25
      phone.scale.set(s, s, s)

      // The car drives in, then idles with its wheels spinning.
      const drive = ease(Math.min(1, p / 0.45))
      car.position.x = -16 + drive * 13
      car.rotation.y = Math.sin(t * 0.8) * 0.04
      for (const w of car.userData.wheels as THREE.Mesh[]) w.rotation.z = -t * 8

      // 2: coins burst up around the phone when chat explodes.
      const burst = ease(Math.min(1, Math.max(0, (p - 0.28) / 0.3)))
      for (const c of coins) {
        const ang = c.userData.a + t * 0.5
        c.position.set(Math.cos(ang) * c.userData.r, 0.4 + c.userData.y * burst + Math.sin(t * 2 + c.userData.a) * 0.15, Math.sin(ang) * c.userData.r)
        c.rotation.z = t * 2 + c.userData.a
        c.scale.setScalar(0.2 + burst * 0.55)
      }
      bag.rotation.y = Math.sin(t * 0.7) * 0.4
      bag.position.y = 1.1 + Math.sin(t * 1.2) * 0.1

      for (const palm of palms) (palm.userData.crown as THREE.Group).rotation.z = Math.sin(t * 0.9 + palm.position.z) * 0.06
      grid.position.z = (t * 3) % 2.5

      renderer.render(scene, camera)
    }
    raf = requestAnimationFrame(frame)

    return () => {
      cancelAnimationFrame(raf)
      io.disconnect()
      window.removeEventListener('resize', resize)
      video.pause()
      video.removeAttribute('src')
      scene.traverse((o) => {
        const m = o as THREE.Mesh
        m.geometry?.dispose()
        const mat = m.material as THREE.Material | THREE.Material[] | undefined
        if (Array.isArray(mat)) mat.forEach((x) => x.dispose())
        else mat?.dispose()
      })
      renderer.dispose()
    }
  }, [])

  return (
    <section className="vc-3d" ref={section} id="showcase" aria-label="How SpikeClip turns a stream into a clip">
      <div className="vc-3d-sticky">
        {!failed && <canvas ref={canvas} className="vc-3d-canvas" />}
        <div className="vc-3d-shade" />
        <div className="vc-3d-copy">
          <div className="vc-kicker">On your PC</div>
          {BEATS.map((b, i) => (
            <div key={b.n} className={`vc-3d-beat${beat === i ? ' on' : ''}`}>
              <span className="vc-3d-n">{b.n}</span>
              <h2 className="vc-display">{b.title}</h2>
              <p>{b.text}</p>
            </div>
          ))}
          <div className="vc-3d-dots">
            {BEATS.map((b, i) => (
              <span key={b.n} className={beat === i ? 'on' : ''} />
            ))}
          </div>
        </div>
        <div className={`vc-3d-chat${beat === 1 ? ' on' : ''}`} aria-hidden="true">
          {['W', 'W W W', 'NO SHOT 😭', 'CLIP IT 🔥', 'WWWWW', '💀💀💀', 'W'].map((m, i) => (
            <span key={i} style={{ '--i': i } as CSSProperties}>
              {m}
            </span>
          ))}
        </div>
      </div>
    </section>
  )
}
