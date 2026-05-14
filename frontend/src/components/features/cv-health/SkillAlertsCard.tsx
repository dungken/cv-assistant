import { memo } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../ui/Card';
import { Badge } from '../../ui/Badge';
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
        <Card className="bg-surface/80 border border-white/5">
            <CardHeader>
                <CardTitle>Skill Alerts</CardTitle>
                <CardDescription>
                    Cảnh báo khi điểm Freshness giảm hơn 5 điểm giữa 2 lần đo
                </CardDescription>
            </CardHeader>
            <CardContent>
                {loading ? (
                    <div className="h-24 flex items-center justify-center text-text-secondary/50 text-sm">
                        Đang tải…
                    </div>
                ) : alerts.length === 0 ? (
                    <div className="h-24 flex items-center justify-center text-text-secondary/50 text-sm">
                        Chưa có cảnh báo nào. CV của bạn đang ổn định ✓
                    </div>
                ) : (
                    <ul className="space-y-3">
                        {alerts.map(a => (
                            <li
                                key={a.id}
                                className="flex flex-col gap-2 p-4 rounded-xl bg-rose-500/5 border border-rose-500/10"
                            >
                                <div className="flex items-start justify-between gap-3">
                                    <div className="flex-1 min-w-0">
                                        <div className="text-sm font-medium text-text-primary">
                                            {a.reason}
                                        </div>
                                        <div className="text-xs text-text-secondary mt-1">
                                            {formatFiredAt(a.fired_at)} · Role: {a.role}
                                        </div>
                                    </div>
                                    <Badge variant="destructive" className="shrink-0">
                                        −{a.delta.toFixed(1)}
                                    </Badge>
                                </div>
                                <div className="flex items-center gap-2 text-xs text-text-secondary">
                                    <span className="font-medium tabular-nums">{a.prev_score.toFixed(1)}</span>
                                    <span className="opacity-50">→</span>
                                    <span className="font-medium text-rose-400 tabular-nums">{a.new_score.toFixed(1)}</span>
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
