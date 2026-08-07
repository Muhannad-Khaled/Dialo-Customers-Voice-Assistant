'use client'

import { useEffect, useRef } from 'react'
import styles from './TranscriptPanel.module.css'

interface Message { id: string; role: 'user' | 'assistant'; content: string }

interface TranscriptPanelProps {
    messages: Message[]
    identity: string
}

export default function TranscriptPanel({ messages, identity }: TranscriptPanelProps) {
    const bottomRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    return (
        <div className={styles.panel}>
            <div className={styles.header}>
                <h2 className={styles.title}>Conversation</h2>
                <span className={styles.count}>{messages.length} messages</span>
            </div>

            <div className={styles.messages} id="transcript-messages">
                {messages.length === 0 && (
                    <div className={styles.empty}>
                        <span className={styles.emptyIcon}>🎙️</span>
                        <p>Press <strong>Speak</strong> and ask anything.</p>
                        <p className={styles.emptyHint}>e.g. "What is your return policy?"</p>
                    </div>
                )}
                {messages.map(msg => (
                    <div
                        key={msg.id}
                        className={`${styles.bubble} ${msg.role === 'user' ? styles.user : styles.assistant} fade-in`}
                    >
                        <div className={styles.bubbleHeader}>
                            <span className={styles.role}>
                                {msg.role === 'user' ? identity || 'You' : '🤖 Dialo'}
                            </span>
                        </div>
                        <p className={styles.content}>{msg.content}</p>
                    </div>
                ))}
                <div ref={bottomRef} />
            </div>
        </div>
    )
}
