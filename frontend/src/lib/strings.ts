// Lightweight bilingual UI strings — no i18n library. Keyed by language code.
// Server-spoken text (greeting, agent replies) is handled backend-side; this only
// covers the static UI chrome.

export type Lang = 'en' | 'ar'

export const LANGUAGES: { code: Lang; label: string }[] = [
    { code: 'en', label: 'English' },
    { code: 'ar', label: 'العربية (مصري)' },
]

export function isRTL(lang: Lang): boolean {
    return lang === 'ar'
}

type Strings = {
    // Join screen
    headlinePre: string
    headlinePost: string
    sub: string
    nameLabel: string
    namePlaceholder: string
    languageLabel: string
    roomLabel: string
    nameRequired: string
    connecting: string
    startSession: string
    // Room
    brand: string
    muted: string
    thinking: string
    speaking: string
    listening: string
    connectingShort: string
    startSpeaking: string
    mute: string
    unmute: string
    leave: string
    identity: string
    mode: string
    // Transcript
    conversation: string
    messages: string
    assistantLabel: string
    you: string
    emptyPrompt: string
    emptyHint: string
}

export const STRINGS: Record<Lang, Strings> = {
    en: {
        headlinePre: 'Talk to',
        headlinePost: 'Customer Support',
        sub: 'Real-time voice assistant',
        nameLabel: 'Your Name',
        namePlaceholder: 'e.g. Alex',
        languageLabel: 'Language',
        roomLabel: 'Room ID',
        nameRequired: 'Please enter your name.',
        connecting: 'Connecting…',
        startSession: '🎙️ Start Voice Session',
        brand: 'Dialo',
        muted: 'Muted',
        thinking: 'Thinking…',
        speaking: 'Speaking…',
        listening: 'Listening…',
        connectingShort: 'Connecting…',
        startSpeaking: 'Just start speaking — the assistant is listening.',
        mute: '🔊 Mute',
        unmute: '🔇 Unmute',
        leave: '✕ Leave',
        identity: 'Identity',
        mode: 'Mode',
        conversation: 'Conversation',
        messages: 'messages',
        assistantLabel: '🤖 Dialo',
        you: 'You',
        emptyPrompt: 'Press Speak and ask anything.',
        emptyHint: 'e.g. "What is your return policy?"',
    },
    ar: {
        headlinePre: 'اتكلم مع',
        headlinePost: 'خدمة العملاء',
        sub: 'مساعد صوتي فوري',
        nameLabel: 'اسمك',
        namePlaceholder: 'مثلاً محمد',
        languageLabel: 'اللغة',
        roomLabel: 'رقم الغرفة',
        nameRequired: 'من فضلك اكتب اسمك.',
        connecting: 'جاري الاتصال…',
        startSession: '🎙️ ابدأ المحادثة الصوتية',
        brand: 'Dialo',
        muted: 'مكتوم',
        thinking: 'بيفكر…',
        speaking: 'بيتكلم…',
        listening: 'بيسمع…',
        connectingShort: 'جاري الاتصال…',
        startSpeaking: 'ابدأ اتكلم على طول — المساعد بيسمعك.',
        mute: '🔊 كتم',
        unmute: '🔇 تشغيل الصوت',
        leave: '✕ خروج',
        identity: 'الاسم',
        mode: 'الوضع',
        conversation: 'المحادثة',
        messages: 'رسائل',
        assistantLabel: '🤖 Dialo',
        you: 'أنت',
        emptyPrompt: 'دوس على "اتكلم" واسأل أي حاجة.',
        emptyHint: 'مثلاً: "سياسة الإرجاع عندكم إيه؟"',
    },
}
