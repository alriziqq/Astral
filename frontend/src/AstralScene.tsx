import { useEffect, useMemo, useRef, useState } from 'react'
import blackholeImage from './assets/blackhole-reference.png'
import earthImage from './assets/earth-reference.png'
import sunImage from './assets/sun-reference.png'

type SceneModel = 'blackhole' | 'earth' | 'sun'

const MODEL_LABELS: Record<SceneModel, string> = { blackhole: 'Black hole', earth: 'Earth', sun: 'Matahari' }
const MODEL_IMAGES: Record<SceneModel, string> = { blackhole: blackholeImage, earth: earthImage, sun: sunImage }

export function AstralScene({ compact }: { compact: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [model, setModel] = useState<SceneModel>('blackhole')
  const [rotation, setRotation] = useState(-5)
  const [zoom, setZoom] = useState(1)
  const dragRef = useRef<{ x: number; rotation: number } | null>(null)
  const modelImage = useMemo(() => MODEL_IMAGES[model], [model])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const context = canvas.getContext('2d')
    if (!context) return
    const rect = canvas.getBoundingClientRect()
    const ratio = window.devicePixelRatio || 1
    canvas.width = rect.width * ratio
    canvas.height = rect.height * ratio
    context.setTransform(ratio, 0, 0, ratio, 0, 0)
    context.clearRect(0, 0, rect.width, rect.height)
    const stars = [[.05, .18, 1], [.12, .72, 1], [.23, .31, 1.4], [.34, .12, .8], [.48, .82, 1], [.61, .2, 1], [.75, .68, 1.3], [.88, .28, .8], [.94, .83, 1], [.67, .91, .7], [.16, .93, .7], [.83, .1, .65]]
    stars.forEach(([x, y, size], index) => {
      context.globalAlpha = .34 + (index % 3) * .2
      context.fillStyle = index % 4 === 0 ? '#efb58f' : '#d9e4ed'
      context.beginPath()
      context.arc(rect.width * x, rect.height * y, size, 0, Math.PI * 2)
      context.fill()
    })
    context.globalAlpha = 1
  }, [compact])

  function changeZoom(delta: number) { setZoom((value) => Math.min(1.22, Math.max(.82, value + delta))) }

  return <div className={`astral-scene ${compact ? 'astral-scene--compact' : ''}`} aria-label="Model astral interaktif">
    <span className="scene-title">ASTRAL</span>
    <canvas ref={canvasRef} className="astral-canvas" aria-hidden="true" onPointerDown={(event) => { event.currentTarget.setPointerCapture(event.pointerId); dragRef.current = { x: event.clientX, rotation } }} onPointerMove={(event) => { if (dragRef.current) setRotation(dragRef.current.rotation + (event.clientX - dragRef.current.x) * .18) }} onPointerUp={() => { dragRef.current = null }} onPointerCancel={() => { dragRef.current = null }} onWheel={(event) => { event.preventDefault(); changeZoom(event.deltaY > 0 ? -.05 : .05) }} />
    <img className="astral-model-image" src={modelImage} alt={`${MODEL_LABELS[model]} interaktif`} style={{ transform: `translate(-50%, -50%) rotate(${rotation}deg) scale(${zoom})` }} />
    {!compact && <div className="scene-controls"><div className="scene-models">{(Object.keys(MODEL_LABELS) as SceneModel[]).map((item) => <button type="button" key={item} className={item === model ? 'scene-model scene-model--active' : 'scene-model'} onClick={() => setModel(item)}>{MODEL_LABELS[item]}</button>)}</div><span>Drag untuk memutar · Scroll untuk zoom</span></div>}
  </div>
}
