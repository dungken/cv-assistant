import React from 'react';
import {
    PlusCircle,
    MessageSquare,
    Database,
    BookOpen,
    History,
    Rocket,
    Sun,
    Moon,
    LogOut,
    PanelLeftClose,
    Edit2,
    Check,
    Trash2,
    PanelLeftOpen,
    Briefcase,
    Cpu
} from 'lucide-react';
import { Session } from '../../services/api';
import { cn } from '../../lib/utils';

interface SidebarProps {
    isOpen: boolean;
    onToggle: () => void;
    onNewChat: () => void;
    sessions: Session[];
    currentSessionId: number | null;
    onSelectSession: (id: number) => void;
    onDeleteSession: (e: React.MouseEvent, id: number) => void;
    onStartEditing: (e: React.MouseEvent, s: Session) => void;
    onSaveTitle: (e: React.MouseEvent, id: number) => void;
    editingSessionId: number | null;
    tempTitle: string;
    setTempTitle: (val: string) => void;
    theme: 'dark' | 'light';
    onThemeToggle: () => void;
    userName: string;
    onLogout: () => void;
    onOpenSettings: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
    isOpen, onToggle, onNewChat, sessions, currentSessionId, onSelectSession,
    onDeleteSession, onStartEditing, onSaveTitle, editingSessionId,
    tempTitle, setTempTitle, theme, onThemeToggle, userName, onLogout, onOpenSettings
}) => {
    return (
        <aside className={cn(
            "sidebar-transition bg-secondary flex flex-col h-full border-r border-border-main relative z-30 shadow-2xl",
            isOpen ? "w-[300px]" : "w-[80px]"
        )}>
            {/* Branding Section with Integrated Toggle */}
            <div className={cn("h-20 flex items-center px-6 border-b border-border-main/50", isOpen ? "justify-between" : "justify-center px-0")}>
                {isOpen ? (
                    <div className="flex items-center justify-between w-full animate-in fade-in duration-500">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-accent-primary flex items-center justify-center shadow-lg shadow-accent-primary/20">
                                <Cpu className="w-6 h-6 text-white" />
                            </div>
                            <div>
                                <p className="text-sm font-black text-text-primary tracking-tight leading-none uppercase">CV ENGINE</p>
                            </div>
                        </div>
                        <button onClick={onToggle} className="p-2.5 hover:bg-surface rounded-xl text-text-muted hover:text-text-primary transition-all">
                            <PanelLeftClose className="w-5 h-5" />
                        </button>
                    </div>
                ) : (
                    <button onClick={onToggle} className="w-12 h-12 rounded-xl bg-accent-primary flex items-center justify-center shadow-lg shadow-accent-primary/10 hover:scale-105 transition-transform group relative">
                        <Briefcase className="w-5 h-5 text-white" />
                        {/* Mini Tooltip for Toggle */}
                        <div className="absolute left-16 top-1/2 -translate-y-1/2 bg-surface border border-border-main px-3 py-1.5 rounded-lg text-xs font-bold text-text-primary opacity-0 group-hover:opacity-100 pointer-events-none transition-all whitespace-nowrap shadow-2xl z-[100] translate-x-2 group-hover:translate-x-0">
                            Expand Sidebar
                        </div>
                    </button>
                )}
            </div>

            {/* Main Controls */}
            <div className={cn("p-4", isOpen ? "" : "flex justify-center")}>
                <button
                    onClick={onNewChat}
                    className={cn(
                        "flex items-center gap-3 rounded-2xl bg-surface border border-border-main shadow-sm hover:border-accent-primary/40 transition-all group overflow-visible active:scale-95 relative",
                        isOpen ? "w-full px-4 py-3.5" : "w-12 h-12 justify-center"
                    )}
                >
                    <PlusCircle className="w-5 h-5 text-accent-primary group-hover:scale-110 transition-transform" />
                    {isOpen && <span className="text-sm font-bold text-text-primary">New Session</span>}
                    {!isOpen && (
                        <div className="absolute left-16 top-1/2 -translate-y-1/2 bg-surface border border-border-main px-3 py-1.5 rounded-lg text-xs font-bold text-text-primary opacity-0 group-hover:opacity-100 pointer-events-none transition-all whitespace-nowrap shadow-2xl z-[100] translate-x-2 group-hover:translate-x-0">
                            New Session
                        </div>
                    )}
                </button>
            </div>

            {/* Navigation */}
            <nav className={cn(
                "flex-1 px-4 space-y-12 no-scrollbar py-6",
                isOpen ? "overflow-y-auto" : "overflow-visible"
            )}>
                <div className="space-y-1">
                    <div className="space-y-1">
                        <button title="Career Market" className={cn("w-full flex items-center rounded-2xl transition-all group relative", isOpen ? "gap-3 px-3 py-3 hover:bg-surface" : "justify-center py-4 hover:bg-surface")}>
                            <Database className="w-5 h-5 text-text-secondary group-hover:text-accent-primary transition-colors" />
                            {isOpen && <span className="text-[13px] font-bold text-text-secondary group-hover:text-text-primary truncate transition-colors">Career Market</span>}
                            {!isOpen && (
                                <div className="absolute left-16 top-1/2 -translate-y-1/2 bg-surface border border-border-main px-3 py-1.5 rounded-lg text-xs font-bold text-text-primary opacity-0 group-hover:opacity-100 pointer-events-none transition-all whitespace-nowrap shadow-2xl z-[100] translate-x-2 group-hover:translate-x-0">
                                    Career Market
                                </div>
                            )}
                        </button>
                        <button title="Mastery Guides" className={cn("w-full flex items-center rounded-2xl transition-all group relative", isOpen ? "gap-3 px-3 py-3 hover:bg-surface" : "justify-center py-4 hover:bg-surface")}>
                            <BookOpen className="w-5 h-5 text-text-secondary group-hover:text-accent-primary transition-colors" />
                            {isOpen && <span className="text-[13px] font-bold text-text-secondary group-hover:text-text-primary truncate transition-colors">Mastery Guides</span>}
                            {!isOpen && (
                                <div className="absolute left-16 top-1/2 -translate-y-1/2 bg-surface border border-border-main px-3 py-1.5 rounded-lg text-xs font-bold text-text-primary opacity-0 group-hover:opacity-100 pointer-events-none transition-all whitespace-nowrap shadow-2xl z-[100] translate-x-2 group-hover:translate-x-0">
                                    Mastery Guides
                                </div>
                            )}
                        </button>
                    </div>
                </div>

                <div className="space-y-1">
                    {isOpen && (
                        <div className="px-2 mb-4 items-center gap-2 flex">
                            <History className="w-3.5 h-3.5 text-text-secondary/20" />
                            <span className="text-[11px] font-black text-text-secondary/40 uppercase tracking-[0.4em]">History</span>
                        </div>
                    )}
                    <div className={cn(
                        "space-y-0.5 no-scrollbar",
                        isOpen ? "max-h-[400px] overflow-y-auto" : "overflow-visible"
                    )}>
                        {sessions.slice(0, isOpen ? 25 : 6).map(s => (
                            <div
                                key={s.id}
                                onClick={() => onSelectSession(s.id)}
                                className={cn(
                                    "group relative w-full flex items-center transition-all cursor-pointer rounded-xl border border-transparent shadow-xs mb-1",
                                    isOpen ? "gap-3 px-3 py-2.5 hover:border-border-main hover:bg-surface" : "justify-center py-4 hover:bg-surface",
                                    currentSessionId === s.id ? "bg-surface border-border-main text-text-primary" : "text-text-secondary/60 hover:text-text-primary"
                                )}
                            >
                                {currentSessionId === s.id && <div className="absolute left-[-4px] top-1/2 -translate-y-1/2 w-1.5 h-7 bg-accent-primary rounded-r-full shadow-[0_0_15px_rgba(99,102,241,0.5)]"></div>}

                                {isOpen ? (
                                    <>
                                        {editingSessionId === s.id ? (
                                            <input
                                                autoFocus
                                                className="flex-1 bg-transparent border-none outline-none text-text-primary text-sm font-bold"
                                                value={tempTitle}
                                                onChange={(e) => setTempTitle(e.target.value)}
                                                onBlur={(e) => onSaveTitle(e as any, s.id)}
                                                onKeyDown={(e) => e.key === 'Enter' && onSaveTitle(e as any, s.id)}
                                            />
                                        ) : (
                                            <span className="flex-1 truncate tracking-tight text-[13px] font-bold">{s.title}</span>
                                        )}
                                        <div className="opacity-0 group-hover:opacity-100 flex items-center gap-1 transition-opacity">
                                            <button onClick={(e) => onStartEditing(e, s)} className="p-1 hover:text-accent-primary"><Edit2 className="w-3.5 h-3.5" /></button>
                                            <button onClick={(e) => onDeleteSession(e, s.id)} className="p-1 hover:text-red-500"><Trash2 className="w-3.5 h-3.5" /></button>
                                        </div>
                                    </>
                                ) : (
                                    <>
                                        <MessageSquare className={cn("w-5 h-5 transition-transform group-hover:scale-110", currentSessionId === s.id ? "opacity-100 text-accent-primary" : "opacity-40 group-hover:opacity-100")} />
                                        {/* Collapsed State Tooltip for History */}
                                        <div className="absolute left-16 top-1/2 -translate-y-1/2 bg-surface border border-border-main px-3 py-1.5 rounded-lg text-xs font-bold text-text-primary opacity-0 group-hover:opacity-100 pointer-events-none transition-all whitespace-nowrap shadow-2xl z-[100] translate-x-2 group-hover:translate-x-0">
                                            {s.title}
                                        </div>
                                    </>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </nav>

            {/* Footer Actions */}
            <div className={cn("p-4 bg-secondary border-t border-border-main", !isOpen && "items-center")}>
                <button title="Upgrade to Pro" className={cn("shimmer-bg w-full flex items-center rounded-2xl transition-all group border border-accent-primary/10 shadow-xs relative", isOpen ? "gap-4 px-4 py-3 bg-accent-primary/5" : "justify-center py-4")}>
                    <Rocket className="w-5 h-5 text-accent-primary flex-shrink-0" />
                    {isOpen && (
                        <div className="flex-1 text-left">
                            <p className="text-[11px] font-black text-text-primary uppercase">PREMIUM ACCESS</p>
                        </div>
                    )}
                    {!isOpen && (
                        <div className="absolute left-16 top-1/2 -translate-y-1/2 bg-surface border border-border-main px-3 py-1.5 rounded-lg text-xs font-bold text-text-primary opacity-0 group-hover:opacity-100 pointer-events-none transition-all whitespace-nowrap shadow-2xl z-[100] translate-x-2 group-hover:translate-x-0">
                            Premium Access
                        </div>
                    )}
                </button>

                <div className="mt-4 space-y-3">
                    {/* User Profile / Settings */}
                    <button
                        type="button"
                        onClick={onOpenSettings}
                        className={cn(
                            "flex items-center rounded-2xl bg-surface border border-border-main/50 hover:border-accent-primary/30 transition-all cursor-pointer shadow-sm group relative",
                            isOpen ? "w-full gap-3 p-3" : "w-12 h-12 justify-center mx-auto"
                        )}
                    >
                        <div className="w-9 h-9 rounded-xl bg-linear-to-br from-indigo-500 to-purple-600 flex items-center justify-center font-black text-white text-xs shadow-lg flex-shrink-0">
                            {userName.charAt(0).toUpperCase()}
                        </div>
                        {isOpen && (
                            <div className="flex-1 overflow-hidden text-left">
                                <p className="text-sm font-black text-text-primary truncate leading-none">{userName}</p>
                            </div>
                        )}
                        {!isOpen && (
                            <div className="absolute left-16 top-1/2 -translate-y-1/2 bg-surface border border-border-main px-3 py-1.5 rounded-lg text-xs font-bold text-text-primary opacity-0 group-hover:opacity-100 pointer-events-none transition-all whitespace-nowrap shadow-2xl z-[100] translate-x-3 group-hover:translate-x-0">
                                Settings
                            </div>
                        )}
                    </button>

                    {/* Dedicated Logout Button */}
                    <button
                        type="button"
                        onClick={onLogout}
                        className={cn(
                            "flex items-center rounded-2xl border border-transparent hover:bg-red-500/10 hover:border-red-500/20 text-text-secondary hover:text-red-500 transition-all cursor-pointer group relative",
                            isOpen ? "w-full gap-3 p-3" : "w-12 h-12 justify-center mx-auto"
                        )}
                    >
                        <LogOut className="w-5 h-5 flex-shrink-0" />
                        {isOpen && <span className="text-sm font-bold">Sign Out</span>}
                        {!isOpen && (
                            <div className="absolute left-16 top-1/2 -translate-y-1/2 bg-surface border border-border-main px-3 py-1.5 rounded-lg text-xs font-bold text-text-primary opacity-0 group-hover:opacity-100 pointer-events-none transition-all whitespace-nowrap shadow-2xl z-[100] translate-x-3 group-hover:translate-x-0">
                                Sign Out
                            </div>
                        )}
                    </button>
                </div>
            </div>
        </aside>
    );
};

export default Sidebar;
