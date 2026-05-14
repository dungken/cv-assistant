import { memo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../ui/Card';
import { Badge } from '../../ui/Badge';
import { Button } from '../../ui/Button';
import type { LearningPathResponse } from '../../../services/api';

interface Props {
    data: LearningPathResponse | null;
    loading?: boolean;
    error?: string | null;
    budgetWeeks: number;
    algorithm: 'greedy' | 'dijkstra' | 'dp';
    onConfigChange: (budget: number, algorithm: 'greedy' | 'dijkstra' | 'dp') => void;
}

const BUDGETS = [4, 8, 12, 16, 24];
const ALGOS: Array<{ id: 'greedy' | 'dijkstra' | 'dp'; label: string }> = [
    { id: 'greedy', label: 'Greedy' },
    { id: 'dijkstra', label: 'Dijkstra' },
    { id: 'dp', label: 'DP' },
];

function LearningPathViewInner({
    data, loading, error, budgetWeeks, algorithm, onConfigChange,
}: Props) {
    const [expanded, setExpanded] = useState<Record<number, boolean>>({});

    return (
        <Card className="bg-surface/80 border border-white/5">
            <CardHeader>
                <CardTitle>Learning Path</CardTitle>
                <CardDescription>
                    Lộ trình học tối ưu — mở khóa được nhiều JD nhất trong budget
                </CardDescription>
            </CardHeader>
            <CardContent>
                <div className="flex flex-wrap items-center gap-4 mb-6">
                    <div className="flex items-center gap-2">
                        <span className="text-xs uppercase tracking-widest text-text-secondary font-bold">
                            Budget
                        </span>
                        {BUDGETS.map(b => (
                            <Button
                                key={b}
                                size="sm"
                                variant={b === budgetWeeks ? 'default' : 'ghost'}
                                onClick={() => onConfigChange(b, algorithm)}
                                className="h-8 px-3 text-xs"
                            >
                                {b}w
                            </Button>
                        ))}
                    </div>
                    <div className="flex items-center gap-2 ml-auto">
                        <span className="text-xs uppercase tracking-widest text-text-secondary font-bold">
                            Algo
                        </span>
                        {ALGOS.map(a => (
                            <Button
                                key={a.id}
                                size="sm"
                                variant={a.id === algorithm ? 'default' : 'ghost'}
                                onClick={() => onConfigChange(budgetWeeks, a.id)}
                                className="h-8 px-3 text-xs"
                            >
                                {a.label}
                            </Button>
                        ))}
                    </div>
                </div>

                {loading ? (
                    <div className="h-32 flex items-center justify-center text-text-secondary/50 text-sm">
                        Đang tính toán lộ trình…
                    </div>
                ) : error ? (
                    <div className="p-4 rounded-xl bg-rose-500/5 border border-rose-500/10 text-sm text-rose-400">
                        {error}
                    </div>
                ) : !data || data.steps.length === 0 ? (
                    <div className="h-32 flex items-center justify-center text-text-secondary/50 text-sm">
                        Không tìm được lộ trình phù hợp. Hãy tăng budget hoặc thay đổi role.
                    </div>
                ) : (
                    <>
                        <div className="grid grid-cols-4 gap-3 mb-6">
                            <Stat label="Algorithm" value={data.algorithm.toUpperCase()} />
                            <Stat label="Tổng tuần" value={`${data.total_weeks}w`} />
                            <Stat
                                label="JD unlock"
                                value={`${data.jd_unlocked_count}/${data.jd_unlocked_total}`}
                            />
                            <Stat label="Runtime" value={`${data.runtime_ms.toFixed(1)} ms`} />
                        </div>

                        <ol className="space-y-3">
                            {data.steps.map(step => (
                                <li
                                    key={step.order}
                                    className="relative pl-12"
                                >
                                    <div className="absolute left-0 top-0 w-8 h-8 rounded-full bg-accent-primary/20 border border-accent-primary/40 flex items-center justify-center text-xs font-black text-accent-primary">
                                        {step.order}
                                    </div>
                                    <div
                                        className="p-4 rounded-xl bg-surface/40 border border-white/5 cursor-pointer hover:bg-surface-hover/40 transition-colors"
                                        onClick={() => setExpanded(e => ({ ...e, [step.order]: !e[step.order] }))}
                                    >
                                        <div className="flex items-center justify-between gap-3">
                                            <div className="flex-1 min-w-0">
                                                <div className="text-sm font-bold text-text-primary">
                                                    {step.skill}
                                                </div>
                                                <div className="text-xs text-text-secondary mt-1">
                                                    {step.reason}
                                                </div>
                                            </div>
                                            <Badge variant="outline" className="shrink-0">
                                                {step.cost_weeks}w
                                            </Badge>
                                        </div>
                                        {expanded[step.order] && step.jd_unlocked_after_this.length > 0 && (
                                            <div className="mt-3 pt-3 border-t border-white/5 text-xs text-text-secondary">
                                                <div className="font-bold uppercase tracking-widest opacity-60 mb-1.5">
                                                    JD đã mở khóa
                                                </div>
                                                <ul className="space-y-1">
                                                    {step.jd_unlocked_after_this.slice(0, 8).map(jdKey => {
                                                        const entry = data.jd_labels?.[jdKey];
                                                        const label = entry?.label ?? jdKey;
                                                        return (
                                                            <li key={jdKey} className="truncate">
                                                                · {entry?.url ? (
                                                                    <a
                                                                        href={entry.url}
                                                                        target="_blank"
                                                                        rel="noopener noreferrer"
                                                                        className="text-accent-primary hover:underline"
                                                                        onClick={e => e.stopPropagation()}
                                                                    >
                                                                        {label}
                                                                    </a>
                                                                ) : label}
                                                            </li>
                                                        );
                                                    })}
                                                </ul>
                                                {step.jd_unlocked_after_this.length > 8 && (
                                                    <div className="opacity-50 mt-1">
                                                        + {step.jd_unlocked_after_this.length - 8} JD khác
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                </li>
                            ))}
                        </ol>

                        <div className="mt-4 text-xs text-text-secondary text-center">
                            Coverage: <span className="font-bold text-text-primary">{data.coverage_percent.toFixed(1)}%</span>
                            {' '}của tổng JD trong cửa sổ thời gian
                        </div>
                    </>
                )}
            </CardContent>
        </Card>
    );
}

function Stat({ label, value }: { label: string; value: string }) {
    return (
        <div className="p-3 rounded-xl bg-surface/40 border border-white/5">
            <div className="text-[10px] uppercase tracking-widest text-text-secondary font-bold">
                {label}
            </div>
            <div className="text-base font-bold text-text-primary mt-1 tabular-nums">
                {value}
            </div>
        </div>
    );
}

export default memo(LearningPathViewInner);
