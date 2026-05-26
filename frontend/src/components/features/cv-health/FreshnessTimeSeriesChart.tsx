import { memo, useMemo } from 'react';
import {
    Area, AreaChart, CartesianGrid, ResponsiveContainer,
    Tooltip, XAxis, YAxis,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../ui/Card';
import { ChartSkeleton } from '../../ui/Skeleton';
import type { FreshnessHistoryResponse } from '../../../services/api';

interface Props {
    data: FreshnessHistoryResponse | null;
    loading?: boolean;
}

function FreshnessTimeSeriesChartInner({ data, loading }: Props) {
    const points = useMemo(() => (data?.points ?? []).map(p => ({
        date: p.snapshot_date.split('T')[0],  // YYYY-MM-DD
        score: p.score,
        coldStart: p.cold_start,
    })), [data]);

    return (
        <Card className="bg-surface/80 border border-white/5">
            <CardHeader>
                <CardTitle>Lịch sử Freshness</CardTitle>
                <CardDescription>
                    Diễn biến điểm sức khỏe CV theo thời gian
                </CardDescription>
            </CardHeader>
            <CardContent>
                {loading ? (
                    <ChartSkeleton height={240} />
                ) : points.length === 0 ? (
                    <div className="h-56 flex items-center justify-center text-text-secondary/50 text-sm">
                        Chưa có lịch sử. Hãy upload CV để bắt đầu theo dõi.
                    </div>
                ) : (
                    <div className="animate-in fade-in duration-500">
                    <ResponsiveContainer width="100%" height={240}>
                        <AreaChart data={points} margin={{ top: 10, right: 12, bottom: 0, left: 0 }}>
                            <defs>
                                <linearGradient id="freshnessGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="rgb(var(--accent-primary))" stopOpacity={0.4} />
                                    <stop offset="100%" stopColor="rgb(var(--accent-primary))" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis
                                dataKey="date"
                                tick={{ fill: 'currentColor', fontSize: 11, opacity: 0.6 }}
                                stroke="currentColor"
                                strokeOpacity={0.1}
                            />
                            <YAxis
                                domain={[0, 100]}
                                tick={{ fill: 'currentColor', fontSize: 11, opacity: 0.6 }}
                                stroke="currentColor"
                                strokeOpacity={0.1}
                                width={32}
                            />
                            <Tooltip
                                contentStyle={{
                                    background: 'rgb(var(--surface))',
                                    border: '1px solid rgba(255,255,255,0.08)',
                                    borderRadius: '0.75rem',
                                    fontSize: '12px',
                                }}
                                labelStyle={{ color: 'rgb(var(--text-secondary))', fontSize: '11px' }}
                                formatter={(value) => {
                                    const n = typeof value === 'number' ? value : Number(value);
                                    return [Number.isFinite(n) ? n.toFixed(2) : String(value), 'Freshness'];
                                }}
                            />
                            <Area
                                type="monotone"
                                dataKey="score"
                                stroke="rgb(var(--accent-primary))"
                                strokeWidth={2}
                                fill="url(#freshnessGradient)"
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

export default memo(FreshnessTimeSeriesChartInner);
