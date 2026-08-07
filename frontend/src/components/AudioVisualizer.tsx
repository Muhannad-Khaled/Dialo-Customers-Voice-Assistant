'use client'

import { useEffect, useRef } from 'react'
import styles from './AudioVisualizer.module.css'

interface AudioVisualizerProps {
    active: boolean
}

export default function AudioVisualizer({ active }: AudioVisualizerProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null)
    const animRef = useRef<number>(0)
    const analyserRef = useRef<AnalyserNode | null>(null)
    const streamRef = useRef<MediaStream | null>(null)

    useEffect(() => {
        if (!active) {
            cancelAnimationFrame(animRef.current)
            streamRef.current?.getTracks().forEach(t => t.stop())
            drawIdle()
            return
        }

        async function init() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
                streamRef.current = stream
                const ctx = new AudioContext()
                const src = ctx.createMediaStreamSource(stream)
                const analyser = ctx.createAnalyser()
                analyser.fftSize = 256
                src.connect(analyser)
                analyserRef.current = analyser
                draw()
            } catch { }
        }
        init()

        return () => {
            cancelAnimationFrame(animRef.current)
            streamRef.current?.getTracks().forEach(t => t.stop())
        }
    }, [active])

    function drawIdle() {
        const canvas = canvasRef.current
        if (!canvas) return
        const ctx = canvas.getContext('2d')!
        ctx.clearRect(0, 0, canvas.width, canvas.height)
        const cx = canvas.width / 2, cy = canvas.height / 2
        ctx.beginPath()
        ctx.arc(cx, cy, 40, 0, Math.PI * 2)
        ctx.strokeStyle = 'rgba(99,102,241,0.25)'
        ctx.lineWidth = 2
        ctx.stroke()
    }

    function draw() {
        const canvas = canvasRef.current
        const analyser = analyserRef.current
        if (!canvas || !analyser) return
        const ctx = canvas.getContext('2d')!
        const dataArray = new Uint8Array(analyser.frequencyBinCount)

        const render = () => {
            animRef.current = requestAnimationFrame(render)
            analyser.getByteFrequencyData(dataArray)
            ctx.clearRect(0, 0, canvas.width, canvas.height)
            const cx = canvas.width / 2, cy = canvas.height / 2
            const bars = 48
            const radius = 40
            for (let i = 0; i < bars; i++) {
                const angle = (i / bars) * Math.PI * 2 - Math.PI / 2
                const value = dataArray[i * 2] / 255
                const barLen = radius * 0.4 * value + 4
                const x1 = cx + Math.cos(angle) * radius
                const y1 = cy + Math.sin(angle) * radius
                const x2 = cx + Math.cos(angle) * (radius + barLen)
                const y2 = cy + Math.sin(angle) * (radius + barLen)
                ctx.beginPath()
                ctx.moveTo(x1, y1)
                ctx.lineTo(x2, y2)
                ctx.strokeStyle = `hsl(${240 + value * 60}, 80%, ${55 + value * 20}%)`
                ctx.lineWidth = 2.5
                ctx.lineCap = 'round'
                ctx.stroke()
            }
            // Center circle
            ctx.beginPath()
            ctx.arc(cx, cy, radius - 4, 0, Math.PI * 2)
            ctx.strokeStyle = active ? 'rgba(99,102,241,0.6)' : 'rgba(99,102,241,0.2)'
            ctx.lineWidth = 1.5
            ctx.stroke()
        }
        render()
    }

    return (
        <canvas
            ref={canvasRef}
            width={160}
            height={160}
            className={`${styles.canvas} ${active ? styles.active : ''}`}
        />
    )
}
