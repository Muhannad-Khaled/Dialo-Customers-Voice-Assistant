'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import styles from './page.module.css'

export default function HomePage() {
    const router = useRouter()
    // Start empty so server and client render the same markup (no hydration
    // mismatch); the real values are restored from localStorage on mount below.
    const [room, setRoom] = useState('')
    const [identity, setIdentity] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    // Use a FRESH, unique room for every visit so the LiveKit agent is reliably
    // dispatched on room creation (rejoining a lingering room does not re-dispatch).
    // Conversation memory no longer depends on the room — it's keyed on the caller's
    // identity server-side (see agent_worker.py), so the remembered name below is
    // what actually carries memory across sessions.
    useEffect(() => {
        setRoom('support-' + Math.random().toString(36).slice(2, 8))
        setIdentity(localStorage.getItem('dialo_identity') ?? '')
    }, [])

    async function handleJoin(e: React.FormEvent) {
        e.preventDefault()
        if (!identity.trim()) { setError('Please enter your name.'); return }
        setLoading(true)
        setError('')
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/token`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ room, identity }),
            })
            if (!res.ok) throw new Error('Failed to get token')
            const data = await res.json()
            router.push(`/room?token=${encodeURIComponent(data.token)}&room=${encodeURIComponent(room)}&identity=${encodeURIComponent(identity)}`)
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Connection failed')
        } finally {
            setLoading(false)
        }
    }

    return (
        <main className={styles.main}>
            {/* Background orbs */}
            <div className={styles.orb1} aria-hidden />
            <div className={styles.orb2} aria-hidden />

            <div className={`${styles.hero} fade-in`}>
                {/* Badge */}
                <div className={styles.badge}>
                    <span className="status-dot live" />
                    AI-Powered · Always On
                </div>

                {/* Headline */}
                <h1 className={styles.headline}>
                    Talk to{' '}
                    <span className="gradient-text">Dialo</span>
                    <br />Customer Support
                </h1>
                <p className={styles.sub}>
                    Real-time voice assistant
                    <br />
                </p>

                {/* Join card */}
                <div className={`card ${styles.joinCard}`}>
                    <form onSubmit={handleJoin}>
                        <div className={styles.field}>
                            <label htmlFor="identity" className={styles.label}>Your Name</label>
                            <input
                                id="identity"
                                className="input"
                                value={identity}
                                onChange={e => { setIdentity(e.target.value); localStorage.setItem('dialo_identity', e.target.value) }}
                                placeholder="e.g. Alex"
                                autoFocus
                            />
                        </div>
                        <div className={styles.field}>
                            <label htmlFor="room" className={styles.label}>Room ID</label>
                            <input
                                id="room"
                                className="input"
                                value={room}
                                onChange={e => setRoom(e.target.value)}
                                placeholder="support-xxxxxx"
                            />
                        </div>
                        {error && <p className={styles.error}>{error}</p>}
                        <button
                            type="submit"
                            id="join-btn"
                            className={`btn btn-primary ${styles.joinBtn} ${loading ? styles.loading : ''}`}
                            disabled={loading}
                        >
                            {loading ? 'Connecting…' : '🎙️ Start Voice Session'}
                        </button>
                    </form>
                </div>

                {/* Feature grid */}
                <div className={styles.features}>
                    {FEATURES.map(f => (
                        <div key={f.title} className={`card ${styles.featureCard}`}>
                            <span className={styles.featureIcon}>{f.icon}</span>
                            <h3 className={styles.featureTitle}>{f.title}</h3>
                            <p className={styles.featureDesc}>{f.desc}</p>
                        </div>
                    ))}
                </div>
            </div>
        </main>
    )
}

const FEATURES = [
    { icon: '🧠', title: 'Gemini 2.5 Flash', desc: 'State-of-the-art LLM with RAG grounding for accurate answers.' },
    { icon: '📚', title: 'RAG Knowledge Base', desc: 'Retrieves relevant docs from ChromaDB with bge-m3 embeddings.' },
    { icon: '🎤', title: 'Faster-Whisper STT', desc: 'Low-latency, high-accuracy speech transcription.' },
    { icon: '🔊', title: 'Piper TTS', desc: 'Natural voice synthesis, streamed back in real time.' },
    { icon: '📡', title: 'LiveKit Streaming', desc: 'Ultra-low-latency audio transport via WebRTC.' },
    { icon: '🔒', title: 'Secure & Private', desc: 'JWT auth, session isolation, and encrypted transport.' },
]
