import React, { useState, useRef, useEffect } from 'react';
import { X, TrendingUp } from 'lucide-react';
import { skillApi, SkillSearchResult } from '../../services/api';
import { cn } from '../../lib/utils';

interface SkillAutocompleteInputProps {
    selectedSkills: string[];
    onChange: (skills: string[]) => void;
    jobTitle?: string;
    placeholder?: string;
}

const SkillAutocompleteInput: React.FC<SkillAutocompleteInputProps> = ({
    selectedSkills,
    onChange,
    placeholder = "Nhập kỹ năng (vd: React, Python...)",
}) => {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<SkillSearchResult[]>([]);
    const [isOpen, setIsOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleInputChange = (val: string) => {
        setQuery(val);
        if (debounceRef.current) clearTimeout(debounceRef.current);
        if (val.trim().length < 2) {
            setResults([]);
            setIsOpen(false);
            return;
        }
        debounceRef.current = setTimeout(async () => {
            setIsLoading(true);
            try {
                const res = await skillApi.searchSkills(val.trim(), 8);
                setResults(res.data.results.filter(r => !selectedSkills.includes(r.name)));
                setIsOpen(true);
            } catch {
                setResults([]);
            }
            setIsLoading(false);
        }, 300);
    };

    const handleAdd = (skillName: string) => {
        if (!selectedSkills.includes(skillName)) {
            onChange([...selectedSkills, skillName]);
        }
        setQuery('');
        setResults([]);
        setIsOpen(false);
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' && query.trim()) {
            e.preventDefault();
            handleAdd(query.trim());
        }
    };

    const handleRemove = (skill: string) => {
        onChange(selectedSkills.filter(s => s !== skill));
    };

    return (
        <div ref={containerRef} className="space-y-2">
            {/* Selected skills chips */}
            {selectedSkills.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                    {selectedSkills.map(skill => (
                        <span
                            key={skill}
                            className="flex items-center gap-1 px-2.5 py-1 bg-accent-primary/10 border border-accent-primary/20 text-accent-primary rounded-lg text-xs font-medium"
                        >
                            {skill}
                            <button
                                onClick={() => handleRemove(skill)}
                                className="hover:text-white transition-colors ml-0.5"
                            >
                                <X className="w-3 h-3" />
                            </button>
                        </span>
                    ))}
                </div>
            )}

            {/* Input */}
            <div className="relative">
                <input
                    type="text"
                    value={query}
                    onChange={e => handleInputChange(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={placeholder}
                    className="w-full bg-slate-950/50 border border-white/10 rounded-xl px-3 py-2 text-sm text-slate-200 outline-none focus:border-accent-primary transition-all placeholder:text-slate-500"
                />
                {isLoading && (
                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                        <div className="w-3.5 h-3.5 border-2 border-accent-primary/30 border-t-accent-primary rounded-full animate-spin" />
                    </div>
                )}

                {/* Dropdown */}
                {isOpen && results.length > 0 && (
                    <div className="absolute z-50 top-full mt-1 w-full bg-slate-900 border border-white/10 rounded-xl shadow-2xl overflow-hidden">
                        {results.map(r => (
                            <button
                                key={r.name}
                                onClick={() => handleAdd(r.name)}
                                className="w-full flex items-center justify-between px-3 py-2 hover:bg-white/5 text-left transition-colors"
                            >
                                <div className="flex items-center gap-2">
                                    <span className="text-sm text-slate-200">{r.name}</span>
                                    {r.trending && (
                                        <span className="flex items-center gap-0.5 text-[10px] text-emerald-400 font-bold">
                                            <TrendingUp className="w-2.5 h-2.5" /> trending
                                        </span>
                                    )}
                                </div>
                                <div className="flex items-center gap-2 text-[10px] text-slate-500">
                                    <span className="bg-white/5 px-1.5 py-0.5 rounded">{r.category}</span>
                                    <span>{Math.round(r.demand)}% demand</span>
                                </div>
                            </button>
                        ))}
                        <div className="px-3 py-1.5 text-[10px] text-slate-500 border-t border-white/5">
                            Nhấn Enter để thêm kỹ năng tùy chỉnh
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default SkillAutocompleteInput;
