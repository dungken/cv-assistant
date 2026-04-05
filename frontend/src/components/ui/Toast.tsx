import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertCircle, X } from 'lucide-react';
import { cn } from '../../lib/utils';

interface ToastProps {
    message: string;
    type?: 'success' | 'error';
    onClose: () => void;
    duration?: number;
}

export const Toast: React.FC<ToastProps> = ({ 
    message, 
    type = 'success', 
    onClose, 
    duration = 3000 
}) => {
    useEffect(() => {
        const timer = setTimeout(onClose, duration);
        return () => clearTimeout(timer);
    }, [onClose, duration]);

    return (
        <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
            className={cn(
                "fixed bottom-8 right-8 z-[100] flex items-center gap-3 px-5 py-3 rounded-2xl shadow-2xl border backdrop-blur-xl",
                type === 'success' 
                    ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-500" 
                    : "bg-red-500/10 border-red-500/20 text-red-500"
            )}
        >
            {type === 'success' ? (
                <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
            ) : (
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
            )}
            <p className="text-sm font-bold tracking-tight">{message}</p>
            <button 
                onClick={onClose}
                className="ml-2 p-1 hover:bg-white/5 rounded-lg transition-colors"
            >
                <X className="w-4 h-4 opacity-50 hover:opacity-100" />
            </button>
        </motion.div>
    );
};
