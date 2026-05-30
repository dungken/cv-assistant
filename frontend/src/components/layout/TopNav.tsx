import { Activity, TrendingUp, Settings, LogOut, Shield, ChevronDown } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useState, useRef, useEffect } from 'react';
import { cn } from '../../lib/utils';

interface TopNavProps {
    userName: string;
    userRole?: string;
    isAuthenticated: boolean;
    onRequireAuth: (view: 'login' | 'register') => void;
    onLogout: () => void;
    onOpenSettings: () => void;
    onOpenAdmin?: () => void;
}

export default function TopNav({
    userName, userRole, isAuthenticated, onRequireAuth, onLogout, onOpenSettings, onOpenAdmin,
}: TopNavProps) {
    const location = useLocation();
    const navigate = useNavigate();
    const [userMenuOpen, setUserMenuOpen] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handler = (e: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(e.target as Node)) setUserMenuOpen(false);
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, []);

    const navLinks = [
        { path: '/cv-health', label: 'CV Health', icon: Activity },
        { path: '/market-intel', label: 'Market Intel', icon: TrendingUp },
        ...(isAuthenticated && userRole === 'Admin' && onOpenAdmin ? [{ path: '/admin', label: 'Admin', icon: Shield }] : []),
    ];

    return (
        <header className="h-14 shrink-0 sticky top-0 z-50 flex items-center px-6 gap-6 bg-secondary border-b border-white/5">
            {/* Brand */}
            <div className="flex items-center gap-2 shrink-0">
                <div className="w-7 h-7 rounded-lg bg-accent-primary/20 flex items-center justify-center">
                    <Activity className="w-4 h-4 text-accent-primary" strokeWidth={2} />
                </div>
                <span className="text-sm font-black font-outfit tracking-tight text-text-primary">CV Assistant</span>
            </div>

            {/* Divider */}
            <div className="h-5 w-px bg-white/8" />

            {/* Nav links */}
            <nav className="flex items-center gap-1">
                {navLinks.map(({ path, label, icon: Icon }) => {
                    const active = location.pathname === path;
                    return (
                        <button
                            key={path}
                            type="button"
                            onClick={() => path === '/admin' && onOpenAdmin ? onOpenAdmin() : navigate(path)}
                            className={cn(
                                'flex items-center gap-2 h-9 px-3.5 rounded-xl text-sm font-semibold transition-colors',
                                active
                                    ? 'bg-surface-hover text-text-primary'
                                    : 'text-text-secondary hover:text-text-primary hover:bg-surface-hover/60',
                            )}
                        >
                            <Icon className="w-4 h-4" strokeWidth={1.5} />
                            {label}
                        </button>
                    );
                })}
            </nav>

            {/* Spacer */}
            <div className="flex-1" />

            {/* Right actions */}
            {!isAuthenticated ? (
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => onRequireAuth('login')}
                        className="h-9 px-4 rounded-xl text-sm font-bold text-text-secondary hover:text-text-primary transition-colors hover:bg-white/5"
                    >
                        Đăng nhập
                    </button>
                    <button
                        onClick={() => onRequireAuth('register')}
                        className="h-9 px-4 rounded-xl text-sm font-bold bg-accent-primary text-white hover:bg-accent-dark transition-colors shadow-lg shadow-accent-primary/20"
                    >
                        Đăng ký miễn phí
                    </button>
                </div>
            ) : (
                <div className="relative" ref={menuRef}>
                    <button
                        type="button"
                        onClick={() => setUserMenuOpen(v => !v)}
                        className="flex items-center gap-2 h-9 px-2.5 rounded-xl hover:bg-white/5 transition-colors"
                    >
                        <div className="w-7 h-7 rounded-full bg-accent-primary/20 flex items-center justify-center font-bold text-accent-primary text-xs ring-1 ring-accent-primary/20">
                            {userName.charAt(0).toUpperCase()}
                        </div>
                        <span className="text-sm font-semibold text-text-primary max-w-[100px] truncate hidden sm:block">
                            {userName}
                        </span>
                        <ChevronDown className={cn('w-3.5 h-3.5 text-text-muted transition-transform duration-200', userMenuOpen && 'rotate-180')} />
                    </button>

                    {userMenuOpen && (
                        <div className="absolute right-0 top-full mt-2 w-52 bg-surface border border-white/10 rounded-2xl shadow-2xl shadow-black/50 overflow-hidden animate-in fade-in zoom-in-95 duration-150 z-50">
                            {/* User info */}
                            <div className="px-4 py-3 border-b border-white/5 flex items-center gap-3">
                                <div className="w-8 h-8 rounded-full bg-accent-primary/20 flex items-center justify-center font-bold text-accent-primary text-sm shrink-0">
                                    {userName.charAt(0).toUpperCase()}
                                </div>
                                <div className="min-w-0">
                                    <div className="text-sm font-semibold text-text-primary truncate">{userName}</div>
                                    {userRole === 'Admin' && (
                                        <div className="text-[10px] text-emerald-400 font-bold uppercase tracking-wide">Admin</div>
                                    )}
                                </div>
                            </div>
                            <div className="p-1.5 space-y-0.5">
                                <button
                                    type="button"
                                    onClick={() => { onOpenSettings(); setUserMenuOpen(false); }}
                                    className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl hover:bg-white/5 text-sm text-text-secondary hover:text-text-primary transition-colors"
                                >
                                    <Settings className="w-3.5 h-3.5" strokeWidth={1.5} />
                                    Cài đặt
                                </button>
                                <button
                                    type="button"
                                    onClick={() => { onLogout(); setUserMenuOpen(false); }}
                                    className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl hover:bg-rose-500/10 text-sm text-text-secondary hover:text-rose-400 transition-colors"
                                >
                                    <LogOut className="w-3.5 h-3.5" />
                                    Đăng xuất
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </header>
    );
}
