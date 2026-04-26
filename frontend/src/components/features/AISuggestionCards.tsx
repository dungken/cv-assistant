import React, { useState } from 'react';
import { Sparkles, Check, Edit3, ChevronDown, ChevronUp } from 'lucide-react';
import { BulletSuggestion } from '../../services/api';
import { cn } from '../../lib/utils';

interface AISuggestionCardsProps {
    suggestions: BulletSuggestion[];
    isLoading: boolean;
    onSelect: (bullet: string) => void;
}

const AISuggestionCards: React.FC<AISuggestionCardsProps> = ({ suggestions, isLoading, onSelect }) => {
    const [editingId, setEditingId] = useState<number | null>(null);
    const [editValue, setEditValue] = useState('');
    const [expandedId, setExpandedId] = useState<number | null>(null);
    const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

    const handleEdit = (s: BulletSuggestion) => {
        setEditingId(s.id);
        setEditValue(s.bullet);
    };

    const handleConfirmEdit = (id: number) => {
        onSelect(editValue);
        setSelectedIds(prev => new Set(prev).add(id));
        setEditingId(null);
    };

    const handleSelect = (s: BulletSuggestion) => {
        onSelect(s.bullet);
        setSelectedIds(prev => new Set(prev).add(s.id));
    };

    if (isLoading) {
        return (
            <div className="space-y-3">
                {[1, 2, 3].map(i => (
                    <div key={i} className="h-16 bg-white/5 rounded-xl animate-pulse border border-white/5" />
                ))}
            </div>
        );
    }

    if (!suggestions.length) return null;

    return (
        <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-accent-primary uppercase tracking-widest mb-3">
                <Sparkles className="w-3.5 h-3.5" />
                AI Suggestions — chọn hoặc sửa trước khi thêm vào CV
            </div>
            {suggestions.map(s => (
                <div
                    key={s.id}
                    className={cn(
                        "bg-slate-900/60 border rounded-xl p-3 transition-all duration-200",
                        selectedIds.has(s.id) ? "border-emerald-500/40 bg-emerald-900/10" : "border-white/10 hover:border-white/20"
                    )}
                >
                    {editingId === s.id ? (
                        <div className="space-y-2">
                            <textarea
                                value={editValue}
                                onChange={e => setEditValue(e.target.value)}
                                className="w-full bg-slate-950/50 border border-white/10 rounded-lg p-2 text-xs text-slate-200 outline-none focus:border-accent-primary resize-none min-h-[60px]"
                                autoFocus
                            />
                            <div className="flex gap-2">
                                <button
                                    onClick={() => handleConfirmEdit(s.id)}
                                    className="flex items-center gap-1 px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold transition-all"
                                >
                                    <Check className="w-3 h-3" /> Thêm vào CV
                                </button>
                                <button
                                    onClick={() => setEditingId(null)}
                                    className="px-3 py-1 bg-white/5 hover:bg-white/10 text-slate-400 rounded-lg text-xs transition-all"
                                >
                                    Hủy
                                </button>
                            </div>
                        </div>
                    ) : (
                        <>
                            <p className="text-xs text-slate-300 leading-relaxed">{s.bullet}</p>
                            <div className="flex items-center justify-between mt-2">
                                <div className="flex items-center gap-1.5">
                                    <button
                                        onClick={() => handleSelect(s)}
                                        disabled={selectedIds.has(s.id)}
                                        className={cn(
                                            "flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold transition-all",
                                            selectedIds.has(s.id)
                                                ? "bg-emerald-600/30 text-emerald-400 cursor-default"
                                                : "bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-400"
                                        )}
                                    >
                                        <Check className="w-3 h-3" />
                                        {selectedIds.has(s.id) ? "Đã chọn" : "Chọn"}
                                    </button>
                                    <button
                                        onClick={() => handleEdit(s)}
                                        className="flex items-center gap-1 px-2.5 py-1 bg-white/5 hover:bg-white/10 text-slate-400 rounded-lg text-xs transition-all"
                                    >
                                        <Edit3 className="w-3 h-3" /> Sửa
                                    </button>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="text-[10px] text-slate-500">
                                        {Math.round(s.confidence * 100)}% match
                                    </span>
                                    <button
                                        onClick={() => setExpandedId(expandedId === s.id ? null : s.id)}
                                        className="text-slate-500 hover:text-slate-300 transition-colors"
                                    >
                                        {expandedId === s.id ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                                    </button>
                                </div>
                            </div>
                            {expandedId === s.id && (
                                <div className="mt-2 pt-2 border-t border-white/5 grid grid-cols-2 gap-1">
                                    {Object.entries(s.star_format).map(([k, v]) => (
                                        <div key={k} className="text-[10px]">
                                            <span className="text-accent-primary font-bold uppercase">{k}: </span>
                                            <span className="text-slate-400">{v}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </>
                    )}
                </div>
            ))}
        </div>
    );
};

export default AISuggestionCards;
