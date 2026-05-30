import { useState, useCallback, useMemo } from 'react';
import { Sparkles, X, Plus, TrendingUp, CheckCircle, Info } from 'lucide-react';
import { cvHealthApi, type HealthScoreResponse } from '../../../services/api';

interface Props {
    userId: string;
    originalData: HealthScoreResponse | null;
    onSimulate: (data: HealthScoreResponse | null) => void;
}

const DIM_LABELS: Record<string, string> = {
    skill: 'Skill',
    experience: 'Experience',
    project: 'Project',
    education: 'Education',
    achievement: 'Achievement',
    language: 'Language',
    completeness: 'Completeness',
    market_alignment: 'Market Align',
};

export default function WhatIfSimulation({ userId, originalData, onSimulate }: Props) {
    const [active, setActive] = useState(false);
    const [addedSkills, setAddedSkills] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);
    
    // Track simulated data locally to render the impact callout card
    const [simulatedData, setSimulatedData] = useState<HealthScoreResponse | null>(null);

    const toggleSimulation = useCallback(async (newSkills: string[]) => {
        if (!originalData) return;
        setLoading(true);
        try {
            // Get current skills from baseline
            const currentSkills = originalData.contributions.map(c => c.skill);
            const allSkills = Array.from(new Set([...currentSkills, ...newSkills]));
            
            // Invoke simulation endpoint
            const res = await cvHealthApi.simulateCv(
                userId,
                originalData.role,
                allSkills.map(name => ({ name })),
                { seniority: originalData.seniority }
            );
            setSimulatedData(res.data);
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
            setSimulatedData(null);
            onSimulate(null); // Return to original
        } else {
            toggleSimulation(next);
        }
    };

    const handleClose = () => {
        setActive(false);
        setAddedSkills([]);
        setSimulatedData(null);
        onSimulate(null);
    };

    // Calculate boosted dimensions and scores
    const simulationImpact = useMemo(() => {
        if (!originalData || !simulatedData || addedSkills.length === 0) return null;
        
        const scoreDiff = simulatedData.score - originalData.score;
        
        // Find which dimensions got improved
        const boostedDims: string[] = [];
        const simDims = simulatedData.dimensions || [];
        const origDims = originalData.dimensions || [];
        simDims.forEach(simDim => {
            const origDim = origDims.find(d => d.name === simDim.name);
            if (origDim && simDim.score > origDim.score) {
                boostedDims.push(DIM_LABELS[simDim.name] ?? simDim.name);
            }
        });

        return {
            scoreDiff,
            boostedDims,
            originalScore: originalData.score,
            simulatedScore: simulatedData.score,
        };
    }, [originalData, simulatedData, addedSkills]);

    if (!originalData) return null;

    if (!active) {
        return (
            <button
                type="button"
                onClick={() => setActive(true)}
                className="w-full flex items-center justify-center gap-2.5 py-4 rounded-2xl bg-gradient-to-r from-violet-500/10 to-indigo-500/10 border border-violet-500/25 hover:border-violet-500/40 hover:bg-gradient-to-r hover:from-violet-500/15 hover:to-indigo-500/15 transition-all text-violet-400 font-extrabold text-sm shadow-[0_4px_20px_rgba(99,102,241,0.05)] cursor-pointer group active:scale-[0.99]"
            >
                <Sparkles className="w-4 h-4 text-violet-400 animate-pulse group-hover:rotate-12 transition-transform" />
                Bật chế độ "What-if Simulation"
            </button>
        );
    }

    return (
        <div className="rounded-3xl border border-violet-500/20 bg-surface/95 p-6 relative overflow-hidden shadow-lg animate-in fade-in zoom-in-95 duration-200">

            <button
                type="button"
                onClick={handleClose}
                className="absolute top-5 right-5 text-text-muted hover:text-text-primary p-1.5 hover:bg-white/5 rounded-full transition-colors cursor-pointer"
            >
                <X className="w-5 h-5" />
            </button>
            
            <div className="flex items-center gap-2.5 mb-2">
                <Sparkles className="w-5 h-5 text-violet-400 animate-spin-slow" />
                <h3 className="font-extrabold text-lg text-white font-outfit">What-if Simulation Mode</h3>
                {loading && (
                    <span className="ml-2 text-xs font-bold text-violet-400 bg-violet-500/10 px-2 py-0.5 rounded-full border border-violet-500/20 animate-pulse">
                        Đang tính toán…
                    </span>
                )}
            </div>
            
            <p className="text-xs text-text-secondary mb-5 leading-relaxed max-w-2xl">
                Giả định hồ sơ của bạn bổ sung thêm các kỹ năng mới để đo lường độ tăng điểm <strong>Freshness</strong> và khả năng tương thích 8 chiều mà không làm ảnh hưởng đến bản lưu trữ gốc của CV.
            </p>

            <div className="space-y-5">
                {/* Simulated Skills Badges */}
                <div className="space-y-2">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted">Kỹ năng đang giả lập ({addedSkills.length}):</span>
                    {addedSkills.length === 0 ? (
                        <div className="text-xs text-text-muted italic py-1 px-3 bg-white/[0.01] rounded-xl border border-dashed border-white/5">
                            Chưa có kỹ năng giả lập nào. Chọn các gợi ý bên dưới để mô phỏng.
                        </div>
                    ) : (
                        <div className="flex flex-wrap gap-2 animate-in fade-in duration-300">
                            {addedSkills.map(skill => (
                                <span key={skill} className="px-3 py-1.5 rounded-xl bg-violet-500/10 border border-violet-500/20 text-violet-300 text-xs font-semibold flex items-center gap-1.5 shadow-sm">
                                    {skill}
                                    <button 
                                        type="button" 
                                        onClick={() => handleRemoveSkill(skill)} 
                                        className="text-violet-400 hover:text-white transition-colors cursor-pointer"
                                    >
                                        <X className="w-3.5 h-3.5" />
                                    </button>
                                </span>
                            ))}
                        </div>
                    )}
                </div>

                {/* Simulated Impact Report Callout Card */}
                {simulationImpact && (
                    <div className="p-4 rounded-2xl bg-gradient-to-br from-emerald-500/10 to-teal-500/[0.02] border border-emerald-500/20 shadow-lg shadow-emerald-950/10 animate-in slide-in-from-top-3 duration-300 relative overflow-hidden group">
                        {/* Shimmer overlay */}
                        <div className="absolute inset-0 translate-x-[-100%] bg-gradient-to-r from-transparent via-white/5 to-transparent group-hover:animate-shimmer pointer-events-none" />
                        
                        <div className="flex items-start gap-3">
                            <div className="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shrink-0 mt-0.5">
                                <TrendingUp className="w-4 h-4 text-emerald-400" />
                            </div>
                            <div className="space-y-2 flex-1 min-w-0">
                                <h4 className="text-xs font-black uppercase tracking-wider text-emerald-400 flex items-center gap-2">
                                    Báo cáo Tác động Giả lập (Impact Report)
                                </h4>
                                <p className="text-xs text-text-secondary leading-relaxed">
                                    Bằng việc bổ sung <strong className="text-text-primary">{addedSkills.join(', ')}</strong>, điểm Freshness tổng quát của bạn tăng thêm <strong className="text-emerald-400">+{simulationImpact.scoreDiff.toFixed(1)}</strong> điểm (từ <span className="line-through opacity-60 text-text-muted">{simulationImpact.originalScore.toFixed(1)}</span> ➔ <strong className="text-emerald-400">{simulationImpact.simulatedScore.toFixed(1)}</strong>).
                                </p>
                                
                                {simulationImpact.boostedDims.length > 0 && (
                                    <div className="flex items-center gap-1.5 flex-wrap pt-1 border-t border-white/5">
                                        <span className="text-[10px] text-text-muted font-bold uppercase tracking-widest">Nâng cấp các chiều:</span>
                                        {simulationImpact.boostedDims.map(dim => (
                                            <span key={dim} className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 text-[10px] font-bold border border-emerald-500/10">
                                                ✓ {dim}
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Skill Suggestions Grid */}
                {originalData.missing_ideal.length > 0 && (
                    <div className="space-y-2">
                        <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted flex items-center gap-1">
                            <Info className="w-3.5 h-3.5 text-text-muted" />
                            Thử thêm kỹ năng xu hướng:
                        </span>
                        <div className="flex flex-wrap gap-2 pt-1">
                            {originalData.missing_ideal.filter(s => !addedSkills.includes(s)).slice(0, 10).map(skill => (
                                <button
                                    key={skill}
                                    type="button"
                                    onClick={() => handleAddSkill(skill)}
                                    disabled={loading}
                                    className="px-3 py-2 rounded-xl bg-white/5 border border-white/8 hover:border-violet-500/40 hover:bg-violet-500/10 transition-all text-text-secondary hover:text-white text-xs font-semibold flex items-center gap-1.5 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer active:scale-95"
                                >
                                    <Plus className="w-3.5 h-3.5 text-violet-400" /> <span className="sr-only">＋</span> {skill}
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
