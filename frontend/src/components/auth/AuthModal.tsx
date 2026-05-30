import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { Dialog } from '../ui/Dialog';
import Login from './Login';
import Register from './Register';
import ForgotPassword from './ForgotPassword';

export type AuthViewType = 'login' | 'register' | 'forgot-password';

interface AuthModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onAuthSuccess: (token: string, name: string, role: string, email: string) => void;
    defaultView?: AuthViewType;
}

export default function AuthModal({ open, onOpenChange, onAuthSuccess, defaultView = 'login' }: AuthModalProps) {
    const [view, setView] = useState<AuthViewType>(defaultView);

    // Reset view when modal opens
    useEffect(() => {
        if (open) setView(defaultView);
    }, [open, defaultView]);

    const handleSuccess = (token: string, name: string, role: string, email: string) => {
        onAuthSuccess(token, name, role, email);
        onOpenChange(false); // Close modal on success
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <div className="relative w-full max-w-6xl mx-auto flex justify-center px-4">
                {/* Close Button floating top right */}
                <button 
                    onClick={() => onOpenChange(false)}
                    className="absolute -top-10 right-4 lg:-right-4 z-50 p-2 rounded-full bg-black/40 text-white/70 hover:text-white hover:bg-black/60 border border-white/10 transition-all backdrop-blur-sm"
                >
                    <X className="w-5 h-5" />
                </button>
                
                {view === 'login' ? (
                    <Login 
                        onLoginSuccess={handleSuccess} 
                        onSwitchToRegister={() => setView('register')} 
                        onSwitchToForgotPassword={() => setView('forgot-password')} 
                    />
                ) : view === 'register' ? (
                    <Register 
                        onRegisterSuccess={handleSuccess} 
                        onSwitchToLogin={() => setView('login')} 
                    />
                ) : (
                    <ForgotPassword onBackToLogin={() => setView('login')} />
                )}
            </div>
        </Dialog>
    );
}
