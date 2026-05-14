import { memo } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../ui/Card';
import { Badge } from '../../ui/Badge';
import type { OpportunityWindowResponse } from '../../../services/api';

interface Props {
    data: OpportunityWindowResponse | null;
    loading?: boolean;
}

function formatSalary(min?: number | null, max?: number | null): string | null {
    if (!min && !max) return null;
    if (min && max) return `${min.toLocaleString()} – ${max.toLocaleString()}`;
    return `~${(min ?? max!).toLocaleString()}`;
}

function OpportunityWindowInner({ data, loading }: Props) {
    const items = data?.items ?? [];

    return (
        <Card className="bg-surface/80 border border-white/5">
            <CardHeader>
                <CardTitle>Opportunity Window</CardTitle>
                <CardDescription>
                    JD mới (trong {data?.days ?? 7} ngày) phù hợp với CV của bạn
                </CardDescription>
            </CardHeader>
            <CardContent>
                {loading ? (
                    <div className="h-24 flex items-center justify-center text-text-secondary/50 text-sm">
                        Đang tìm cơ hội…
                    </div>
                ) : items.length === 0 ? (
                    <div className="h-24 flex items-center justify-center text-text-secondary/50 text-sm">
                        Không có JD nào phù hợp trong cửa sổ thời gian này
                    </div>
                ) : (
                    <ul className="space-y-3">
                        {items.map(jd => (
                            <li
                                key={jd.jd_key}
                                className="flex flex-col gap-2 p-4 rounded-xl bg-surface/40 hover:bg-surface-hover/40 transition-colors border border-white/5"
                            >
                                <div className="flex items-start justify-between gap-3">
                                    <div className="flex-1 min-w-0">
                                        {jd.url ? (
                                            <a
                                                href={jd.url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-sm font-bold text-text-primary hover:text-accent-primary transition-colors block truncate"
                                            >
                                                {jd.title}
                                            </a>
                                        ) : (
                                            <span className="text-sm font-bold text-text-primary block truncate">
                                                {jd.title}
                                            </span>
                                        )}
                                        <div className="text-xs text-text-secondary mt-1 flex items-center gap-2 flex-wrap">
                                            <span>{jd.company}</span>
                                            {jd.location && <><span className="opacity-30">·</span><span>{jd.location}</span></>}
                                            <span className="opacity-30">·</span>
                                            <span>{jd.posted_date}</span>
                                            {formatSalary(jd.salary_min, jd.salary_max) && (
                                                <>
                                                    <span className="opacity-30">·</span>
                                                    <span className="text-emerald-500">
                                                        {formatSalary(jd.salary_min, jd.salary_max)}
                                                    </span>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                    <Badge
                                        variant={jd.match_score >= 0.8 ? 'success' : 'outline'}
                                        className="shrink-0"
                                    >
                                        {(jd.match_score * 100).toFixed(0)}%
                                    </Badge>
                                </div>
                                {jd.missing_skills.length > 0 && (
                                    <div className="text-xs text-text-secondary">
                                        <span className="opacity-60">Còn thiếu: </span>
                                        <span className="text-amber-400">
                                            {jd.missing_skills.slice(0, 4).join(', ')}
                                        </span>
                                        {jd.missing_skills.length > 4 && (
                                            <span> · +{jd.missing_skills.length - 4}</span>
                                        )}
                                    </div>
                                )}
                            </li>
                        ))}
                    </ul>
                )}
            </CardContent>
        </Card>
    );
}

export default memo(OpportunityWindowInner);
