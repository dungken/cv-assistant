import { memo, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer,
} from 'recharts';
import { ExternalLink } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../ui/Card';
import { Badge } from '../../ui/Badge';
import { GaugeSkeleton } from '../../ui/Skeleton';
import type { HealthScoreResponse } from '../../../services/api';

interface Props {
    data: HealthScoreResponse | null;
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
    if (score >= 75) return '#10b981';
    if (score >= 50) return '#f59e0b';
    if (score >= 25) return '#f97316';
    return '#ef4444';
}

function scoreLabel(score: number): string {
    if (score >= 85) return 'Xuất sắc';
    if (score >= 70) return 'Tốt';
    if (score >= 50) return 'Trung bình';
    if (score >= 30) return 'Cần cải thiện';
    return 'Lỗi thời';
}

function FreshnessGaugeInner({ data, loading }: Props) {
    const navigate = useNavigate();
    const safeData = data && typeof data.score === 'number' ? data : null;

    const radarData = useMemo(() => {
        if (!safeData?.dimensions || safeData.dimensions.length === 0) return [];
        return safeData.dimensions.map(d => ({
            axis: DIM_LABELS[d.name] ?? d.name,
            score: d.score,
            weight: d.weight,
            detail: d.detail,
        }));
    }, [safeData]);

    const hasMulti = radarData.length > 0;

    return (
        <Card className="bg-surface/80 border border-white/5">
            <CardHeader>
                <CardTitle>Multi-criteria CV Freshness</CardTitle>
                <CardDescription>
                    Đánh giá CV theo 8 chiều (Skill · Experience · Project · Education · Achievement · Language · Completeness · Market Alignment)
                </CardDescription>
            </CardHeader>
            <CardContent>
                {loading ? (
                    <GaugeSkeleton />
                ) : !safeData ? (
                    <div className="h-64 flex items-center justify-center text-text-secondary/50 text-sm">
                        Chưa có dữ liệu
                    </div>
                ) : (
                    <div className="animate-in fade-in duration-500">
                        {/* Total score header */}
                        <div className="flex items-end justify-between mb-4">
                            <div>
                                <div className="text-5xl font-black font-outfit tabular-nums" style={{ color: scoreColor(safeData.score) }}>
                                    {safeData.score.toFixed(1)}
                                </div>
                                <div className="text-xs uppercase tracking-widest text-text-secondary mt-1">
                                    Weighted Sum 8 chiều / 100
                                </div>
                            </div>
                            <div className="flex flex-col items-end gap-1">
                                <Badge
                                    variant="outline"
                                    style={{ color: scoreColor(safeData.score), borderColor: `${scoreColor(safeData.score)}30` }}
                                >
                                    {scoreLabel(safeData.score)}
                                </Badge>
                                {safeData.seniority && (
                                    <span className="text-[10px] uppercase tracking-wider text-text-muted">
                                        Role: {safeData.role} · {safeData.seniority}
                                    </span>
                                )}
                            </div>
                        </div>

                        {hasMulti ? (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
                                {/* Radar chart */}
                                <ResponsiveContainer width="100%" height={300}>
                                    <RadarChart data={radarData} margin={{ top: 8, right: 30, bottom: 8, left: 30 }}>
                                        <PolarGrid stroke="rgba(255,255,255,0.06)" />
                                        <PolarAngleAxis
                                            dataKey="axis"
                                            tick={{ fill: 'rgb(var(--text-secondary))', fontSize: 10 }}
                                        />
                                        <PolarRadiusAxis
                                            domain={[0, 100]}
                                            angle={90}
                                            tick={{ fill: 'rgb(var(--text-muted))', fontSize: 9 }}
                                            stroke="rgba(255,255,255,0.04)"
                                        />
                                        <Radar
                                            name="Score"
                                            dataKey="score"
                                            stroke="rgb(var(--accent-primary))"
                                            fill="rgb(var(--accent-primary))"
                                            fillOpacity={0.25}
                                            strokeWidth={2}
                                        />
                                    </RadarChart>
                                </ResponsiveContainer>

                                {/* Per-dimension breakdown */}
                                <div className="space-y-1.5">
                                    {safeData.dimensions!.map(d => (
                                        <div
                                            key={d.name}
                                            className="flex items-center gap-3 px-3 py-1.5 rounded-lg bg-surface/30 text-xs"
                                        >
                                            <div className="w-24 font-medium text-text-primary shrink-0">
                                                {DIM_LABELS[d.name] ?? d.name}
                                            </div>
                                            <div className="flex-1 h-1.5 rounded-full bg-white/5 overflow-hidden">
                                                <div
                                                    className="h-full rounded-full"
                                                    style={{
                                                        width: `${Math.min(100, d.score)}%`,
                                                        background: scoreColor(d.score),
                                                    }}
                                                />
                                            </div>
                                            <div className="w-10 text-right tabular-nums font-bold" style={{ color: scoreColor(d.score) }}>
                                                {d.score.toFixed(0)}
                                            </div>
                                            <div className="w-12 text-right text-text-muted tabular-nums">
                                                ω={d.weight.toFixed(2)}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ) : (
                            // Fallback khi chưa có dimensions (legacy compatibility)
                            <div className="py-4 text-center text-xs text-text-secondary">
                                Chưa nhận được breakdown 8 chiều từ backend.
                            </div>
                        )}

                        <div className="mt-4 flex flex-wrap gap-2 items-center justify-between text-xs">
                            <div className="text-text-secondary">
                                Snapshot: <span className="text-text-primary font-medium">{safeData.snapshot_date}</span>
                            </div>
                            {safeData.cold_start && (
                                <Badge variant="destructive" className="!text-[9px]">
                                    Cold start · cần ≥4 tuần dữ liệu
                                </Badge>
                            )}
                        </div>

                        {safeData.missing_ideal.length > 0 && (
                            <div className="mt-3 text-xs text-text-secondary">
                                <span className="font-bold uppercase tracking-widest block mb-2">Skills nên học (top): </span>
                                <div className="flex flex-wrap gap-2">
                                    {safeData.missing_ideal.slice(0, 5).map(skill => (
                                        <button 
                                            key={skill}
                                            onClick={() => navigate(`/market-intel?skill=${encodeURIComponent(skill)}`)}
                                            className="px-2 py-1 rounded bg-white/5 border border-white/10 hover:border-accent-primary hover:bg-accent-primary/10 transition-colors flex items-center gap-1 group"
                                            title="Xem xu hướng và lương của kỹ năng này trên thị trường"
                                        >
                                            {skill}
                                            <ExternalLink className="w-3 h-3 text-text-muted group-hover:text-accent-primary" />
                                        </button>
                                    ))}
                                    {safeData.missing_ideal.length > 5 && (
                                        <span className="self-center"> · +{safeData.missing_ideal.length - 5}</span>
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
