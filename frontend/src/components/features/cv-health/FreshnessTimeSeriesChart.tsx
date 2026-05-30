import { memo, useMemo } from 'react';
import {
    Area, AreaChart, CartesianGrid, ResponsiveContainer,
    Tooltip, XAxis, YAxis,
} from 'recharts';
import { Activity } from 'lucide-react';
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
        <Card className="bg-surface/80 border border-white/5 shadow-xl">
            <CardHeader className="border-b border-white/5 pb-5">
                <CardTitle className="font-outfit text-xl font-black flex items-center gap-2">
                    <Activity className="w-5 h-5 text-accent-primary" />
                    Lịch sử Freshness
                </CardTitle>
                <CardDescription className="text-xs">
                    Diễn biến điểm sức khỏe CV theo thời gian
                </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
                {loading ? (
                    <ChartSkeleton height={240} />
                ) : points.length === 0 ? (
                    <div className="h-56 flex items-center justify-center text-text-secondary/50 text-sm">
                        Chưa có lịch sử. Hãy upload CV để bắt đầu theo dõi.
                    </div>
                ) : (
                    <div className="animate-in fade-in duration-500">
                    <ResponsiveContainer width="100%" height={250}>
                        <AreaChart data={points} margin={{ top: 10, right: 10, bottom: 0, left: -20 }}>
                            <defs>
                                <linearGradient id="freshnessGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="rgb(var(--accent-primary))" stopOpacity={0.4} />
                                    <stop offset="100%" stopColor="rgb(var(--accent-primary))" stopOpacity={0.0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="4 4" stroke="rgba(255,255,255,0.04)" vertical={false} />
                            <XAxis
                                dataKey="date"
                                tick={{ fill: 'currentColor', fontSize: 10, opacity: 0.4 }}
                                stroke="currentColor"
                                strokeOpacity={0.1}
                                axisLine={false}
                                tickLine={false}
                                tickMargin={12}
                            />
                            <YAxis
                                domain={[0, 100]}
                                tick={{ fill: 'currentColor', fontSize: 10, opacity: 0.4 }}
                                stroke="currentColor"
                                strokeOpacity={0.1}
                                width={40}
                                axisLine={false}
                                tickLine={false}
                                tickMargin={12}
                            />
                            <Tooltip
                                contentStyle={{
                                    background: 'rgba(20,20,20,0.95)',
                                    backdropFilter: 'blur(8px)',
                                    border: '1px solid rgba(255,255,255,0.1)',
                                    borderRadius: '0.75rem',
                                    fontSize: '13px',
                                    fontWeight: '600',
                                    boxShadow: '0 10px 30px -10px rgba(0,0,0,0.5)',
                                }}
                                itemStyle={{ color: 'rgb(var(--accent-primary))' }}
                                labelStyle={{ color: 'rgba(255,255,255,0.5)', fontSize: '11px', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}
                                cursor={{ stroke: 'rgba(255,255,255,0.1)', strokeWidth: 2, strokeDasharray: '4 4' }}
                                formatter={(value) => {
                                    const n = typeof value === 'number' ? value : Number(value);
                                    return [Number.isFinite(n) ? n.toFixed(1) : String(value), 'Score'];
                                }}
                            />
                            <Area
                                type="monotone"
                                dataKey="score"
                                stroke="rgb(var(--accent-primary))"
                                strokeWidth={3}
                                fill="url(#freshnessGradient)"
                                isAnimationActive={true}
                                animationDuration={1000}
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
