import React, { useState, useEffect, useCallback } from 'react';
import { X, Moon, Sun, Monitor, Shield, Settings, Activity, CheckCircle, XCircle, Loader2, RefreshCw } from 'lucide-react';
import axios from 'axios';

interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
    theme: 'dark' | 'light';
    onThemeToggle: () => void;
    userName: string;
}

const SERVICES = [
    { name: 'API Gateway',    url: 'http://localhost:8081/api/health', label: 'C# / .NET 9' },
    { name: 'Chatbot AI',     url: 'http://localhost:5004/health',     label: 'Python / FastAPI' },
    { name: 'NER Extractor',  url: 'http://localhost:5005/health',     label: 'Python / Transformers' },
    { name: 'Skill Engine',   url: 'http://localhost:5002/health',     label: 'Python / SBERT' },
    { name: 'Career Engine',  url: 'http://localhost:5003/health',     label: 'Python / O*NET' },
];

type ServiceStatus = 'checking' | 'online' | 'offline';

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose, theme, onThemeToggle, userName }) => {
    const [statuses, setStatuses] = useState<Record<string, ServiceStatus>>({});

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
        if (isOpen) checkHealth();
    }, [isOpen, checkHealth]);

    if (!isOpen) return null;

    const onlineCount = Object.values(statuses).filter(s => s === 'online').length;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-surface w-full max-w-2xl rounded-3xl border border-border-main shadow-2xl overflow-hidden flex flex-col max-h-[88vh] text-text-main">
                <div className="p-6 border-b border-border-main flex items-center justify-between">
                    <h2 className="text-xl font-bold flex items-center gap-2">
                        <Settings className="w-5 h-5" />
                        Settings
                    </h2>
                    <button onClick={onClose} className="p-2 hover:bg-overlay rounded-xl transition-colors">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-6 space-y-8 no-scrollbar">
                    {/* Personalization */}
                    <section>
                        <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest mb-4 opacity-50">Personalization</h3>
                        <div className="bg-overlay rounded-2xl p-4 border border-border-main">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-accent-primary/10 rounded-lg">
                                        {theme === 'dark' ? <Moon className="w-5 h-5 text-accent-primary" /> : <Sun className="w-5 h-5 text-accent-primary" />}
                                    </div>
                                    <div>
                                        <p className="font-medium">Interface Theme</p>
                                        <p className="text-xs text-text-muted">Switch between dark and light appearance</p>
                                    </div>
                                </div>
                                <button
                                    onClick={onThemeToggle}
                                    className="px-4 py-2 bg-surface hover:bg-surface-hover border border-border-main rounded-xl text-sm font-medium transition-all shadow-sm"
                                >
                                    Toggle {theme === 'dark' ? 'Light' : 'Dark'}
                                </button>
                            </div>
                        </div>
                    </section>

                    {/* Account */}
                    <section>
                        <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest mb-4 opacity-50">Account</h3>
                        <div className="bg-overlay rounded-2xl p-4 border border-border-main">
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 rounded-2xl bg-accent-primary flex items-center justify-center font-black text-white text-xl shadow-lg">
                                    {userName.charAt(0).toUpperCase()}
                                </div>
                                <div>
                                    <p className="text-lg font-bold">{userName}</p>
                                    <p className="text-xs text-text-muted opacity-50">Authenticated via JWT</p>
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* System Health */}
                    <section>
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest opacity-50 flex items-center gap-2">
                                <Activity className="w-3.5 h-3.5" />
                                System Health
                                <span className={`ml-1 px-2 py-0.5 rounded-full text-xs font-bold ${
                                    onlineCount === SERVICES.length ? 'bg-emerald-500/10 text-emerald-500' :
                                    onlineCount === 0 ? 'bg-rose-500/10 text-rose-500' :
                                    'bg-amber-500/10 text-amber-500'
                                }`}>
                                    {onlineCount}/{SERVICES.length} Online
                                </span>
                            </h3>
                            <button onClick={checkHealth} className="p-1.5 hover:bg-overlay rounded-lg transition-colors text-text-muted hover:text-text-primary">
                                <RefreshCw className="w-3.5 h-3.5" />
                            </button>
                        </div>
                        <div className="bg-overlay rounded-2xl border border-border-main divide-y divide-border-main/50">
                            {SERVICES.map(svc => {
                                const st = statuses[svc.name] || 'checking';
                                return (
                                    <div key={svc.name} className="flex items-center justify-between px-5 py-4">
                                        <div>
                                            <p className="font-medium text-sm">{svc.name}</p>
                                            <p className="text-xs text-text-muted opacity-50 font-mono">{svc.label}</p>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            {st === 'checking' && (
                                                <><Loader2 className="w-4 h-4 text-text-muted animate-spin" /><span className="text-xs text-text-muted">Checking…</span></>
                                            )}
                                            {st === 'online' && (
                                                <><CheckCircle className="w-4 h-4 text-emerald-500" /><span className="text-xs text-emerald-500 font-bold">Online</span></>
                                            )}
                                            {st === 'offline' && (
                                                <><XCircle className="w-4 h-4 text-rose-500" /><span className="text-xs text-rose-500 font-bold">Offline</span></>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </section>

                    {/* Advanced (locked) */}
                    <section className="opacity-50 pointer-events-none">
                        <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest mb-4 opacity-50">Advanced</h3>
                        <div className="space-y-2">
                            <div className="flex items-center gap-3 p-3 text-sm">
                                <Shield className="w-4 h-4 text-text-muted" />
                                <span>Encrypted Session Storage</span>
                            </div>
                            <div className="flex items-center gap-3 p-3 text-sm">
                                <Monitor className="w-4 h-4 text-text-muted" />
                                <span>Hardware Acceleration</span>
                            </div>
                        </div>
                    </section>
                </div>

                <div className="p-6 bg-canvas border-t border-border-main text-center">
                    <p className="text-[10px] font-bold text-text-muted uppercase tracking-widest opacity-40">Antigravity CV Engine v1.3.0</p>
                </div>
            </div>
        </div>
    );
};

export default SettingsModal;
