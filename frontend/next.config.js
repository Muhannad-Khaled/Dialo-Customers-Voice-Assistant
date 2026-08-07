/** @type {import('next').NextConfig} */
const nextConfig = {
    env: {
        NEXT_PUBLIC_BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000',
        NEXT_PUBLIC_LIVEKIT_URL: process.env.NEXT_PUBLIC_LIVEKIT_URL || 'ws://localhost:7880',
        NEXT_PUBLIC_VOICE_MODE: process.env.NEXT_PUBLIC_VOICE_MODE || 'agent',
    },
}

module.exports = nextConfig
