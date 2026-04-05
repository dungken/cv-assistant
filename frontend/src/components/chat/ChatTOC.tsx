import React, { useState } from 'react';
import { cn } from '../../lib/utils';

interface Message {
    role: 'user' | 'assistant';
    content: string;
}

interface ChatTOCProps {
    messages: Message[];
}

function extractUserPreview(content: string): string {
    return content.replace(/[*_`#]/g, '').trim().slice(0, 60) || 'Message';
}

const ChatTOC: React.FC<ChatTOCProps> = ({ messages }) => {
    const [hovered, setHovered] = useState<number | null>(null);

    // One entry per assistant message; track the preceding user message index
    const entries = messages
        .map((m, i) => {
            if (m.role !== 'assistant') return null;
            let userIndex = -1;
            let userPreview = '';
            for (let j = i - 1; j >= 0; j--) {
                if (messages[j].role === 'user') {
                    userIndex = j;
                    userPreview = extractUserPreview(messages[j].content);
                    break;
                }
            }
            if (userIndex === -1) return null;
            return { userIndex, userPreview };
        })
        .filter(Boolean) as { userIndex: number; userPreview: string }[];

    if (entries.length < 3) return null;

    // Scroll to the USER message, not the assistant reply
    const scrollTo = (userIndex: number) => {
        document.getElementById(`message-${userIndex}`)
            ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    return (
        <div className="absolute right-6 top-1/2 -translate-y-1/2 z-30 flex flex-col items-end gap-0 pointer-events-none">
            {entries.map((e) => {
                const isHov = hovered === e.userIndex;

                return (
                    <div
                        key={e.userIndex}
                        className="relative flex items-center justify-end pointer-events-auto"
                    >
                        {/* Tooltip — user message preview, appears to the left */}
                        {isHov && (
                            <div className="absolute right-full mr-4 bg-surface/95 border border-white/10 rounded-xl px-3.5 py-2 shadow-2xl text-[12px] leading-snug text-text-primary whitespace-nowrap max-w-[260px] truncate animate-in fade-in slide-in-from-right-2 duration-150 z-40 backdrop-blur-md">
                                {e.userPreview}
                            </div>
                        )}

                        {/* Button with large padding hit area, fixed-width bar inside */}
                        <button
                            onClick={() => scrollTo(e.userIndex)}
                            onMouseEnter={() => setHovered(e.userIndex)}
                            onMouseLeave={() => setHovered(null)}
                            className="py-2 pl-6 pr-0 flex items-center justify-end"
                            aria-label={e.userPreview}
                        >
                            <div
                                className={cn(
                                    "h-[3px] rounded-full transition-all duration-200",
                                    isHov
                                        ? "w-8 bg-accent-primary"
                                        : "w-6 bg-overlay/30 hover:bg-overlay/50"
                                )}
                            />
                        </button>
                    </div>
                );
            })}
        </div>
    );
};

export default ChatTOC;
