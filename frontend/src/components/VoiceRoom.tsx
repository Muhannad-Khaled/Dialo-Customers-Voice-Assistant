'use client'

import { useState, useRef, useCallback, useMemo } from 'react'
import {
    LiveKitRoom,
    RoomAudioRenderer,
    useLocalParticipant,
    useTranscriptions,
    useVoiceAssistant,
} from '@livekit/components-react'
import '@livekit/components-styles'
import styles from './VoiceRoom.module.css'
import AudioVisualizer from './AudioVisualizer'
import TranscriptPanel from './TranscriptPanel'
import { STRINGS, isRTL, type Lang } from '@/lib/strings'

interface VoiceRoomProps {
    token: string
    room: string
    identity: string
    language: Lang
}

interface Message {
    id: string
    role: 'user' | 'assistant'
    content: string
}

// agent = real-time LiveKit agent worker (default) | rest = record->STT->chat->TTS fallback
const VOICE_MODE = process.env.NEXT_PUBLIC_VOICE_MODE || 'agent'

export default function VoiceRoom({ token, room, identity, language }: VoiceRoomProps) {
    const lkUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL || 'ws://localhost:7880'

    return (
        <LiveKitRoom
            serverUrl={lkUrl}
            token={token}
            connect={true}
            audio={true}
            video={false}
            onDisconnected={() => (window.location.href = '/')}
            data-lk-theme="default"
            dir={isRTL(language) ? 'rtl' : 'ltr'}
        >
            {/* Plays the agent's synthesized (TTS) audio track. */}
            <RoomAudioRenderer />
            {VOICE_MODE === 'rest'
                ? <RestRoomUI room={room} identity={identity} language={language} />
                : <AgentRoomUI room={room} identity={identity} language={language} />}
        </LiveKitRoom>
    )
}

/* ─── Agent mode: continuous LiveKit voice agent ──────────────────────────── */

function AgentRoomUI({ room, identity, language }: { room: string; identity: string; language: Lang }) {
    const { localParticipant } = useLocalParticipant()
    const { state: agentState } = useVoiceAssistant()
    const transcriptions = useTranscriptions()
    const [muted, setMuted] = useState(false)
    const t = STRINGS[language]

    const localIdentity = localParticipant?.identity

    // Map LiveKit transcription streams (user finals + agent output) to chat bubbles.
    const messages: Message[] = useMemo(() => {
        return [...transcriptions]
            .sort((a, b) => a.streamInfo.timestamp - b.streamInfo.timestamp)
            .map((t) => ({
                id: t.streamInfo.id,
                role: t.participantInfo.identity === localIdentity ? 'user' : 'assistant',
                content: t.text,
            }))
    }, [transcriptions, localIdentity])

    const toggleMute = useCallback(() => {
        const nextMuted = !muted
        localParticipant?.setMicrophoneEnabled(!nextMuted)
        setMuted(nextMuted)
    }, [muted, localParticipant])

    const statusLabel = muted
        ? t.muted
        : agentState === 'thinking'
            ? t.thinking
            : agentState === 'speaking'
                ? t.speaking
                : agentState === 'listening'
                    ? t.listening
                    : t.connectingShort
    const live = !muted && (agentState === 'listening' || agentState === 'speaking')

    return (
        <div className={styles.roomWrapper}>
            <div className={styles.sidebar}>
                <div className={styles.sidebarHeader}>
                    <span className="gradient-text" style={{ fontWeight: 700, fontSize: '1.1rem' }}>{t.brand}</span>
                    <span className={styles.roomBadge}>{room}</span>
                </div>

                <div className={styles.vizSection}>
                    <AudioVisualizer active={live} />
                    <div className={styles.statusRow}>
                        <span className={`status-dot ${live ? 'live' : 'offline'}`} />
                        <span className={styles.statusText}>{statusLabel}</span>
                    </div>
                </div>

                <div className={styles.controls}>
                    <p className={styles.statusText} style={{ textAlign: 'center', opacity: 0.7 }}>
                        {t.startSpeaking}
                    </p>
                    <button onClick={toggleMute} className="btn btn-ghost" id="mute-btn">
                        {muted ? t.unmute : t.mute}
                    </button>
                    <button className="btn btn-ghost" id="leave-btn" onClick={() => (window.location.href = '/')}>
                        {t.leave}
                    </button>
                </div>

                <div className={styles.sessionInfo}>
                    <p className={styles.infoRow}><span>{t.identity}</span><span>{identity}</span></p>
                    <p className={styles.infoRow}><span>{t.mode}</span><span>agent</span></p>
                </div>
            </div>

            <div className={styles.main}>
                <TranscriptPanel messages={messages} identity={identity} language={language} />
            </div>
        </div>
    )
}

/* ─── Dev fallback: manual record → REST STT/Chat/TTS loop ─────────────────── */

function RestRoomUI({ room, identity, language }: { room: string; identity: string; language: Lang }) {
    const { localParticipant } = useLocalParticipant()
    const [muted, setMuted] = useState(false)
    const [messages, setMessages] = useState<Message[]>([])
    const [listening, setListening] = useState(false)
    const [processing, setProcessing] = useState(false)
    const mediaRecorderRef = useRef<MediaRecorder | null>(null)
    const chunksRef = useRef<Blob[]>([])
    const sessionId = useRef(`session-${identity}-${Date.now()}`)

    const handleRecord = useCallback(async () => {
        if (listening) {
            mediaRecorderRef.current?.stop()
            setListening(false)
            return
        }
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
            const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
            chunksRef.current = []
            recorder.ondataavailable = (e) => chunksRef.current.push(e.data)
            recorder.onstop = async () => {
                stream.getTracks().forEach((t) => t.stop())
                await sendAudio(new Blob(chunksRef.current, { type: 'audio/webm' }))
            }
            recorder.start()
            mediaRecorderRef.current = recorder
            setListening(true)
        } catch (err) {
            console.error('Mic error:', err)
        }
    }, [listening])

    async function sendAudio(audioBlob: Blob) {
        setProcessing(true)
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
        try {
            const formData = new FormData()
            formData.append('audio', audioBlob, 'recording.webm')
            const sttRes = await fetch(`${backendUrl}/api/stt`, { method: 'POST', body: formData })
            const { transcript } = await sttRes.json()
            if (!transcript?.trim()) return
            setMessages((prev) => [...prev, { id: Date.now().toString(), role: 'user', content: transcript }])

            const chatRes = await fetch(`${backendUrl}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: transcript, session_id: sessionId.current }),
            })
            const { answer } = await chatRes.json()
            setMessages((prev) => [...prev, { id: (Date.now() + 1).toString(), role: 'assistant', content: answer }])

            const ttsRes = await fetch(`${backendUrl}/api/tts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: answer }),
            })
            const audioBuffer = await ttsRes.arrayBuffer()
            const audioCtx = new AudioContext()
            const decoded = await audioCtx.decodeAudioData(audioBuffer)
            const source = audioCtx.createBufferSource()
            source.buffer = decoded
            source.connect(audioCtx.destination)
            source.start()
        } catch (err) {
            console.error('Pipeline error:', err)
        } finally {
            setProcessing(false)
        }
    }

    function toggleMute() {
        const nextMuted = !muted
        localParticipant?.setMicrophoneEnabled(!nextMuted)
        setMuted(nextMuted)
    }

    return (
        <div className={styles.roomWrapper}>
            <div className={styles.sidebar}>
                <div className={styles.sidebarHeader}>
                    <span className="gradient-text" style={{ fontWeight: 700, fontSize: '1.1rem' }}>Dialo</span>
                    <span className={styles.roomBadge}>{room}</span>
                </div>

                <div className={styles.vizSection}>
                    <AudioVisualizer active={listening} />
                    <div className={styles.statusRow}>
                        <span className={`status-dot ${listening ? 'live' : 'offline'}`} />
                        <span className={styles.statusText}>
                            {processing ? 'Processing…' : listening ? 'Recording…' : 'Ready (REST)'}
                        </span>
                    </div>
                </div>

                <div className={styles.controls}>
                    <button
                        id="record-btn"
                        onClick={handleRecord}
                        className={`btn ${listening ? 'btn-danger pulse' : 'btn-primary'} ${styles.recordBtn}`}
                        disabled={processing}
                    >
                        {listening ? '⏹ Stop' : '🎙️ Speak'}
                    </button>
                    <button onClick={toggleMute} className="btn btn-ghost" id="mute-btn">
                        {muted ? '🔇 Unmute' : '🔊 Mute'}
                    </button>
                    <button className="btn btn-ghost" id="leave-btn" onClick={() => (window.location.href = '/')}>
                        ✕ Leave
                    </button>
                </div>

                <div className={styles.sessionInfo}>
                    <p className={styles.infoRow}><span>Identity</span><span>{identity}</span></p>
                    <p className={styles.infoRow}>
                        <span>Session</span>
                        <span title={sessionId.current}>{sessionId.current.slice(-8)}</span>
                    </p>
                </div>
            </div>

            <div className={styles.main}>
                <TranscriptPanel messages={messages} identity={identity} language={language} />
            </div>
        </div>
    )
}
