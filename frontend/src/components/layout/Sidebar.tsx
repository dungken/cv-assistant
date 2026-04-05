import React, { useState, useEffect, useRef } from 'react';
import {
    Plus, MessageSquare, Database, BookOpen, History, Rocket, Sun, Moon, LogOut,
    PanelLeftClose, Edit2, Check, Trash2, PanelLeftOpen, Briefcase, Settings,
    Search, MoreVertical, Sparkles, UserCircle, HelpCircle, Share2, Pin,
    AlertCircle, Menu, SquarePen, BarChart3, Shield, Home
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useLocation, useNavigate } from 'react-router-dom';
import { Session } from '../../services/api';
import { cn } from '../../lib/utils';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Dialog, DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogContent } from '../ui/Dialog';

interface SidebarProps {
    isOpen: boolean;
    onToggle: () => void;
    onNewChat: () => void;
    sessions: Session[];
    currentSessionId: number | null;
    onSelectSession: (id: number) => void;
    onDeleteSession: (e: React.MouseEvent | null, id: number) => void;
    onStartEditing: (e: React.MouseEvent | null, s: Session) => void;
    onSaveTitle: (e: React.MouseEvent | null, id: number, customTitle?: string) => void;
    editingSessionId: number | null;
    tempTitle: string;
    setTempTitle: (val: string) => void;
    theme: 'dark' | 'light';
    onThemeToggle: () => void;
    userName: string;
    onLogout: () => void;
    onOpenSettings: () => void;
    onSearchToggle: () => void;
    onOpenProfile?: () => void;
    onOpenCvList?: () => void;
    onOpenMemory?: () => void;
    onOpenMarket?: () => void;
    onOpenAdmin?: () => void;
    userRole?: string;
}

const Sidebar: React.FC<SidebarProps> = ({
    isOpen, onToggle, onNewChat, sessions, currentSessionId, onSelectSession,
    onDeleteSession, onStartEditing, onSaveTitle, editingSessionId,
    tempTitle, setTempTitle, theme, onThemeToggle, userName, onLogout, onOpenSettings,
    onSearchToggle, onOpenProfile, onOpenCvList, onOpenMemory, onOpenMarket, onOpenAdmin, userRole
}) => {
    const location = useLocation();
    const navigate = useNavigate();
    const { t } = useTranslation();
    const [activeMenuId, setActiveMenuId] = useState<number | null>(null);
    const [menuPosition, setMenuPosition] = useState({ top: 0, left: 0 });
    const menuRef = useRef<HTMLDivElement>(null);
    const scrollContainerRef = useRef<HTMLDivElement>(null);

    const [isDeleteOpen, setIsDeleteOpen] = useState(false);
    const [isRenameOpen, setIsRenameOpen] = useState(false);
    const [targetSession, setTargetSession] = useState<Session | null>(null);
    const [renameValue, setRenameValue] = useState("");

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setActiveMenuId(null);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    useEffect(() => {
        const handleClose = () => setActiveMenuId(null);
        window.addEventListener('resize', handleClose);
        const scrollEl = scrollContainerRef.current;
        if (scrollEl) scrollEl.addEventListener('scroll', handleClose);
        return () => {
            window.removeEventListener('resize', handleClose);
            scrollEl?.removeEventListener('scroll', handleClose);
        };
    }, []);

    const handleMenuToggle = (e: React.MouseEvent, s: Session) => {
        e.stopPropagation();
        if (activeMenuId === s.id) {
            setActiveMenuId(null);
        } else {
            const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
            setMenuPosition({ 
                top: rect.top + (rect.height / 2) - 10, 
                left: rect.left + rect.width + 12 
            });
            setActiveMenuId(s.id);
            setTargetSession(s);
        }
    };

    const handleOpenDelete = () => {
        setIsDeleteOpen(true);
        setActiveMenuId(null);
    };

    const handleOpenRename = () => {
        if (targetSession) {
            setRenameValue(targetSession.title);
            setIsRenameOpen(true);
            setActiveMenuId(null);
        }
    };

    const confirmDelete = () => {
        if (targetSession) {
            onDeleteSession(null, targetSession.id);
            setIsDeleteOpen(false);
            setTargetSession(null);
        }
    };

    const confirmRename = () => {
        if (targetSession && renameValue.trim()) {
            onSaveTitle(null, targetSession.id, renameValue.trim());
            setIsRenameOpen(false);
            setTargetSession(null);
        }
    };

    return (
        <>
            <aside className={cn(
                "sidebar-transition bg-secondary flex flex-col h-full relative z-50 shadow-2xl shadow-black/5",
                isOpen ? "w-[300px] overflow-visible" : "w-[68px] overflow-hidden"
            )}>
                <div className={cn("h-16 flex items-center px-[10px] shrink-0 transition-all duration-400 relative overflow-hidden")}>
                    <Button 
                        variant="ghost" 
                        size="icon" 
                        onClick={onToggle} 
                        className="w-12 h-12 hover:bg-surface-hover rounded-full flex items-center justify-center transition-all duration-400 shrink-0"
                    >
                        <Menu className="w-5 h-5" strokeWidth={1.5} />
                    </Button>
                    <div className={cn("sidebar-content-slide absolute right-[10px]", isOpen ? "open" : "closed opacity-0 pointer-events-none")}>
                        <Button variant="ghost" size="icon" onClick={onSearchToggle} className="w-12 h-12 hover:bg-surface-hover rounded-full">
                            <Search className="w-5 h-5 text-text-secondary" strokeWidth={1.5} />
                        </Button>
                    </div>
                </div>

                <div className="px-0 pt-2 pb-4 shrink-0 transition-all duration-400">
                    <Button
                        onClick={onNewChat}
                        variant={isOpen ? "secondary" : "ghost"}
                        className={cn(
                            "h-12 flex items-center !justify-start transition-all duration-400 overflow-hidden mx-[10px] px-[14px]",
                            isOpen ? "w-[calc(100%-20px)] bg-surface shadow-sm hover:shadow-md rounded-xl" : "w-12 hover:bg-surface-hover rounded-full"
                        )}
                    >
                        <SquarePen className="w-5 h-5 text-text-primary shrink-0" strokeWidth={1.5} />
                        <span className={cn("sidebar-content-slide font-bold text-[14px] text-text-primary ml-4", isOpen ? "open" : "closed")}>
                            {t('chat.new_chat')}
                        </span>
                    </Button>
                </div>

                <div ref={scrollContainerRef} className={cn("flex-1 flex flex-col space-y-1 overflow-y-auto floating-scrollbar scroll-smooth", !isOpen && "no-scrollbar")}>


                    <div className="space-y-1">
                        <Button variant="ghost" className={cn(
                            "h-10 flex items-center !justify-start group transition-all duration-400 overflow-hidden mx-[10px] px-[14px]",
                            isOpen ? "w-[calc(100%-20px)] rounded-xl" : "w-12 rounded-full"
                        )}>
                            <Sparkles className="w-5 h-5 text-text-secondary group-hover:scale-110 transition-transform shrink-0" strokeWidth={1.5} />
                            <span className={cn("sidebar-content-slide font-bold text-[13px] text-left ml-4", isOpen ? "open" : "closed")}>
                                {t('sidebar.designer')}
                            </span>
                        </Button>
                        <Button 
                            onClick={onOpenMarket}
                            variant="ghost" 
                            className={cn(
                                "h-10 flex items-center !justify-start group transition-all duration-400 overflow-hidden mx-[10px] px-[14px] border",
                                isOpen ? "w-[calc(100%-20px)] rounded-xl border-transparent" : "w-12 rounded-full shadow-lg shadow-black/5 bg-surface/50 border-white/5"
                            )}
                        >
                            <BarChart3 className="w-5 h-5 text-text-secondary group-hover:scale-110 transition-transform shrink-0" strokeWidth={1.5} />
                            <span className={cn("sidebar-content-slide font-bold text-[13px] text-left ml-4 text-text-primary", isOpen ? "open" : "closed")}>
                                {t('sidebar.market')}
                            </span>
                        </Button>
                        {userRole === 'Admin' && onOpenAdmin && (
                            <Button 
                                onClick={onOpenAdmin}
                                variant="ghost" 
                                className={cn(
                                    "h-10 flex items-center !justify-start group transition-all duration-400 overflow-hidden mx-[10px] px-[14px] border",
                                    isOpen ? "w-[calc(100%-20px)] rounded-xl border-transparent" : "w-12 rounded-full shadow-lg shadow-black/5 bg-surface/50 border-white/5",
                                    location.pathname === '/admin' && "bg-surface-hover text-white border-white/10 shadow-black/20"
                                )}
                            >
                                <Shield className={cn("w-5 h-5 transition-transform group-hover:scale-110 shrink-0", location.pathname === '/admin' ? "text-white" : "text-text-secondary")} strokeWidth={1.5} />
                                <span className={cn("sidebar-content-slide font-bold text-[13px] text-left ml-4 transition-all", isOpen ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-4", location.pathname === '/admin' ? "text-white" : "text-text-secondary")}>
                                    {t('sidebar.admin')}
                                </span>
                            </Button>
                        )}
                    </div>

                    <div className="space-y-1 pt-4 pb-12">
                        <div className="px-6 mb-2 h-6">
                             <span className={cn("sidebar-content-slide text-[11px] font-black tracking-widest text-text-muted/60 uppercase", isOpen ? "open" : "closed")}>
                                {t('sidebar.chats_header')}
                             </span>
                        </div>
                        <div className="space-y-0.5">
                            {sessions.map(s => (
                                <div key={s.id} className="relative group/item px-3 overflow-visible">
                                    <Button
                                        variant={currentSessionId === s.id ? "secondary" : "ghost"}
                                        onClick={() => onSelectSession(s.id)}
                                        className={cn(
                                            "w-full justify-start text-[13px] h-10 px-3 rounded-full border-none transition-opacity overflow-hidden",
                                            !isOpen ? "opacity-0 pointer-events-none" : "opacity-100",
                                            "group-hover/item:bg-surface-hover",
                                            activeMenuId === s.id && "bg-surface-hover"
                                        )}
                                    >
                                        <div className="flex items-center justify-between w-full min-w-[200px] pr-6">
                                            <span className={cn(
                                                "flex-1 truncate tracking-tight text-left text-text-secondary font-medium",
                                                currentSessionId === s.id && "font-bold text-text-primary",
                                                !isOpen && "opacity-0 invisible"
                                            )}>
                                                {s.title}
                                            </span>
                                        </div>
                                    </Button>
                                    {isOpen && (
                                        <div className={cn("absolute right-6 top-1/2 -translate-y-1/2 opacity-0 group-hover/item:opacity-100 transition-all z-20", activeMenuId === s.id && "opacity-100")}>
                                             <button onClick={(e) => handleMenuToggle(e, s)} className={cn("p-1 hover:bg-canvas rounded-full text-text-secondary transition-colors", activeMenuId === s.id && "bg-surface-hover opacity-100")}>
                                                <MoreVertical className="w-4 h-4" />
                                            </button>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="mt-auto pb-4 space-y-1 shrink-0">
                    <Button variant="ghost" className={cn("flex items-center justify-start transition-all duration-400 overflow-hidden mx-[10px] px-[14px]", isOpen ? "h-10 w-[calc(100%-20px)] rounded-xl opacity-100" : "opacity-0 pointer-events-none w-12 h-10")}>
                        <Rocket className="w-5 h-5 text-text-secondary shrink-0" />
                        <span className={cn("sidebar-content-slide text-[13px] font-bold ml-4", isOpen ? "open" : "closed")}>Upgrade to Plus</span>
                    </Button>
                    <Button onClick={onOpenSettings} variant="ghost" className={cn("group transition-all duration-400 flex items-center !justify-start overflow-hidden mx-[10px] px-[14px]", isOpen ? "w-[calc(100%-20px)] h-11 rounded-xl" : "w-12 h-11 rounded-full hover:bg-surface-hover")}>
                        <Settings className="w-5 h-5 text-text-secondary group-hover:rotate-45 transition-transform shrink-0" strokeWidth={1.5} />
                        <span className={cn("sidebar-content-slide text-[13px] font-bold ml-4", isOpen ? "open" : "closed")}>Settings</span>
                    </Button>
                    <div className="relative px-0 mt-2">
                         <div className={cn("flex items-center transition-all duration-400 h-16", isOpen ? "justify-between" : "justify-start")}>
                            <div className="relative shrink-0">
                                {isOpen ? (
                                    <div className="w-12 h-12 flex items-center justify-center mx-[10px]">
                                        <div className="w-8 h-8 rounded-full bg-surface-hover flex items-center justify-center font-black text-text-primary text-xs shadow-lg shadow-black/20 ring-1 ring-white/10">
                                            {userName.charAt(0).toUpperCase()}
                                        </div>
                                    </div>
                                ) : (
                                    <button onClick={onLogout} className="w-12 h-12 mx-[10px] px-[14px] flex items-center justify-center bg-surface/50 hover:bg-surface-hover rounded-full transition-all text-text-secondary hover:text-rose-500 shadow-sm active:scale-95">
                                        <LogOut className="w-5 h-5" />
                                    </button>
                                )}
                            </div>
                            <div className={cn("sidebar-content-slide flex-1 flex items-center justify-between pl-1 pr-6", isOpen ? "open opacity-100" : "closed opacity-0 pointer-events-none")}>
                                <div className="flex flex-col min-w-0 cursor-pointer" onClick={onOpenProfile}>
                                    <div className="flex items-center gap-1.5 overflow-hidden">
                                        <span className="text-[13px] font-bold truncate text-text-primary font-outfit uppercase tracking-tight hover:text-accent-primary transition-colors">{userName}</span>
                                        {userRole === 'Admin' && (
                                            <Badge variant="outline" className="h-4 px-1 text-[8px] border-emerald-500/30 text-emerald-500/80 bg-emerald-500/5 normal-case font-bold">ADM</Badge>
                                        )}
                                    </div>
                                    <span className="text-[9px] text-text-muted font-black uppercase tracking-[0.1em]">{userRole === 'Admin' ? 'Administrator' : 'Free tier'}</span>
                                </div>
                                <div className="flex items-center gap-1 shrink-0">
                                    {onOpenCvList && (
                                        <button onClick={onOpenCvList} title="My CVs" className="p-2 text-text-muted hover:text-accent-primary transition-all bg-surface/30 hover:bg-surface-hover rounded-full">
                                            <Briefcase className="w-4 h-4" />
                                        </button>
                                    )}
                                    {onOpenMemory && (
                                        <button onClick={onOpenMemory} title={t('sidebar.memory')} className="p-2 text-text-muted hover:text-accent-primary transition-all bg-surface/30 hover:bg-surface-hover rounded-full">
                                            <Sparkles className="w-4 h-4" />
                                        </button>
                                    )}
                                    <button onClick={onLogout} className="p-2 text-text-muted hover:text-rose-500 transition-all bg-surface/30 hover:bg-surface-hover rounded-full">
                                        <LogOut className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                         </div>
                    </div>
                </div>

                {activeMenuId && (
                    <div ref={menuRef} style={{ position: 'fixed', top: `${menuPosition.top}px`, left: `${menuPosition.left}px` }} className="w-52 bg-surface shadow-2xl rounded-2xl py-1.5 border border-white/5 animate-in fade-in zoom-in-95 duration-200 z-[9999] backdrop-blur-3xl px-0 overflow-hidden" onClick={(e) => e.stopPropagation()}>
                        <button className="flex w-full items-center gap-3 px-4 py-2 hover:bg-surface-hover text-text-primary text-left" onClick={() => setActiveMenuId(null)}>
                            <Share2 className="w-4 h-4 text-text-secondary" />
                            <span className="text-[13px] font-bold">Share conversation</span>
                        </button>
                        <button className="flex w-full items-center gap-3 px-4 py-2 hover:bg-surface-hover text-text-primary text-left" onClick={() => setActiveMenuId(null)}>
                            <Pin className="w-4 h-4 text-text-secondary" />
                            <span className="text-[13px] font-bold">Pin</span>
                        </button>
                        <button onClick={handleOpenRename} className="flex w-full items-center gap-3 px-4 py-2 hover:bg-surface-hover text-text-primary text-left">
                            <Edit2 className="w-4 h-4 text-text-secondary" />
                            <span className="text-[13px] font-bold">Rename</span>
                        </button>
                        <div className="h-px bg-white/5 my-1 mx-2" />
                        <button onClick={handleOpenDelete} className="flex w-full items-center gap-3 px-4 py-2 hover:bg-red-500/10 text-red-500 text-left">
                            <Trash2 className="w-4 h-4" />
                            <span className="text-[13px] font-bold">Delete</span>
                        </button>
                    </div>
                )}
            </aside>
            <Dialog open={isRenameOpen} onOpenChange={setIsRenameOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Rename Chat</DialogTitle>
                        <DialogDescription>Enter a new name for this conversation.</DialogDescription>
                    </DialogHeader>
                    <div className="px-8 py-2">
                        <input 
                            className="w-full bg-secondary/80 text-text-primary rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-accent-primary/20 transition-all font-medium font-outfit" 
                            value={renameValue} 
                            onChange={(e) => setRenameValue(e.target.value)} 
                            autoFocus 
                            onKeyDown={(e) => e.key === 'Enter' && confirmRename()} 
                        />
                    </div>
                    <DialogFooter>
                        <Button variant="ghost" onClick={() => setIsRenameOpen(false)}>Cancel</Button>
                        <Button variant="default" onClick={confirmRename}>Save</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
            <Dialog open={isDeleteOpen} onOpenChange={setIsDeleteOpen}>
                <DialogContent>
                    <div className="p-6">
                        <DialogHeader className="p-0 flex flex-row items-center gap-4 mb-4">
                            <div className="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center shrink-0">
                                <Trash2 className="w-5 h-5 text-red-500" />
                            </div>
                            <DialogTitle className="text-xl m-0">Delete Chat?</DialogTitle>
                        </DialogHeader>
                        <DialogDescription className="text-[14px] px-1 line-clamp-3">
                            This will permanently delete <span className="font-bold text-text-primary">"{targetSession?.title}"</span>. This action cannot be undone.
                        </DialogDescription>
                        <div className="flex items-center justify-end gap-3 mt-8">
                            <Button variant="ghost" onClick={() => setIsDeleteOpen(false)} className="px-4 py-2 text-sm font-bold">Cancel</Button>
                            <Button variant="destructive" onClick={confirmDelete} className="bg-red-500 text-white hover:bg-red-600 px-6 py-2 text-sm font-bold rounded-full shadow-lg shadow-red-500/20">Delete</Button>
                        </div>
                    </div>
                </DialogContent>
            </Dialog>
        </>
    );
};

export default Sidebar;
