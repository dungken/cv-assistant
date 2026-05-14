import { memo } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../ui/Card';
import { Badge } from '../../ui/Badge';
import type { OpportunityJD, OpportunityWindowResponse } from '../../../services/api';

interface Props {
    data: OpportunityWindowResponse | null;
    loading?: boolean;
}

function formatSalary(min?: number | null, max?: number | null, currency?: string | null): string | null {
    if (!min && !max) return null;
    const c = currency ? ` ${currency}` : '';
    if (min && max) return `${min.toLocaleString()} – ${max.toLocaleString()}${c}`;
    return `~${(min ?? max!).toLocaleString()}${c}`;
}

function workModeLabel(mode?: string | null): string | null {
    if (!mode) return null;
    const m = mode.toLowerCase();
    if (m === 'remote') return 'Remote';
    if (m === 'hybrid') return 'Hybrid';
    if (m === 'onsite') return 'Onsite';
    return mode;
}

function seniorityLabel(s?: string | null): string | null {
    if (!s) return null;
    const map: Record<string, string> = {
        junior: 'Junior', mid: 'Mid', senior: 'Senior', lead: 'Lead', principal: 'Principal',
    };
    return map[s.toLowerCase()] ?? s;
}

function expRange(min?: number | null, max?: number | null): string | null {
    if (min == null && max == null) return null;
    if (min != null && max != null) return `${min}–${max} năm exp`;
    if (min != null) return `${min}+ năm exp`;
    return `≤ ${max} năm exp`;
}

// Tag for each match dimension. Green = good, amber = partial, red = blocker.
function DimTag({ label, score }: { label: string; score: number }) {
    const tone =
        score >= 0.85 ? 'success' :
        score >= 0.55 ? 'outline' : 'destructive';
    return (
        <Badge variant={tone} className="!text-[9px] gap-1">
            {label} {(score * 100).toFixed(0)}%
        </Badge>
    );
}


function OpportunityCard({ jd }: { jd: OpportunityJD }) {
    const salary = formatSalary(jd.salary_min, jd.salary_max, jd.salary_currency);
    const wm = workModeLabel(jd.work_mode);
    const sen = seniorityLabel(jd.seniority);
    const exp = expRange(jd.min_exp, jd.max_exp);

    return (
        <li className="flex flex-col gap-3 p-4 rounded-xl bg-surface/40 hover:bg-surface-hover/40 transition-colors border border-white/5">
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
                        <span className="font-medium">{jd.company}</span>
                        {jd.location && <><span className="opacity-30">·</span><span>{jd.location}</span></>}
                        <span className="opacity-30">·</span>
                        <span>{jd.posted_date}</span>
                        {salary && (
                            <>
                                <span className="opacity-30">·</span>
                                <span className="text-emerald-500 font-medium">{salary}</span>
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

            {/* Enriched signal row */}
            <div className="flex items-center gap-2 flex-wrap text-[10px]">
                {sen && (
                    <span className="px-2 py-0.5 rounded-full bg-surface/60 text-text-secondary font-medium">
                        {sen}
                    </span>
                )}
                {exp && (
                    <span className="px-2 py-0.5 rounded-full bg-surface/60 text-text-secondary font-medium">
                        {exp}
                    </span>
                )}
                {wm && (
                    <span className={[
                        'px-2 py-0.5 rounded-full font-medium',
                        jd.work_mode_match
                            ? 'bg-emerald-500/10 text-emerald-400'
                            : 'bg-amber-500/10 text-amber-400',
                    ].join(' ')}>
                        {wm}
                    </span>
                )}
                {!jd.location_match && jd.location && (
                    <span className="px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 font-medium">
                        khác địa điểm
                    </span>
                )}
            </div>

            {/* Match breakdown */}
            <div className="flex items-center gap-1.5 flex-wrap">
                <DimTag label="Required" score={jd.skill_required_coverage} />
                {jd.skill_preferred_coverage > 0 && (
                    <DimTag label="Preferred" score={jd.skill_preferred_coverage} />
                )}
                <DimTag label="Exp fit" score={jd.exp_fit} />
            </div>

            {/* Description summary */}
            {jd.description_summary && (
                <p className="text-xs text-text-secondary/80 leading-relaxed line-clamp-3">
                    {jd.description_summary}
                </p>
            )}

            {/* Blockers — only show when there are concrete reasons not to apply */}
            {jd.blockers.length > 0 && (
                <div className="text-[11px] text-rose-300/80 space-y-0.5">
                    {jd.blockers.map((b, i) => (
                        <div key={i}>⚠ {b}</div>
                    ))}
                </div>
            )}

            {/* Missing required skills as soft inline note when not in blockers already */}
            {jd.missing_required.length > 0 && jd.blockers.every(b => !b.includes('skill')) && (
                <div className="text-xs text-text-secondary">
                    <span className="opacity-60">Còn thiếu: </span>
                    <span className="text-amber-400">
                        {jd.missing_required.slice(0, 4).join(', ')}
                    </span>
                    {jd.missing_required.length > 4 && (
                        <span> · +{jd.missing_required.length - 4}</span>
                    )}
                </div>
            )}
        </li>
    );
}


function OpportunityWindowInner({ data, loading }: Props) {
    const items = data?.items ?? [];

    return (
        <Card className="bg-surface/80 border border-white/5">
            <CardHeader>
                <CardTitle>Opportunity Window</CardTitle>
                <CardDescription>
                    JD mới (trong {data?.days ?? 7} ngày) phù hợp với CV của bạn — match theo skill, exp, location, work mode
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
                        {items.map(jd => <OpportunityCard key={jd.jd_key} jd={jd} />)}
                    </ul>
                )}
            </CardContent>
        </Card>
    );
}

export default memo(OpportunityWindowInner);
