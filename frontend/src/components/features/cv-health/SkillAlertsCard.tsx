import { memo } from 'react';
import { BellRing, TrendingDown, Clock, ShieldAlert } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../ui/Card';
import { ListSkeleton } from '../../ui/Skeleton';
import type { SkillAlertsResponse } from '../../../services/api';

interface Props {
    data: SkillAlertsResponse | null;
    loading?: boolean;
}

function formatFiredAt(iso: string): string {
    try {
        const d = new Date(iso);
        return d.toLocaleString('vi-VN', {
            day: '2-digit', month: '2-digit', year: 'numeric',
            hour: '2-digit', minute: '2-digit',
        });
    } catch {
        return iso;
    }
}

function SkillAlertsCardInner({ data, loading }: Props) {
    const alerts = data?.alerts ?? [];

    return (
        <Card className="bg-surface/80 border border-white/5 shadow-xl">
            <CardHeader className="border-b border-white/5 pb-5">
                <CardTitle className="font-outfit text-xl font-black flex items-center gap-2">
                    <BellRing className="w-5 h-5 text-rose-400" />
                    Skill Alerts
                </CardTitle>
                <CardDescription className="text-xs">
                    Cảnh báo khi điểm Freshness giảm hơn 5 điểm giữa 2 lần đo
                </CardDescription>
            </CardHeader>
            <CardContent className="pt-5">
                {loading ? (
                    <ListSkeleton rows={3} />
                ) : alerts.length === 0 ? (
                    <div className="h-24 flex items-center justify-center text-text-secondary/50 text-sm">
                        Chưa có cảnh báo nào. CV của bạn đang ổn định ✓
                    </div>
                ) : (
                    <ul className="space-y-4 animate-in fade-in duration-500">
                        {alerts.map(a => (
                            <li
                                key={a.id}
                                className="relative flex flex-col gap-3 p-5 rounded-2xl bg-white/[0.02] border border-rose-500/10 hover:border-rose-500/30 transition-all group overflow-hidden"
                            >
                                {/* Glow Effect */}
                                <div className="absolute top-0 right-0 w-32 h-32 bg-rose-500/10 blur-[40px] rounded-full pointer-events-none group-hover:opacity-100 opacity-0 transition-opacity duration-500" />
                                
                                <div className="flex items-start justify-between gap-4 relative z-10">
                                    <div className="flex-1 min-w-0">
                                        <div className="text-[13px] font-medium text-text-primary leading-relaxed flex items-start gap-2">
                                            <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                                            {a.reason}
                                        </div>
                                        <div className="flex items-center gap-3 text-[11px] text-text-muted mt-3">
                                            <div className="flex items-center gap-1.5 bg-black/20 px-2.5 py-1 rounded-md border border-white/5">
                                                <Clock className="w-3 h-3 text-text-secondary" />
                                                {formatFiredAt(a.fired_at)}
                                            </div>
                                            <div className="px-2.5 py-1 bg-white/5 rounded-md border border-white/5">
                                                Role: <span className="font-bold text-text-secondary">{a.role}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="shrink-0 flex flex-col items-end gap-2">
                                        <div className="px-2.5 py-1 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 font-bold text-xs flex items-center gap-1.5 shadow-sm">
                                            <TrendingDown className="w-3.5 h-3.5" />
                                            {a.delta.toFixed(1)}
                                        </div>
                                    </div>
                                </div>

                                {/* Score transition row */}
                                <div className="flex items-center gap-3 relative z-10 pt-3 border-t border-white/5 mt-1">
                                    <span className="text-[10px] uppercase font-bold text-text-muted tracking-wider">Score Drop</span>
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs font-bold text-text-secondary tabular-nums line-through decoration-rose-500/50">{a.prev_score.toFixed(1)}</span>
                                        <span className="text-text-muted opacity-50 text-[10px]">➔</span>
                                        <span className="text-sm font-black text-rose-400 tabular-nums">{a.new_score.toFixed(1)}</span>
                                    </div>
                                </div>
                            </li>
                        ))}
                    </ul>
                )}
            </CardContent>
        </Card>
    );
}

export default memo(SkillAlertsCardInner);
