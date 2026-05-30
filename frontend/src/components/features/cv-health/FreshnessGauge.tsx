import { memo, useMemo, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip,
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Cell
} from 'recharts';
import { ExternalLink, Grid, BarChart3, HelpCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../ui/Card';
import { Badge } from '../../ui/Badge';
import { GaugeSkeleton } from '../../ui/Skeleton';
import type { HealthScoreResponse } from '../../../services/api';

interface Props {
    data: HealthScoreResponse | null;
    originalData?: HealthScoreResponse | null;
    loading?: boolean;
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

function scoreColor(score: number): string {
    if (score >= 75) return '#10b981'; // green-500
    if (score >= 50) return '#6366f1'; // indigo-500
    if (score >= 30) return '#f59e0b'; // amber-500
    return '#f43f5e'; // rose-500
}

function scoreLabel(score: number): string {
    if (score >= 85) return 'Xuất sắc';
    if (score >= 70) return 'Tốt';
    if (score >= 50) return 'Trung bình';
    if (score >= 30) return 'Cần cải thiện';
    return 'Lỗi thời';
}

function FreshnessGaugeInner({ data, originalData, loading }: Props) {
    const navigate = useNavigate();
    const safeData = data && typeof data.score === 'number' ? data : null;

    // View mode state: 'radar' or 'bar'
    const [viewMode, setViewMode] = useState<'radar' | 'bar'>('radar');

    // Automatically adapt view mode on mobile size
    useEffect(() => {
        const handleResize = () => {
            if (window.innerWidth < 640) {
                setViewMode('bar');
            } else {
                setViewMode('radar');
            }
        };
        handleResize();
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    // Check if simulation is currently active
    const isSimulated = useMemo(() => {
        if (!originalData || !safeData) return false;
        return Math.abs(safeData.score - originalData.score) > 0.05;
    }, [safeData, originalData]);

    const radarData = useMemo(() => {
        if (!safeData?.dimensions || safeData.dimensions.length === 0) return [];
        
        // Map original scores to dimensions
        const originalMap = new Map<string, number>();
        if (originalData?.dimensions) {
            originalData.dimensions.forEach(d => {
                originalMap.set(d.name, d.score);
            });
        }

        return safeData.dimensions.map(d => {
            const hasOrig = originalMap.has(d.name);
            const originalVal = hasOrig ? originalMap.get(d.name)! : d.score;
            return {
                axis: DIM_LABELS[d.name] ?? d.name,
                name: d.name,
                score: d.score,
                originalScore: originalVal,
                weight: d.weight,
                detail: d.detail || '',
            };
        });
    }, [safeData, originalData]);

    const hasMulti = radarData.length > 0;

    return (
        <Card className="bg-surface border border-white/5 shadow-lg overflow-hidden relative group">

            <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-white/5 pb-4">
                <div>
                    <CardTitle className="text-xl font-extrabold font-outfit tracking-tight flex items-center gap-2">
                        Multi-criteria CV Freshness
                        {isSimulated && (
                            <Badge className="bg-violet-500/10 text-violet-400 border border-violet-500/20 px-2 py-0.5 animate-pulse text-[10px] font-bold">
                                Simulated Mode
                            </Badge>
                        )}
                    </CardTitle>
                    <CardDescription className="text-xs">
                        Đánh giá CV 8 chiều được tối ưu và cân đối trọng số theo xu hướng thị trường IT Việt Nam
                    </CardDescription>
                </div>

                {/* View toggles */}
                {hasMulti && (
                    <div className="flex items-center p-0.5 rounded-xl bg-white/5 border border-white/8 shrink-0 self-start sm:self-auto">
                        <button
                            type="button"
                            onClick={() => setViewMode('radar')}
                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                                viewMode === 'radar'
                                    ? 'bg-white/10 text-text-primary shadow-sm'
                                    : 'text-text-muted hover:text-text-secondary'
                            }`}
                        >
                            <Grid className="w-3.5 h-3.5" />
                            Mạng nhện
                        </button>
                        <button
                            type="button"
                            onClick={() => setViewMode('bar')}
                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                                viewMode === 'bar'
                                    ? 'bg-white/10 text-text-primary shadow-sm'
                                    : 'text-text-muted hover:text-text-secondary'
                            }`}
                        >
                            <BarChart3 className="w-3.5 h-3.5" />
                            Dạng cột
                        </button>
                    </div>
                )}
            </CardHeader>

            <CardContent className="pt-6">
                {loading ? (
                    <GaugeSkeleton />
                ) : !safeData ? (
                    <div className="h-64 flex items-center justify-center text-text-secondary/50 text-sm italic">
                        Chưa có dữ liệu phân tích sức khỏe.
                    </div>
                ) : (
                    <div className="animate-in fade-in duration-500 space-y-6">
                        {/* Total score header */}
                        <div className="flex items-end justify-between p-4 rounded-2xl bg-white/[0.02] border border-white/5 relative overflow-hidden">
                            <div>
                                <div className="flex items-baseline gap-2">
                                    <div className="text-5xl font-black font-outfit tracking-tight tabular-nums transition-colors duration-500" style={{ color: scoreColor(safeData.score) }}>
                                        {safeData.score.toFixed(1)}
                                    </div>
                                    {isSimulated && originalData && (
                                        <div className="text-sm font-semibold text-text-muted line-through tabular-nums pb-1">
                                            {originalData.score.toFixed(1)}
                                        </div>
                                    )}
                                    {isSimulated && originalData && (
                                        <div className={`text-sm font-bold pb-1 flex items-center ${safeData.score >= originalData.score ? 'text-emerald-400' : 'text-rose-400'}`}>
                                            {safeData.score >= originalData.score ? '+' : ''}{(safeData.score - originalData.score).toFixed(1)}đ
                                        </div>
                                    )}
                                </div>
                                <div className="text-[10px] font-bold uppercase tracking-widest text-text-muted mt-1.5">
                                    Weighted Sum 8 chiều / 100
                                </div>
                            </div>
                            
                            <div className="flex flex-col items-end gap-1.5">
                                <Badge
                                    variant="outline"
                                    className="font-bold text-xs px-3 py-1 border transition-all duration-500"
                                    style={{ color: scoreColor(safeData.score), borderColor: `${scoreColor(safeData.score)}30`, backgroundColor: `${scoreColor(safeData.score)}08` }}
                                >
                                    {scoreLabel(safeData.score)}
                                </Badge>
                                {safeData.seniority && (
                                    <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                                        {safeData.role} · <span className="text-text-secondary">{safeData.seniority}</span>
                                    </span>
                                )}
                            </div>
                        </div>

                        {hasMulti ? (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
                                {/* Visual Chart Area */}
                                <div className="w-full h-[300px] flex items-center justify-center bg-white/[0.01] rounded-2xl border border-white/5 relative p-4">
                                    {viewMode === 'radar' ? (
                                        <ResponsiveContainer width="100%" height="100%">
                                            <RadarChart data={radarData} margin={{ top: 15, right: 30, bottom: 15, left: 30 }}>
                                                <PolarGrid stroke="rgba(255,255,255,0.06)" />
                                                <PolarAngleAxis
                                                    dataKey="axis"
                                                    tick={{ fill: 'rgba(255,255,255,0.7)', fontSize: 10, fontWeight: 600 }}
                                                />
                                                <PolarRadiusAxis
                                                    domain={[0, 100]}
                                                    angle={90}
                                                    tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 8 }}
                                                    stroke="rgba(255,255,255,0.03)"
                                                />
                                                
                                                <Tooltip
                                                    cursor={false}
                                                    content={({ active, payload }) => {
                                                        if (active && payload && payload.length) {
                                                            const dp = payload[0].payload;
                                                            const currentVal = dp.score;
                                                            const originalVal = dp.originalScore;
                                                            const hasDiff = Math.abs(currentVal - originalVal) > 0.05;
                                                            return (
                                                                <div className="bg-surface/95 border border-white/10 backdrop-blur-xl rounded-xl p-3 shadow-2xl text-[11px] space-y-1.5 min-w-[150px] animate-in fade-in zoom-in-95 duration-100">
                                                                    <div className="font-extrabold text-text-primary border-b border-white/5 pb-1 flex items-center gap-1.5">
                                                                        <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: scoreColor(currentVal) }} />
                                                                        {dp.axis}
                                                                    </div>
                                                                    <div className="flex items-center justify-between gap-4">
                                                                        <span className="text-text-muted">Trọng số (ω):</span>
                                                                        <span className="font-bold text-text-primary tabular-nums">{dp.weight.toFixed(2)}</span>
                                                                    </div>
                                                                    <div className="space-y-1 pt-0.5">
                                                                        {hasDiff ? (
                                                                            <>
                                                                                <div className="flex items-center justify-between gap-4">
                                                                                    <span className="text-text-muted">Điểm gốc:</span>
                                                                                    <span className="font-semibold text-text-secondary tabular-nums">{originalVal.toFixed(0)}</span>
                                                                                </div>
                                                                                <div className="flex items-center justify-between gap-4">
                                                                                    <span className="text-text-muted">Giả lập:</span>
                                                                                    <div className="flex items-center gap-1">
                                                                                        <span className="font-black text-accent-primary tabular-nums">{currentVal.toFixed(0)}</span>
                                                                                        <span className="text-[9px] font-black text-emerald-400">+{ (currentVal - originalVal).toFixed(0) }</span>
                                                                                    </div>
                                                                                </div>
                                                                            </>
                                                                        ) : (
                                                                            <div className="flex items-center justify-between gap-4">
                                                                                <span className="text-text-muted">Đạt điểm:</span>
                                                                                <span className="font-black tabular-nums" style={{ color: scoreColor(currentVal) }}>{currentVal.toFixed(0)}/100</span>
                                                                            </div>
                                                                        )}
                                                                    </div>
                                                                </div>
                                                            );
                                                        }
                                                        return null;
                                                    }}
                                                />

                                                {isSimulated && (
                                                    <Radar
                                                        name="Original"
                                                        dataKey="originalScore"
                                                        stroke="rgba(255,255,255,0.25)"
                                                        fill="rgba(255,255,255,0.05)"
                                                        fillOpacity={0.1}
                                                        strokeWidth={1.5}
                                                        strokeDasharray="4 4"
                                                        isAnimationActive={false}
                                                    />
                                                )}
                                                <Radar
                                                    name={isSimulated ? "Simulated" : "Score"}
                                                    dataKey="score"
                                                    stroke="rgb(var(--accent-primary))"
                                                    fill="rgb(var(--accent-primary))"
                                                    fillOpacity={0.2}
                                                    strokeWidth={2.5}
                                                    isAnimationActive={false}
                                                />
                                            </RadarChart>
                                        </ResponsiveContainer>
                                    ) : (
                                        <ResponsiveContainer width="100%" height="100%">
                                            <BarChart data={radarData} layout="vertical" margin={{ top: 10, right: 15, left: -5, bottom: 5 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" horizontal={false} />
                                                <XAxis type="number" domain={[0, 100]} tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 8 }} stroke="rgba(255,255,255,0.04)" />
                                                <YAxis dataKey="axis" type="category" tick={{ fill: 'rgba(255,255,255,0.7)', fontSize: 9, fontWeight: 600 }} width={75} stroke="rgba(255,255,255,0.04)" />
                                                
                                                <Tooltip
                                                    cursor={{ fill: 'rgba(255,255,255,0.02)' }}
                                                    content={({ active, payload }) => {
                                                        if (active && payload && payload.length) {
                                                            const dp = payload[0].payload;
                                                            const currentVal = dp.score;
                                                            const originalVal = dp.originalScore;
                                                            const hasDiff = Math.abs(currentVal - originalVal) > 0.05;
                                                            return (
                                                                <div className="bg-surface/95 border border-white/10 backdrop-blur-xl rounded-xl p-3 shadow-2xl text-[11px] space-y-1.5 min-w-[150px]">
                                                                    <div className="font-extrabold text-text-primary border-b border-white/5 pb-1 flex items-center gap-1.5">
                                                                        <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: scoreColor(currentVal) }} />
                                                                        {dp.axis}
                                                                    </div>
                                                                    <div className="flex items-center justify-between gap-4">
                                                                        <span className="text-text-muted">Trọng số (ω):</span>
                                                                        <span className="font-bold text-text-primary tabular-nums">{dp.weight.toFixed(2)}</span>
                                                                    </div>
                                                                    <div className="space-y-1 pt-0.5">
                                                                        {hasDiff ? (
                                                                            <>
                                                                                <div className="flex items-center justify-between gap-4">
                                                                                    <span className="text-text-muted">Điểm gốc:</span>
                                                                                    <span className="font-semibold text-text-secondary tabular-nums">{originalVal.toFixed(0)}</span>
                                                                                </div>
                                                                                <div className="flex items-center justify-between gap-4">
                                                                                    <span className="text-text-muted">Giả lập:</span>
                                                                                    <div className="flex items-center gap-1">
                                                                                        <span className="font-black text-accent-primary tabular-nums">{currentVal.toFixed(0)}</span>
                                                                                        <span className="text-[9px] font-black text-emerald-400">+{ (currentVal - originalVal).toFixed(0) }</span>
                                                                                    </div>
                                                                                </div>
                                                                            </>
                                                                        ) : (
                                                                            <div className="flex items-center justify-between gap-4">
                                                                                <span className="text-text-muted">Đạt điểm:</span>
                                                                                <span className="font-black tabular-nums" style={{ color: scoreColor(currentVal) }}>{currentVal.toFixed(0)}/100</span>
                                                                            </div>
                                                                        )}
                                                                    </div>
                                                                </div>
                                                            );
                                                        }
                                                        return null;
                                                    }}
                                                />

                                                {isSimulated && (
                                                    <Bar dataKey="originalScore" fill="rgba(255, 255, 255, 0.15)" radius={[0, 4, 4, 0]} barSize={6} isAnimationActive={false} />
                                                )}
                                                <Bar dataKey="score" radius={[0, 4, 4, 0]} barSize={isSimulated ? 6 : 10} isAnimationActive={false}>
                                                    {radarData.map((entry, index) => (
                                                        <Cell key={`cell-${index}`} fill={scoreColor(entry.score)} />
                                                    ))}
                                                </Bar>
                                            </BarChart>
                                        </ResponsiveContainer>
                                    )}
                                </div>

                                {/* Per-dimension breakdown details */}
                                <div className="space-y-2.5">
                                    {safeData.dimensions!.map(d => {
                                        const orig = originalData?.dimensions?.find(od => od.name === d.name);
                                        const origVal = orig ? orig.score : d.score;
                                        const diff = d.score - origVal;
                                        const hasDiff = Math.abs(diff) > 0.05;

                                        return (
                                            <div
                                                key={d.name}
                                                className="flex flex-col gap-1.5 p-3 rounded-xl bg-white/[0.015] border border-white/[0.04] text-xs hover:bg-white/[0.03] transition-all relative group/item"
                                            >
                                                <div className="flex items-center justify-between">
                                                    <div className="font-bold text-text-primary flex items-center gap-1.5">
                                                        {DIM_LABELS[d.name] ?? d.name}
                                                        {d.detail && (
                                                            <div className="relative group/tooltip">
                                                                <HelpCircle className="w-3.5 h-3.5 text-text-muted hover:text-text-secondary cursor-help" />
                                                                <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 opacity-0 group-hover/tooltip:opacity-100 transition-opacity pointer-events-none bg-black/90 text-[10px] text-white px-2 py-1 rounded shadow-xl whitespace-pre-wrap max-w-xs z-50">
                                                                    {d.detail}
                                                                </span>
                                                            </div>
                                                        )}
                                                    </div>
                                                    <div className="flex items-center gap-3">
                                                        {hasDiff && (
                                                            <span className="text-[10px] font-bold text-emerald-400">
                                                                +{diff.toFixed(0)}đ
                                                            </span>
                                                        )}
                                                        <div className="font-black tabular-nums" style={{ color: scoreColor(d.score) }}>
                                                            {d.score.toFixed(0)} <span className="text-text-muted font-normal text-[10px]">/100</span>
                                                        </div>
                                                        <div className="text-text-muted font-medium font-mono text-[10px]">
                                                            ω={d.weight.toFixed(2)}
                                                        </div>
                                                    </div>
                                                </div>
                                                
                                                <div className="w-full h-1.5 rounded-full bg-white/5 overflow-hidden relative">
                                                    {/* Original score indicator in back */}
                                                    {isSimulated && (
                                                        <div
                                                            className="absolute top-0 left-0 h-full bg-white/20 transition-all duration-500 rounded-full"
                                                            style={{ width: `${Math.min(100, origVal)}%` }}
                                                        />
                                                    )}
                                                    {/* Simulated/Current score indicator */}
                                                    <div
                                                        className="h-full rounded-full transition-all duration-500 relative z-10"
                                                        style={{
                                                            width: `${Math.min(100, d.score)}%`,
                                                            background: scoreColor(d.score),
                                                        }}
                                                    />
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        ) : (
                            <div className="py-8 text-center text-xs text-text-secondary italic">
                                Chưa nhận được breakdown 8 chiều từ backend.
                            </div>
                        )}

                        {/* Footer metadata */}
                        <div className="mt-4 flex flex-wrap gap-2 items-center justify-between text-xs border-t border-white/5 pt-4">
                            <div className="text-text-secondary flex items-center gap-1.5">
                                Snapshot: <span className="text-text-primary font-semibold">{safeData.snapshot_date}</span>
                            </div>
                            {safeData.cold_start && (
                                <Badge variant="destructive" className="!text-[9px] font-bold animate-pulse">
                                    Cold start · cần ≥4 tuần dữ liệu
                                </Badge>
                            )}
                        </div>

                        {/* Top Missing/Ideal Skills to learn */}
                        {safeData.missing_ideal.length > 0 && (
                            <div className="mt-4 p-4 rounded-xl bg-white/[0.01] border border-white/5 text-xs text-text-secondary space-y-3">
                                <span className="font-extrabold uppercase tracking-widest text-[10px] text-text-muted block">Các kỹ năng thiếu hụt ưu tiên học: </span>
                                <div className="flex flex-wrap gap-2">
                                    {safeData.missing_ideal.slice(0, 5).map(skill => (
                                        <button 
                                            key={skill}
                                            onClick={() => navigate(`/market-intel?skill=${encodeURIComponent(skill)}`)}
                                            className="px-2.5 py-1.5 rounded-lg bg-white/5 border border-white/8 hover:border-accent-primary/40 hover:bg-accent-primary/10 transition-all flex items-center gap-1.5 group cursor-pointer"
                                            title="Xem chi tiết tuyển dụng & mức lương"
                                        >
                                            <span className="font-medium text-text-secondary group-hover:text-accent-primary transition-colors">{skill}</span>
                                            <ExternalLink className="w-3 h-3 text-text-muted group-hover:text-accent-primary transition-colors" />
                                        </button>
                                    ))}
                                    {safeData.missing_ideal.length > 5 && (
                                        <span className="self-center text-text-muted text-[11px] font-semibold pl-1">
                                            và {safeData.missing_ideal.length - 5} kỹ năng khác
                                        </span>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

export default memo(FreshnessGaugeInner);
