import { memo, useMemo } from 'react';
import { RadialBar, RadialBarChart, PolarAngleAxis, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../ui/Card';
import { Badge } from '../../ui/Badge';
import { GaugeSkeleton } from '../../ui/Skeleton';
import type { HealthScoreResponse } from '../../../services/api';

interface Props {
    data: HealthScoreResponse | null;
    loading?: boolean;
}

function scoreColor(score: number): string {
    if (score >= 75) return '#10b981'; // emerald
    if (score >= 50) return '#f59e0b'; // amber
    if (score >= 25) return '#f97316'; // orange
    return '#ef4444';                  // red
}

function scoreLabel(score: number): string {
    if (score >= 85) return 'Xuất sắc';
    if (score >= 70) return 'Tốt';
    if (score >= 50) return 'Trung bình';
    if (score >= 30) return 'Cần cải thiện';
    return 'Lỗi thời';
}

function FreshnessGaugeInner({ data, loading }: Props) {
    const chartData = useMemo(() => {
        const score = data?.score ?? 0;
        return [{ name: 'score', value: score, fill: scoreColor(score) }];
    }, [data]);

    // Defensive: typeof check before .toFixed so we never crash if the API
    // returns an unexpected shape (e.g. gateway forwarding an error body).
    const safeData = data && typeof data.score === 'number' ? data : null;

    return (
        <Card className="bg-surface/80 border border-white/5">
            <CardHeader>
                <CardTitle>CV Freshness Score</CardTitle>
                <CardDescription>
                    Mức độ cập nhật của CV theo thị trường hiện tại
                </CardDescription>
            </CardHeader>
            <CardContent>
                {loading || !safeData ? (
                    loading ? (
                        <GaugeSkeleton />
                    ) : (
                        <div className="h-64 flex items-center justify-center text-text-secondary/50 text-sm">
                            Chưa có dữ liệu
                        </div>
                    )
                ) : (
                    <div className="relative">
                        <ResponsiveContainer width="100%" height={240}>
                            <RadialBarChart
                                innerRadius="75%"
                                outerRadius="100%"
                                data={chartData}
                                startAngle={210}
                                endAngle={-30}
                            >
                                <PolarAngleAxis
                                    type="number"
                                    domain={[0, 100]}
                                    angleAxisId={0}
                                    tick={false}
                                />
                                <RadialBar
                                    background={{ fill: 'rgba(255,255,255,0.05)' }}
                                    dataKey="value"
                                    cornerRadius={20}
                                />
                            </RadialBarChart>
                        </ResponsiveContainer>
                        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                            <div className="text-6xl font-black font-outfit tabular-nums">
                                {safeData.score.toFixed(1)}
                            </div>
                            <div className="text-xs uppercase tracking-widest text-text-secondary mt-1">
                                / 100
                            </div>
                            <Badge
                                variant="outline"
                                className="mt-3"
                                style={{ color: scoreColor(safeData.score) }}
                            >
                                {scoreLabel(safeData.score)}
                            </Badge>
                        </div>

                        <div className="mt-6 flex flex-wrap gap-2 items-center justify-between">
                            <div className="text-xs text-text-secondary">
                                Snapshot: <span className="text-text-primary font-medium">{safeData.snapshot_date}</span>
                                {' · '}
                                Role: <span className="text-text-primary font-medium">{safeData.role}</span>
                            </div>
                            {safeData.cold_start && (
                                <Badge variant="destructive" className="!text-[9px]">
                                    Cold start · cần ≥4 tuần dữ liệu
                                </Badge>
                            )}
                        </div>

                        {safeData.contributions.length > 0 && (
                            <div className="mt-6">
                                <div className="text-xs font-bold uppercase tracking-widest text-text-secondary mb-3">
                                    Top kỹ năng đóng góp
                                </div>
                                <ul className="space-y-2">
                                    {safeData.contributions.slice(0, 5).map(c => (
                                        <li
                                            key={c.skill}
                                            className="flex items-center justify-between text-sm py-1.5 px-3 rounded-lg bg-surface/40"
                                        >
                                            <span className="font-medium">{c.skill}</span>
                                            <div className="flex items-center gap-3 text-xs text-text-secondary">
                                                <span title="Trend (≥1 = đang nóng)">📈 {c.trend.toFixed(2)}</span>
                                                <span title="Recency">⏱ {c.recency.toFixed(1)}</span>
                                                <span className="font-bold text-accent-primary tabular-nums w-12 text-right">
                                                    +{c.contribution.toFixed(1)}
                                                </span>
                                            </div>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {safeData.missing_ideal.length > 0 && (
                            <div className="mt-4 text-xs text-text-secondary">
                                <span className="font-bold uppercase tracking-widest">Thiếu so với ideal: </span>
                                <span>{safeData.missing_ideal.slice(0, 5).join(', ')}</span>
                                {safeData.missing_ideal.length > 5 && (
                                    <span> · +{safeData.missing_ideal.length - 5}</span>
                                )}
                            </div>
                        )}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

// Memoize so the heavy radial chart doesn't re-render unless `data` or
// `loading` actually change (parent re-renders on every fetchAll iteration).
export default memo(FreshnessGaugeInner);
