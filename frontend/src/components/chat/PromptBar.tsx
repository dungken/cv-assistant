import React, { useState, useRef, useEffect } from 'react';
import {
    PlusCircle,
    Mic,
    Image as ImageIcon,
    Send,
    Briefcase,
    Database,
    Edit2,
    LayoutGrid,
    FileText,
    Search,
    Zap,
    ChevronRight
} from 'lucide-react';
import { cn } from '../../lib/utils';

interface PromptBarProps {
    input: string;
    setInput: (val: string) => void;
    isLoading: boolean;
    onSend: (override?: string) => void;
    onKeyPress: (e: React.KeyboardEvent<HTMLInputElement>) => void;
    showChips: boolean;
}

const PromptBar: React.FC<PromptBarProps> = ({
    input, setInput, isLoading, onSend, onKeyPress, showChips
}) => {
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setIsMenuOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const menuItems = [
        { icon: <FileText className="text-blue-400" />, label: "Upload PDF CV", desc: "Anonymize & analyze", action: () => alert("Upload feature coming soon!") },
        { icon: <Search className="text-emerald-400" />, label: "Job Search", desc: "Match skills to market", action: () => onSend("Search for jobs matching my skills") },
        { icon: <Zap className="text-orange-400" />, label: "Fast Roadmap", desc: "Next 3 career steps", action: () => onSend("Generate a 3-step career roadmap for me") },
    ];

    return (
        <div className="w-full px-6 pb-8 pt-4 bg-canvas/60 backdrop-blur-sm border-t border-border-main/20">
            <div className="chat-stream-width relative group">
                {showChips && (
                    <div className="flex flex-wrap items-center justify-center gap-4 mb-10 animate-in fade-in slide-in-from-bottom-3 duration-700 delay-200">
                        <button onClick={() => onSend("Analyze my current CV for skill gaps")} className="action-chip">
                            <Briefcase size={16} className="text-indigo-400" />
                            Analyze CV Gaps
                        </button>
                        <button onClick={() => onSend("What are the top skills for a Senior Software Engineer according to O*NET?")} className="action-chip">
                            <Database size={16} className="text-emerald-400" />
                            O*NET Intelligence
                        </button>
                        <button onClick={() => onSend("Help me write an impact-based summary for my CV")} className="action-chip">
                            <Edit2 size={16} className="text-amber-400" />
                            Expert Summary
                        </button>
                        <button onClick={() => onSend("Recommend a career path for a Junior Developer")} className="action-chip">
                            <LayoutGrid size={16} className="text-purple-400" />
                            Career Scaling
                        </button>
                    </div>
                )}

                {/* PLUS MENU POPUP */}
                {isMenuOpen && (
                    <div ref={menuRef} className="absolute bottom-[80px] left-0 w-72 bg-surface border border-border-main rounded-[2rem] shadow-2xl p-3 animate-in fade-in slide-in-from-bottom-4 duration-300 z-50 overflow-hidden">
                        <div className="px-4 py-2 mb-2 border-b border-border-main/50">
                            <span className="text-[10px] font-black text-text-secondary uppercase tracking-widest">Assistant Tools</span>
                        </div>
                        {menuItems.map((item, idx) => (
                            <button
                                key={idx}
                                onClick={() => { item.action(); setIsMenuOpen(false); }}
                                className="w-full flex items-center gap-4 p-3 hover:bg-overlay rounded-2xl transition-all group text-left"
                            >
                                <div className="w-10 h-10 rounded-xl bg-secondary/50 flex items-center justify-center group-hover:bg-white group-hover:shadow-lg transition-all">
                                    {item.icon}
                                </div>
                                <div className="flex-1 overflow-hidden">
                                    <p className="text-sm font-bold text-text-primary group-hover:text-accent-primary transition-colors">{item.label}</p>
                                    <p className="text-[10px] text-text-secondary/60 font-medium truncate">{item.desc}</p>
                                </div>
                                <ChevronRight className="w-4 h-4 text-text-secondary/20 group-hover:text-text-primary group-hover:translate-x-1 transition-all" />
                            </button>
                        ))}
                    </div>
                )}

                <div className="absolute -inset-0.5 bg-linear-to-r from-accent-primary/10 to-accent-secondary/10 rounded-[2.5rem] blur-xl opacity-0 group-focus-within:opacity-100 transition duration-1000"></div>
                <div className="relative glass-panel rounded-[2.5rem] overflow-hidden transition-all duration-300 group-focus-within:pill-input-focus shadow-2xl bg-surface/90">
                    <div className="flex items-center h-[70px] pl-4 pr-3">
                        <button
                            onClick={() => setIsMenuOpen(!isMenuOpen)}
                            className={cn(
                                "p-3 rounded-full transition-all group/btn",
                                isMenuOpen ? "bg-accent-primary text-white rotate-45" : "hover:bg-overlay text-text-secondary hover:text-text-primary"
                            )}
                        >
                            <PlusCircle className="w-6 h-6" />
                        </button>
                        <input
                            className="flex-1 bg-transparent px-4 outline-none text-[17px] text-text-primary placeholder:text-text-secondary/30 font-medium"
                            placeholder="Type a message or use the + menu..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={onKeyPress}
                            disabled={isLoading}
                        />
                        <div className="flex items-center gap-1.5">
                            <button className="p-2.5 hover:bg-overlay rounded-full text-text-secondary hover:text-text-primary hidden sm:flex transition-transform hover:scale-110">
                                <Mic className="w-5 h-5" />
                            </button>
                            <button className="p-2.5 hover:bg-overlay rounded-full text-text-secondary hover:text-text-primary hidden sm:flex transition-transform hover:scale-110">
                                <ImageIcon className="w-5 h-5" />
                            </button>
                            <button
                                onClick={() => onSend()}
                                disabled={isLoading || !input.trim()}
                                className={cn(
                                    "w-12 h-12 flex items-center justify-center rounded-full transition-all ml-1 shadow-lg",
                                    input.trim() ? "bg-text-primary text-bg-primary hover:scale-105 active:scale-95 shadow-accent-primary/20" : "bg-overlay text-text-secondary opacity-30 grayscale"
                                )}
                            >
                                <Send className={cn("w-5 h-5", input.trim() && "translate-x-0.5 -translate-y-0.5 rotate-12 transition-transform")} />
                            </button>
                        </div>
                    </div>
                </div>
                <div className="flex items-center justify-center gap-5 mt-7 opacity-20">
                    <p className="text-[10px] font-black uppercase tracking-[0.4em] text-text-secondary">Enterprise Career Engine</p>
                    <div className="w-1.5 h-1.5 rounded-full bg-border-main"></div>
                    <p className="text-[10px] font-black uppercase tracking-[0.4em] text-text-secondary">O*NET Knowledge Integrator</p>
                </div>
            </div>
        </div>
    );
};

export default PromptBar;
