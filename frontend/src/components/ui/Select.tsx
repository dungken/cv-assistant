import React, { useState, useRef, useEffect } from 'react';
import ReactDOM from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Check } from 'lucide-react';
import { cn } from '../../lib/utils';

interface SelectOption {
    label: string;
    value: string;
}

interface CustomSelectProps {
    value: string;
    onChange: (value: string) => void;
    options: SelectOption[];
    placeholder?: string;
    icon?: React.ElementType;
    className?: string;
}

export const CustomSelect: React.FC<CustomSelectProps> = ({ 
    value, 
    onChange, 
    options, 
    placeholder = "Select...", 
    icon: Icon,
    className 
}) => {
    const [isOpen, setIsOpen] = useState(false);
    const [dropdownStyle, setDropdownStyle] = useState<React.CSSProperties>({});
    const buttonRef = useRef<HTMLButtonElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    const activeOption = options.find(opt => opt.value === value);

    // Calculate dropdown position relative to viewport
    const updatePosition = () => {
        if (!buttonRef.current) return;
        const rect = buttonRef.current.getBoundingClientRect();
        setDropdownStyle({
            position: 'fixed',
            top: rect.bottom + 8,
            left: rect.left,
            width: rect.width,
            zIndex: 9999,
        });
    };

    useEffect(() => {
        if (isOpen) updatePosition();
    }, [isOpen]);

    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            const target = e.target as Node;
            if (
                containerRef.current && !containerRef.current.contains(target) &&
                !document.getElementById('custom-select-portal')?.contains(target)
            ) {
                setIsOpen(false);
            }
        };
        const handleScroll = () => { if (isOpen) updatePosition(); };
        const handleResize = () => { if (isOpen) updatePosition(); };

        document.addEventListener('mousedown', handleClickOutside);
        window.addEventListener('scroll', handleScroll, true);
        window.addEventListener('resize', handleResize);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
            window.removeEventListener('scroll', handleScroll, true);
            window.removeEventListener('resize', handleResize);
        };
    }, [isOpen]);

    const dropdown = (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    id="custom-select-portal"
                    style={dropdownStyle}
                    initial={{ opacity: 0, y: 6, scale: 0.97 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 6, scale: 0.97 }}
                    transition={{ duration: 0.18, ease: "easeOut" }}
                    className="bg-surface backdrop-blur-xl border border-white/10 rounded-[1.5rem] shadow-2xl shadow-black/80 ring-1 ring-white/5 overflow-hidden"
                >
                    <div className="p-2 space-y-1 max-h-60 overflow-y-auto floating-scrollbar">
                        {options.map((option) => (
                            <button
                                key={option.value}
                                type="button"
                                onClick={() => {
                                    onChange(option.value);
                                    setIsOpen(false);
                                }}
                                className={cn(
                                    "w-full flex items-center justify-between px-4 py-3 rounded-xl text-sm font-bold transition-all duration-200 text-left",
                                    option.value === value 
                                        ? "bg-text-primary text-secondary" 
                                        : "text-text-secondary hover:bg-surface-hover hover:text-text-primary"
                                )}
                            >
                                {option.label}
                                {option.value === value && <Check className="w-4 h-4" />}
                            </button>
                        ))}
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );

    return (
        <div ref={containerRef} className={cn("relative w-full", className)}>
            <button
                ref={buttonRef}
                type="button"
                onClick={() => setIsOpen(!isOpen)}
                className={cn(
                    "w-full bg-secondary/50 text-text-primary rounded-2xl pl-12 pr-4 py-3.5 outline-none focus:ring-2 focus:ring-white/5 transition-all text-sm font-bold flex items-center justify-between text-left",
                    isOpen && "ring-2 ring-white/5"
                )}
            >
                <div className="flex items-center gap-3">
                    {Icon && <Icon className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted/40" />}
                    <span className={cn(!activeOption && "text-text-muted/20")}>
                        {activeOption ? activeOption.label : placeholder}
                    </span>
                </div>
                <ChevronDown className={cn("w-4 h-4 text-text-muted/40 transition-transform duration-300", isOpen && "rotate-180")} />
            </button>

            {typeof window !== 'undefined' && ReactDOM.createPortal(dropdown, document.body)}
        </div>
    );
};
