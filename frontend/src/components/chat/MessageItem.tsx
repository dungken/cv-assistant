import React from 'react';
import { User, Sparkles } from 'lucide-react';
import { Source } from '../../services/api';
import { cn } from '../../lib/utils';

interface MessageItemProps {
    role: 'user' | 'assistant';
    content: string;
    sources?: Source[];
}

const MessageItem: React.FC<MessageItemProps> = ({ role, content, sources }) => {
    return (
        <div className={cn(
            "group flex gap-8 animate-in fade-in slide-in-from-bottom-2 duration-700 fill-mode-both",
            role === 'user' ? "flex-row-reverse" : ""
        )}>
            <div className={cn(
                "w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center transition-all group-hover:scale-110 shadow-sm mt-1",
                role === 'user'
                    ? "bg-text-main text-canvas"
                    : "bg-surface border border-border-main text-accent-primary"
            )}>
                {role === 'user' ? <User className="w-4 h-4" /> : <Sparkles className="w-4 h-4 fill-current" />}
            </div>

            <div className={cn(
                "flex-1 min-w-0 space-y-3",
                role === 'user' ? "text-right" : "text-left"
            )}>
                <div className={cn(
                    "prose max-w-none transition-colors",
                    role === 'user'
                        ? "text-text-main bg-overlay/40 p-5 rounded-[2rem] rounded-tr-none inline-block max-w-[85%] border border-border-main"
                        : "text-text-main chat-text-glow"
                )}>
                    {content.split('\n').map((line, i) => (
                        <p key={i} className={cn(line.trim() === '' && 'h-2')}>
                            {line}
                        </p>
                    ))}
                </div>

                {sources && sources.length > 0 && (
                    <div className="flex flex-wrap gap-2 pt-3 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
                        {sources.map((s, i) => (
                            <div key={i} className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-overlay border border-border-main text-[10px] font-bold text-text-muted hover:text-text-main transition-all cursor-default shadow-sm hover:scale-105">
                                <span className="w-1.5 h-1.5 rounded-full bg-accent-secondary" />
                                {s.title}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default MessageItem;
