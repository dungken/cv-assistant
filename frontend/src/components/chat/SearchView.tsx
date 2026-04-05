import React, { useState, useMemo, useEffect, useRef } from 'react';
import { Search, X, MessageSquare, Clock, Calendar } from 'lucide-react';
import { Session } from '../../services/api';
import { Button } from '../ui/Button';
import { cn } from '../../lib/utils';

interface SearchViewProps {
    sessions: Session[];
    onSelectSession: (id: number) => void;
    onClose: () => void;
}

const SearchView: React.FC<SearchViewProps> = ({ sessions, onSelectSession, onClose }) => {
    const [query, setQuery] = useState('');
    const inputRef = useRef<HTMLInputElement>(null);

    // Auto-focus the search input
    useEffect(() => {
        inputRef.current?.focus();
    }, []);

    const filteredSessions = useMemo(() => {
        if (!query.trim()) return sessions;
        return sessions.filter(s => 
            s.title.toLowerCase().includes(query.toLowerCase())
        );
    }, [query, sessions]);

    // Simple date formatter to match Gemini style
    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        const now = new Date();
        const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

        if (diffInDays === 0) return 'Today';
        if (diffInDays === 1) return 'Yesterday';
        if (diffInDays < 7) return date.toLocaleDateString('en-US', { weekday: 'short' });
        return date.toLocaleDateString('en-US', { day: 'numeric', month: 'short' });
    };

    return (
        <div className="flex-1 flex flex-col h-full items-center pt-20 px-6 animate-in fade-in zoom-in-95 duration-500 max-w-5xl mx-auto w-full overflow-hidden">
            {/* Background Accents */}
            <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-accent-primary/5 rounded-full blur-[120px] pointer-events-none" />
            <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-accent-secondary/5 rounded-full blur-[120px] pointer-events-none" />

            <div className="w-full max-w-3xl space-y-12 z-10 flex flex-col h-full">
                {/* Title */}
                <h1 className="text-5xl font-medium tracking-tight font-outfit text-text-primary px-4">
                    Search
                </h1>

                {/* Search Input Box */}
                <div className="relative group px-4">
                    <div className="absolute left-10 top-1/2 -translate-y-1/2 text-text-secondary group-focus-within:text-accent-primary transition-colors">
                        <Search className="w-5 h-5" strokeWidth={2} />
                    </div>
                    <input
                        ref={inputRef}
                        type="text"
                        placeholder="Search for chats"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        className="w-full h-16 bg-surface/50 border border-white/5 rounded-full pl-16 pr-14 text-lg font-medium outline-none focus:ring-4 focus:ring-accent-primary/10 focus:bg-surface transition-all placeholder:text-text-muted/50"
                    />
                    {query && (
                        <button 
                            onClick={() => setQuery('')}
                            className="absolute right-10 top-1/2 -translate-y-1/2 p-1.5 hover:bg-surface-hover rounded-full text-text-muted transition-colors"
                        >
                            <X className="w-4 h-4" />
                        </button>
                    )}
                </div>

                {/* Results Section */}
                <div className="flex-1 overflow-y-auto floating-scrollbar pb-20">
                    <div className="space-y-8 px-4">
                        <div className="space-y-6">
                            <h2 className="text-xs font-black uppercase tracking-[0.2em] text-text-muted ml-4">
                                {query ? `Found ${filteredSessions.length} results` : 'Recent'}
                            </h2>
                            
                            <div className="space-y-1">
                                {filteredSessions.length > 0 ? (
                                    filteredSessions.map(s => (
                                        <button
                                            key={s.id}
                                            onClick={() => onSelectSession(s.id)}
                                            className="w-full flex items-center justify-between p-4 px-6 hover:bg-surface/80 rounded-2xl transition-all group active:scale-[0.98]"
                                        >
                                            <div className="flex items-center gap-4 min-w-0">
                                                <div className="w-10 h-10 rounded-xl bg-accent-primary/5 flex items-center justify-center text-accent-primary group-hover:bg-accent-primary group-hover:text-white transition-all duration-300">
                                                    <MessageSquare className="w-4 h-4" />
                                                </div>
                                                <span className="font-bold text-[15px] truncate text-text-primary group-hover:translate-x-1 transition-transform">
                                                    {s.title}
                                                </span>
                                            </div>
                                            <span className="text-sm font-bold text-text-muted/60 whitespace-nowrap ml-4">
                                                {formatDate(s.updatedAt)}
                                            </span>
                                        </button>
                                    ))
                                ) : (
                                    <div className="py-20 flex flex-col items-center justify-center text-text-muted/40 gap-4">
                                        <Search className="w-12 h-12" strokeWidth={1} />
                                        <p className="font-bold text-lg uppercase tracking-widest">No chats found</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SearchView;
