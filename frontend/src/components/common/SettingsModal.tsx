import React, { useState, useEffect, useCallback } from 'react';
import {
    X, Moon, Sun, Shield, Settings, Activity, CheckCircle,
    XCircle, Loader2, RefreshCw, User, Bell, Globe,
    Database, Layout as LayoutIcon, Smartphone, Cpu
} from 'lucide-react';
import axios from 'axios';
import { cn } from '../../lib/utils';
import { Button } from '../ui/Button';
import { useTranslation } from 'react-i18next';

interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
    theme: 'dark' | 'light';
    onThemeToggle: () => void;
    userName: string;
    defaultTab?: TabId;
}

const SERVICES = [
    { name: 'API Gateway', url: 'http://localhost:8081/api/health', label: 'C# / .NET 9' },
    { name: 'Chatbot AI', url: 'http://localhost:5004/health', label: 'Python / FastAPI' },
    { name: 'NER Extractor', url: 'http://localhost:5005/health', label: 'Python / Transformers' },
    { name: 'Skill Engine', url: 'http://localhost:5002/health', label: 'Python / SBERT' },
    { name: 'Career Engine', url: 'http://localhost:5003/health', label: 'Python / O*NET' },
];

type ServiceStatus = 'checking' | 'online' | 'offline';
type TabId = 'general' | 'appearance' | 'account' | 'health' | 'data' | 'security';

const SettingsModal: React.FC<SettingsModalProps> = ({
    isOpen,
    onClose,
    theme,
    onThemeToggle,
    userName,
    defaultTab = 'general'
}) => {
    const { t, i18n } = useTranslation();
    const [activeTab, setActiveTab] = useState<TabId>(defaultTab);
    const [statuses, setStatuses] = useState<Record<string, ServiceStatus>>({});

    // Reset tab when modal opens
    useEffect(() => {
        if (isOpen) {
            setActiveTab(defaultTab);
        }
    }, [isOpen, defaultTab]);

    const checkHealth = useCallback(async () => {
        const initial = Object.fromEntries(SERVICES.map(s => [s.name, 'checking' as ServiceStatus]));
        setStatuses(initial);
        await Promise.all(SERVICES.map(async (svc) => {
            try {
                await axios.get(svc.url, { timeout: 3000 });
                setStatuses(prev => ({ ...prev, [svc.name]: 'online' }));
            } catch {
                setStatuses(prev => ({ ...prev, [svc.name]: 'offline' }));
            }
        }));
    }, []);

    useEffect(() => {
        if (isOpen && activeTab === 'health') checkHealth();
    }, [isOpen, activeTab, checkHealth]);

    if (!isOpen) return null;

    const onlineCount = Object.values(statuses).filter(s => s === 'online').length;

    const sidebarItems = [
        { id: 'general', label: t('settings.tabs.general'), icon: Settings },
        { id: 'appearance', label: t('settings.tabs.appearance'), icon: LayoutIcon },
        { id: 'account', label: t('settings.tabs.account'), icon: User },
        { id: 'health', label: t('settings.tabs.health'), icon: Activity },
        { id: 'data', label: t('settings.tabs.data'), icon: Database, locked: true },
        { id: 'security', label: t('settings.tabs.security'), icon: Shield, locked: true },
    ];

    return (
        <div className="fixed inset-0 z-[1000] flex items-center justify-center p-4 bg-transparent backdrop-blur-[6px] animate-in fade-in duration-300">
            {/* Main Modal Container */}
            <div className="bg-surface w-full max-w-4xl h-[640px] rounded-[32px] shadow-[0_32px_128px_-16px_rgba(0,0,0,0.4)] border border-[rgba(var(--border-modal))] overflow-hidden flex animate-in zoom-in-95 duration-300">

                {/* Sidebar Navigation */}
                <div className="w-[280px] bg-[rgba(var(--bg-modal-sidebar))] border-r border-[rgba(var(--border-secondary))] flex flex-col p-6 pr-0">
                    <div className="flex-1 space-y-1 pr-4">
                        {sidebarItems.map((item) => (
                            <button
                                key={item.id}
                                onClick={() => !item.locked && setActiveTab(item.id as TabId)}
                                className={cn(
                                    "w-full flex items-center gap-3.5 px-4 py-3 rounded-2xl transition-all group font-medium text-[14px]",
                                    activeTab === item.id
                                        ? "bg-accent-primary/10 text-accent-primary shadow-sm"
                                        : "text-text-secondary hover:bg-[rgba(var(--bg-surface-hover))] hover:text-text-primary",
                                    item.locked && "opacity-40 cursor-not-allowed"
                                )}
                            >
                                <item.icon className={cn(
                                    "w-4.5 h-4.5 transition-colors",
                                    activeTab === item.id ? "text-accent-primary" : "text-text-muted group-hover:text-text-secondary"
                                )} />
                                <span>{item.label}</span>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Main Content Area */}
                <div className="flex-1 flex flex-col min-w-0 bg-transparent relative">
                    {/* Header */}
                    <div className="h-20 flex items-center justify-between px-10 border-b border-[rgba(var(--border-secondary))] shrink-0">
                        <h2 className="text-2xl font-bold font-outfit tracking-tight capitalize">
                            {sidebarItems.find(i => i.id === activeTab)?.label}
                        </h2>
                        <button
                            onClick={onClose}
                            className="w-10 h-10 flex items-center justify-center hover:bg-[rgba(var(--bg-surface-hover))] rounded-full transition-all text-text-muted hover:text-text-primary active:scale-90"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Content Body */}
                    <div className="flex-1 overflow-y-auto floating-scrollbar px-10 py-12 scroll-smooth">
                        <div className="max-w-2xl animate-in slide-in-from-right-4 fade-in duration-500">

                            {/* General Tab */}
                            {activeTab === 'general' && (
                                <div className="space-y-10">
                                    <div className="flex items-center justify-between group">
                                        <div className="space-y-1.5">
                                            <p className="font-bold text-[15px]">{t('settings.general.lang_title')}</p>
                                            <p className="text-sm text-text-muted leading-relaxed">{t('settings.general.lang_desc')}</p>
                                        </div>
                                        <div className="flex items-center gap-2 text-sm font-bold text-text-secondary bg-[rgba(var(--bg-surface-hover))] px-4 py-2.5 rounded-xl border border-[rgba(var(--border-secondary))] group-hover:bg-accent-primary/5 transition-colors cursor-pointer">
                                            {i18n.language === 'vi' ? 'Tiếng Việt' : 'English (US)'}
                                            <Globe className="w-4 h-4 text-text-muted" />
                                        </div>
                                    </div>

                                    <div className="h-px bg-[rgba(var(--border-secondary))] w-full" />

                                    <div className="flex items-center justify-between group">
                                        <div className="space-y-1.5">
                                            <p className="font-bold text-[15px]">{t('settings.general.advanced_title')}</p>
                                            <p className="text-sm text-text-muted leading-relaxed">{t('settings.general.advanced_desc')}</p>
                                        </div>
                                        <div className="w-12 h-6 bg-text-muted/10 rounded-full relative p-1 cursor-not-allowed opacity-40">
                                            <div className="w-4 h-4 bg-text-muted/30 rounded-full" />
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Appearance Tab */}
                            {activeTab === 'appearance' && (
                                <div className="space-y-10">
                                    <div className="flex items-center justify-between group">
                                        <div className="space-y-1.5 flex-1">
                                            <p className="font-bold text-[15px]">{t('settings.appearance.theme_title')}</p>
                                            <p className="text-sm text-text-muted leading-relaxed">{t('settings.appearance.theme_desc')}</p>
                                        </div>
                                        <button
                                            onClick={onThemeToggle}
                                            className="flex items-center gap-3 px-5 py-3 bg-[rgba(var(--bg-surface-hover))] hover:bg-accent-primary/5 border border-[rgba(var(--border-secondary))] rounded-2xl transition-all shadow-sm group active:scale-95"
                                        >
                                            {theme === 'dark' ? (
                                                <><Moon className="w-4.5 h-4.5 text-accent-primary" /><span className="text-sm font-bold">Dark Mode</span></>
                                            ) : (
                                                <><Sun className="w-4.5 h-4.5 text-amber-400" /><span className="text-sm font-bold">Light Mode</span></>
                                            )}
                                        </button>
                                    </div>

                                    <div className="h-px bg-white/5 w-full" />

                                    <div className="flex items-center justify-between group opacity-40">
                                        <div className="space-y-1.5">
                                            <p className="font-bold text-[15px]">{t('settings.appearance.palette_title')}</p>
                                            <p className="text-sm text-text-muted leading-relaxed">{t('settings.appearance.palette_desc')}</p>
                                        </div>
                                        <div className="flex gap-2">
                                            <div className="w-6 h-6 rounded-full bg-accent-primary border-2 border-accent-primary/20" />
                                            <div className="w-6 h-6 rounded-full bg-emerald-500/10 border border-emerald-500/20" />
                                            <div className="w-6 h-6 rounded-full bg-amber-500/10 border border-amber-500/20" />
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Account Tab */}
                            {activeTab === 'account' && (
                                <div className="space-y-10">
                                    <div className="flex items-center gap-6 p-6 bg-[rgba(var(--bg-surface-hover))] rounded-[24px] border border-[rgba(var(--border-secondary))]">
                                        <div className="w-20 h-20 rounded-[22px] bg-gradient-to-br from-accent-primary to-accent-secondary flex items-center justify-center font-black text-white text-3xl shadow-[0_12px_24px_-4px_rgba(var(--accent-primary),0.3)]">
                                            {userName.charAt(0).toUpperCase()}
                                        </div>
                                        <div className="space-y-1">
                                            <p className="text-2xl font-bold font-outfit">{userName}</p>
                                            <div className="flex items-center gap-2 text-text-muted text-sm font-medium">
                                                <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
                                                Authenticated via Neural JWT
                                            </div>
                                        </div>
                                    </div>

                                    <div className="space-y-5">
                                        <Button variant="outline" className="w-full justify-start h-14 rounded-2xl px-6 gap-3 border-[rgba(var(--border-secondary))] hover:bg-[rgba(var(--bg-surface-hover))] group">
                                            <Smartphone className="w-4.5 h-4.5 text-text-muted group-hover:text-text-primary transition-colors" />
                                            <span className="text-sm font-bold">Manage connected devices</span>
                                        </Button>
                                        <Button variant="outline" className="w-full justify-start h-14 rounded-2xl px-6 gap-3 border-[rgba(var(--border-secondary))] hover:bg-[rgba(var(--bg-surface-hover))] group">
                                            <RefreshCw className="w-4.5 h-4.5 text-text-muted group-hover:text-text-primary transition-colors" />
                                            <span className="text-sm font-bold">Download your data</span>
                                        </Button>
                                    </div>
                                </div>
                            )}

                            {/* System Health Tab */}
                            {activeTab === 'health' && (
                                <div className="space-y-8">
                                    <div className="flex items-center justify-between">
                                        <div className="space-y-1.5">
                                            <div className="flex items-center gap-3">
                                                <p className="font-bold text-[15px]">{t('settings.health.title')}</p>
                                                <span className={cn(
                                                    "px-2 py-0.5 rounded-full text-[10px] font-black tracking-widest",
                                                    onlineCount === SERVICES.length ? "bg-emerald-500/10 text-emerald-500" : "bg-amber-500/10 text-amber-500"
                                                )}>
                                                    {onlineCount}/{SERVICES.length} {t('common.status').toUpperCase()}
                                                </span>
                                            </div>
                                            <p className="text-sm text-text-muted leading-relaxed">{t('settings.health.desc')}</p>
                                        </div>
                                        <button
                                            onClick={checkHealth}
                                            className="w-10 h-10 flex items-center justify-center hover:bg-[rgba(var(--bg-surface-hover))] rounded-full transition-all text-text-muted hover:text-text-primary active:rotate-180 duration-500"
                                        >
                                            <RefreshCw className="w-4 h-4" />
                                        </button>
                                    </div>

                                    <div className="grid grid-cols-1 gap-3">
                                        {SERVICES.map(svc => {
                                            const st = statuses[svc.name] || 'checking';
                                            return (
                                                <div key={svc.name} className="flex items-center justify-between p-5 bg-[rgba(var(--bg-surface-hover))] rounded-[20px] border border-[rgba(var(--border-secondary))] group hover:bg-accent-primary/5 transition-colors">
                                                    <div className="flex items-center gap-4">
                                                        <div className={cn(
                                                            "w-10 h-10 rounded-xl flex items-center justify-center transition-all",
                                                            st === 'online' ? "bg-emerald-500/10 text-emerald-500" :
                                                                st === 'offline' ? "bg-rose-500/10 text-rose-500" : "bg-text-muted/10 text-text-muted"
                                                        )}>
                                                            <Cpu className="w-5 h-5" strokeWidth={1.5} />
                                                        </div>
                                                        <div>
                                                            <p className="font-bold text-[14px]">{svc.name}</p>
                                                            <p className="text-[11px] font-bold text-text-muted/60 font-mono tracking-tighter uppercase">{svc.label}</p>
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center gap-2 pr-2">
                                                        {st === 'checking' && <Loader2 className="w-3.5 h-3.5 animate-spin text-text-muted" />}
                                                        <span className={cn(
                                                            "text-[12px] font-black uppercase tracking-widest",
                                                            st === 'online' ? "text-emerald-500" :
                                                                st === 'offline' ? "text-rose-500" : "text-text-muted"
                                                        )}>
                                                            {st}
                                                        </span>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}

                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
};

export default SettingsModal;
