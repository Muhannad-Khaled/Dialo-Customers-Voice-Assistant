'use client'

import { Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import dynamic from 'next/dynamic'
import styles from './page.module.css'

// LiveKit components must be client-side only
const VoiceRoom = dynamic(() => import('@/components/VoiceRoom'), { ssr: false })

function RoomContent() {
    const params = useSearchParams()
    const token = params.get('token') ?? ''
    const room = params.get('room') ?? ''
    const identity = params.get('identity') ?? ''
    const language = params.get('language') === 'ar' ? 'ar' : 'en'

    if (!token) {
        return (
            <div className={styles.error}>
                <span>⚠️</span>
                <p>No session token. Please <a href="/">go back and join a room</a>.</p>
            </div>
        )
    }

    return <VoiceRoom token={token} room={room} identity={identity} language={language} />
}

export default function RoomPage() {
    return (
        <Suspense fallback={<div className={styles.loading}>Connecting…</div>}>
            <RoomContent />
        </Suspense>
    )
}
