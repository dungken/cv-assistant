import { useState, useCallback } from 'react';
import { Sparkles, X, Plus } from 'lucide-react';
import { cvHealthApi, type HealthScoreResponse } from '../../../services/api';

interface Props {
    userId: string;
    originalData: HealthScoreResponse | null;
    onSimulate: (data: HealthScoreResponse | null) => void;
}

export default function WhatIfSimulation({ userId, originalData, onSimulate }: Props) {
    const [active, setActive] = useState(false);
    const [addedSkills, setAddedSkills] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);

    const toggleSimulation = useCallback(async (newSkills: string[]) => {
        if (!originalData) return;
        setLoading(true);
        try {
            // Lấy danh sách skill hiện tại từ contributions
            const currentSkills = originalData.contributions.map(c => c.skill);
            const allSkills = Array.from(new Set([...currentSkills, ...newSkills]));
            
            // Gọi endpoint simulate
            const res = await cvHealthApi.simulateCv(
                userId,
                originalData.role,
                allSkills.map(name => ({ name })),
                { seniority: originalData.seniority }
            );
            onSimulate(res.data);
        } catch (e) {
            console.error('Simulation failed', e);
        } finally {
            setLoading(false);
        }
    }, [userId, originalData, onSimulate]);

    const handleAddSkill = (skill: string) => {
        const next = [...addedSkills, skill];
        setAddedSkills(next);
        toggleSimulation(next);
    };

    const handleRemoveSkill = (skill: string) => {
        const next = addedSkills.filter(s => s !== skill);
        setAddedSkills(next);
        if (next.length === 0) {
            onSimulate(null); // Return to original
        } else {
            toggleSimulation(next);
        }
    };

    const handleClose = () => {
        setActive(false);
        setAddedSkills([]);
        onSimulate(null);
    };

    if (!originalData) return null;

    if (!active) {
        return (
            <button
                onClick={() => setActive(true)}
                className="w-full flex items-center justify-center gap-2 py-3 rounded-2xl bg-gradient-to-r from-violet-500/10 to-fuchsia-500/10 border border-violet-500/20 text-violet-400 hover:bg-violet-500/20 transition-all font-bold text-sm"
            >
                <Sparkles className="w-4 h-4" />
                Bật chế độ "What-if Simulation"
            </button>
        );
    }

    return (
        <div className="rounded-2xl border border-violet-500/30 bg-gradient-to-br from-violet-500/5 to-fuchsia-500/5 p-5 relative animate-in fade-in zoom-in-95 duration-200">
            <button
                onClick={handleClose}
                className="absolute top-4 right-4 text-text-muted hover:text-white"
            >
                <X className="w-5 h-5" />
            </button>
            
            <div className="flex items-center gap-2 mb-4">
                <Sparkles className="w-5 h-5 text-violet-400" />
                <h3 className="font-bold text-lg text-white">What-if Simulation Mode</h3>
                {loading && <span className="ml-2 text-xs text-violet-400 animate-pulse">Đang tính toán...</span>}
            </div>
            
            <p className="text-sm text-text-secondary mb-4">
                Thêm các kỹ năng bạn dự định học để xem điểm CV và cơ hội việc làm thay đổi như thế nào.
            </p>

            <div className="space-y-4">
                {/* Các kỹ năng đã thêm */}
                {addedSkills.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                        {addedSkills.map(skill => (
                            <span key={skill} className="px-3 py-1.5 rounded-lg bg-violet-500/20 border border-violet-500/30 text-violet-300 text-sm flex items-center gap-1">
                                {skill}
                                <button onClick={() => handleRemoveSkill(skill)} className="hover:text-white ml-1">
                                    <X className="w-3.5 h-3.5" />
                                </button>
                            </span>
                        ))}
                    </div>
                )}

                {/* Gợi ý kỹ năng */}
                {originalData.missing_ideal.length > 0 && (
                    <div>
                        <div className="text-xs font-bold uppercase text-text-muted mb-2">Thử thêm kỹ năng xu hướng:</div>
                        <div className="flex flex-wrap gap-2">
                            {originalData.missing_ideal.filter(s => !addedSkills.includes(s)).slice(0, 8).map(skill => (
                                <button
                                    key={skill}
                                    onClick={() => handleAddSkill(skill)}
                                    disabled={loading}
                                    className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 hover:border-violet-500/40 hover:bg-violet-500/10 transition-colors text-text-secondary hover:text-white text-sm flex items-center gap-1 disabled:opacity-50"
                                >
                                    <Plus className="w-3 h-3" /> {skill}
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
