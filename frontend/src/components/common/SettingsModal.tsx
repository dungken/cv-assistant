import React from 'react';
import { X, Moon, Sun, Monitor, Shield, Settings } from 'lucide-react';

interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
    theme: 'dark' | 'light';
    onThemeToggle: () => void;
    userName: string;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose, theme, onThemeToggle, userName }) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-surface w-full max-w-2xl rounded-3xl border border-border-main shadow-2xl overflow-hidden flex flex-col max-h-[80vh] text-text-main">
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
                    <section>
                        <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest mb-4 opacity-50">Personalization</h3>
                        <div className="bg-overlay rounded-2xl p-4 border border-border-main space-y-4">
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

                    <section>
                        <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest mb-4 opacity-50">Account</h3>
                        <div className="bg-overlay rounded-2xl p-4 border border-border-main space-y-4">
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 rounded-2xl bg-accent-primary flex items-center justify-center font-black text-white text-xl shadow-lg">
                                    {userName.charAt(0).toUpperCase()}
                                </div>
                                <div>
                                    <p className="text-lg font-bold">{userName}</p>
                                    <p className="text-xs text-text-muted font-mono opacity-50">ID: USER-884931</p>
                                </div>
                            </div>
                        </div>
                    </section>

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
                    <p className="text-[10px] font-bold text-text-muted uppercase tracking-widest opacity-40">Antigravity CV Engine v1.2.4</p>
                </div>
            </div>
        </div>
    );
};

export default SettingsModal;
