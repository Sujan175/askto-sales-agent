"use client"

import { useEffect, useRef } from "react"

interface AnimatedOrbProps {
  isAnimating: boolean
}

export function AnimatedOrb({ isAnimating }: AnimatedOrbProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationRef = useRef<number>(0)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    const size = 500
    canvas.width = size
    canvas.height = size
    const cx = size / 2
    const cy = size / 2

    let t = 0

    const draw = () => {
      ctx.clearRect(0, 0, size, size)

      // 🌀 ANIMATED RADIAL GRADIENT (Perplexity-style pulsing waves)
      const baseRadius = 200
      const numWaves = 5
      
      ctx.fillStyle = "#e1f5fe"
      ctx.fillRect(0, 0, size, size)

      if (isAnimating) {
        for (let i = 0; i < numWaves; i++) {
          const offset = (i / numWaves) * Math.PI * 2
          const wave = ((t * 0.08 + offset) % (Math.PI * 2))
          const waveRadius = Math.max(10, baseRadius * (0.4 + Math.sin(wave) * 0.5))
          const opacity = Math.max(0.08, 0.25 + Math.sin(wave) * 0.15)

          const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, waveRadius)
          grad.addColorStop(0, `rgba(31, 142, 219, ${opacity})`)
          grad.addColorStop(0.5, `rgba(66, 165, 230, ${opacity * 0.7})`)
          grad.addColorStop(1, `rgba(106, 189, 234, 0)`)

          ctx.fillStyle = grad
          ctx.fillRect(0, 0, size, size)
        }
      } else {
        // Static gradient when not animating
        const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, baseRadius)
        grad.addColorStop(0, "rgba(31, 142, 219, 0.2)")
        grad.addColorStop(0.5, "rgba(66, 165, 230, 0.1)")
        grad.addColorStop(1, "rgba(106, 189, 234, 0)")
        
        ctx.fillStyle = grad
        ctx.fillRect(0, 0, size, size)
      }

      t++
      animationRef.current = requestAnimationFrame(draw)
    }

    draw()

    return () => cancelAnimationFrame(animationRef.current)
  }, [isAnimating])

  return (
    <canvas
      ref={canvasRef}
      className="w-[300px] h-[300px] md:w-[500px] md:h-[500px] rounded-full"
    />
  )
}