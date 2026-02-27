import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

// Generate deterministic avatar gradient & emoji based on persona
export function generateAvatar(persona: string = "", name: string = "") {
    // Simple hash function for deterministic output
    const hashString = (str: string) => {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = str.charCodeAt(i) + ((hash << 5) - hash);
        }
        return hash;
    };

    const gradients = [
        "from-pink-500 to-rose-400",
        "from-[#9B6FFF] to-[#4ECDC4]",
        "from-blue-500 to-cyan-400",
        "from-amber-400 to-orange-500",
        "from-emerald-400 to-cyan-500",
        "from-[#E94B8C] to-[#9B6FFF]",
        "from-indigo-500 to-purple-500",
    ];

    // Map keywords to emojis
    const emojiMap: Record<string, string> = {
        gym: "🏋️‍♂️", fitness: "💪", workout: "🏃‍♂️",
        tech: "💻", nerd: "🤓", dev: "👨‍💻", gamer: "🎮",
        art: "🎨", creative: "✨", design: "🖌️",
        astrology: "🔮", star: "⭐", moon: "🌙",
        food: "🍕", chef: "👨‍🍳", cook: "🍳", coffee: "☕",
        music: "🎵", dj: "🎧", guitar: "🎸",
        party: "🎉", outgoing: "🍸", social: "🥂",
        dog: "🐕", cat: "🐈", pet: "🐾",
        goth: "🦇", dark: "🖤",
        romance: "💖", sweet: "🥰",
        bro: "🤙", chill: "😎",
    };

    const pLower = persona.toLowerCase();
    let selectedEmoji = "";

    // Find matching emoji
    for (const [key, emoji] of Object.entries(emojiMap)) {
        if (pLower.includes(key)) {
            selectedEmoji = emoji;
            break;
        }
    }

    // Fallback to initial
    if (!selectedEmoji) {
        selectedEmoji = name.substring(0, 1).toUpperCase();
    }

    // Deterministic gradient selection based on combined string
    const hash = Math.abs(hashString(persona + name));
    const gradient = gradients[hash % gradients.length];

    return { emoji: selectedEmoji, gradient };
}
