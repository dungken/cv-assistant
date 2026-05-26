import { useEffect, useRef, useState } from 'react';
import ReactDOM from 'react-dom';
import { ChevronDown, Check } from 'lucide-react';
import { cn } from '../../lib/utils';

interface Option {
    label: string;
    value: string;
}

interface Props {
    value: string;
    onChange: (value: string) => void;
    options: Option[];
    placeholder?: string;
    className?: string;
    label?: string;
}

/**
 * Lightweight dropdown — no framer-motion, no backdrop-blur, no heavy shadows.
 * Replaces native <select> for consistent dark-theme styling without perf hit.
 */
export function LightSelect({ value, onChange, options, placeholder, className, label }: Props) {
    const [open, setOpen] = useState(false);
    const [pos, setPos] = useState<React.CSSProperties>({});
    const btnRef = useRef<HTMLButtonElement>(null);
    const popRef = useRef<HTMLDivElement>(null);

    const active = options.find((o) => o.value === value);

    const updatePos = () => {
        if (!btnRef.current) return;
        const r = btnRef.current.getBoundingClientRect();
        setPos({
            position: 'fixed',
            top: r.bottom + 4,
            left: r.left,
            minWidth: r.width,
            zIndex: 9999,
        });
    };

    useEffect(() => {
        if (!open) return;
        updatePos();
        const onClick = (e: MouseEvent) => {
            const t = e.target as Node;
            if (
                btnRef.current && !btnRef.current.contains(t) &&
                popRef.current && !popRef.current.contains(t)
            ) {
                setOpen(false);
            }
        };
        // Reposition (don't close) when page scrolls — but skip events from
        // inside the popup itself so users can scroll the option list freely.
        const onScroll = (e: Event) => {
            if (popRef.current && popRef.current.contains(e.target as Node)) return;
            updatePos();
        };
        const onResize = () => updatePos();
        document.addEventListener('mousedown', onClick);
        window.addEventListener('scroll', onScroll, true);
        window.addEventListener('resize', onResize);
        return () => {
            document.removeEventListener('mousedown', onClick);
            window.removeEventListener('scroll', onScroll, true);
            window.removeEventListener('resize', onResize);
        };
    }, [open]);

    return (
        <div className="relative">
            {label && (
                <label className="block text-[10px] uppercase tracking-wider text-text-secondary mb-1 font-semibold">
                    {label}
                </label>
            )}
            <button
                ref={btnRef}
                type="button"
                onClick={() => setOpen(!open)}
                className={cn(
                    'rounded-xl border border-white/10 bg-surface/40 px-3 py-2 text-sm flex items-center justify-between gap-2 min-w-[140px]',
                    'hover:border-white/20 focus:border-accent-primary/50 focus:outline-none transition-colors',
                    open && 'border-accent-primary/50',
                    className,
                )}
            >
                <span className="truncate text-left">
                    {active?.label ?? placeholder ?? '—'}
                </span>
                <ChevronDown
                    className={cn(
                        'w-4 h-4 text-text-muted shrink-0 transition-transform duration-150',
                        open && 'rotate-180',
                    )}
                />
            </button>
            {open && typeof window !== 'undefined' && ReactDOM.createPortal(
                <div
                    ref={popRef}
                    style={pos}
                    className="bg-surface border border-white/10 rounded-xl shadow-xl py-1 max-h-72 overflow-y-auto animate-in fade-in zoom-in-95 duration-100"
                >
                    {options.map((o) => {
                        const selected = o.value === value;
                        return (
                            <button
                                key={o.value}
                                type="button"
                                onClick={() => {
                                    onChange(o.value);
                                    setOpen(false);
                                }}
                                className={cn(
                                    'w-full flex items-center justify-between gap-2 px-3 py-2 text-sm text-left transition-colors',
                                    selected
                                        ? 'bg-accent-primary/15 text-text-primary'
                                        : 'text-text-secondary hover:bg-surface-hover hover:text-text-primary',
                                )}
                            >
                                <span className="truncate">{o.label}</span>
                                {selected && <Check className="w-4 h-4 text-accent-primary shrink-0" />}
                            </button>
                        );
                    })}
                </div>,
                document.body,
            )}
        </div>
    );
}
