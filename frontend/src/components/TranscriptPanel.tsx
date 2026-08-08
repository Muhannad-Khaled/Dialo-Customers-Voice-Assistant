'use client'

import { useEffect, useRef } from 'react'
import styles from './TranscriptPanel.module.css'
import { STRINGS, type Lang } from '@/lib/strings'

interface Message { id: string; role: 'user' | 'assistant'; content: string }

interface TranscriptPanelProps {
    messages: Message[]
    identity: string
    language: Lang
}

export default function TranscriptPanel({ messages, identity, language }: TranscriptPanelProps) {
    const bottomRef = useRef<HTMLDivElement>(null)
    const t = STRINGS[language]

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    return (
        <div className={styles.panel}>
            <div className={styles.header}>
                <h2 className={styles.title}>{t.conversation}</h2>
                <span className={styles.count}>{messages.length} {t.messages}</span>
            </div>

            <div className={styles.messages} id="transcript-messages">
                {messages.length === 0 && (
                    <div className={styles.empty}>
                        <span className={styles.emptyIcon}>🎙️</span>
                        <p>{t.emptyPrompt}</p>
                        <p className={styles.emptyHint}>{t.emptyHint}</p>
                    </div>
                )}
                {messages.map(msg => (
                    <div
                        key={msg.id}
                        className={`${styles.bubble} ${msg.role === 'user' ? styles.user : styles.assistant} fade-in`}
                    >
                        <div className={styles.bubbleHeader}>
                            <span className={styles.role}>
                                {msg.role === 'user' ? identity || t.you : t.assistantLabel}
                            </span>
                        </div>
                        <p className={styles.content} dir="auto">{msg.content}</p>
                    </div>
                ))}
                <div ref={bottomRef} />
            </div>
        </div>
    )
}
