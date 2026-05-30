import { memo } from 'react';
import { ExternalLink, MapPin, Building2, Calendar, CircleDollarSign, Briefcase, GraduationCap, AlertTriangle, Target } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../ui/Card';
import { Badge } from '../../ui/Badge';
import { ListSkeleton } from '../../ui/Skeleton';
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

function DimTag({ label, score }: { label: string; score: number }) {
    const tone =
        score >= 0.85 ? 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20' :
        score >= 0.55 ? 'text-blue-400 bg-blue-400/10 border-blue-400/20' : 
        'text-amber-400 bg-amber-400/10 border-amber-400/20';
    return (
        <div className={`px-2 py-0.5 rounded text-[10px] font-bold border flex items-center gap-1.5 ${tone}`}>
            {label}
            <span className="opacity-70">{(score * 100).toFixed(0)}%</span>
        </div>
    );
}

function OpportunityCard({ jd }: { jd: OpportunityJD }) {
    const salary = formatSalary(jd.salary_min, jd.salary_max, jd.salary_currency);
    const wm = workModeLabel(jd.work_mode);
    const sen = seniorityLabel(jd.seniority);
    const exp = expRange(jd.min_exp, jd.max_exp);

    // Dynamic coloring for Match Score
    const scoreColor = jd.match_score >= 0.8 ? 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20' : 
                       jd.match_score >= 0.6 ? 'text-blue-400 bg-blue-400/10 border-blue-400/20' : 
                       'text-amber-400 bg-amber-400/10 border-amber-400/20';

    return (
        <li className="relative flex flex-col gap-4 p-5 rounded-2xl bg-white/[0.02] hover:bg-white/[0.04] transition-all duration-300 border border-white/5 hover:border-white/10 group overflow-hidden">
            {/* Background Accent Glow based on Match */}
            <div className={`absolute top-0 right-0 w-32 h-32 blur-[40px] opacity-0 group-hover:opacity-20 transition-opacity duration-500 rounded-full pointer-events-none ${scoreColor.split(' ')[0].replace('text-', 'bg-')}`} />

            {/* Header: Title & Match Score */}
            <div className="flex items-start justify-between gap-4 relative z-10">
                <div className="flex-1 min-w-0 space-y-2">
                    {jd.url ? (
                        <a
                            href={jd.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-base font-extrabold font-outfit text-text-primary hover:text-accent-primary transition-colors flex items-center gap-2 truncate group/link"
                        >
                            {jd.title}
                            <ExternalLink className="w-3.5 h-3.5 opacity-0 group-hover/link:opacity-100 transition-opacity text-accent-primary shrink-0" />
                        </a>
                    ) : (
                        <span className="text-base font-extrabold font-outfit text-text-primary block truncate">
                            {jd.title}
                        </span>
                    )}
                    
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-text-secondary">
                        <div className="flex items-center gap-1.5 font-medium text-text-primary/80">
                            <Building2 className="w-3.5 h-3.5 text-text-muted" />
                            {jd.company}
                        </div>
                        {jd.location && (
                            <div className="flex items-center gap-1.5">
                                <MapPin className="w-3.5 h-3.5 text-text-muted" />
                                {jd.location}
                            </div>
                        )}
                        <div className="flex items-center gap-1.5">
                            <Calendar className="w-3.5 h-3.5 text-text-muted" />
                            {jd.posted_date}
                        </div>
                        {salary && (
                            <div className="flex items-center gap-1.5 text-emerald-400 font-bold bg-emerald-400/10 px-2 py-0.5 rounded-md border border-emerald-400/20">
                                <CircleDollarSign className="w-3.5 h-3.5" />
                                {salary}
                            </div>
                        )}
                    </div>
                </div>

                <div className={`shrink-0 flex flex-col items-center justify-center w-12 h-12 rounded-xl border ${scoreColor} shadow-sm relative z-10`}>
                    <span className="text-[15px] font-black leading-none">{(jd.match_score * 100).toFixed(0)}</span>
                    <span className="text-[8px] font-bold uppercase tracking-widest opacity-80 mt-0.5">Match</span>
                </div>
            </div>

            {/* Enriched Signals (Tags) & Dim Breakdown */}
            <div className="flex flex-col gap-3 relative z-10">
                <div className="flex items-center gap-2 flex-wrap text-[11px]">
                    {sen && (
                        <span className="px-2.5 py-1 rounded-lg bg-surface border border-white/5 text-text-secondary font-medium flex items-center gap-1.5 shadow-sm">
                            <GraduationCap className="w-3 h-3 text-text-muted" />
                            {sen}
                        </span>
                    )}
                    {exp && (
                        <span className="px-2.5 py-1 rounded-lg bg-surface border border-white/5 text-text-secondary font-medium flex items-center gap-1.5 shadow-sm">
                            <Briefcase className="w-3 h-3 text-text-muted" />
                            {exp}
                        </span>
                    )}
                    {wm && (
                        <span className={[
                            'px-2.5 py-1 rounded-lg border font-bold flex items-center gap-1.5 shadow-sm',
                            jd.work_mode_match
                                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                                : 'bg-amber-500/10 border-amber-500/20 text-amber-400',
                        ].join(' ')}>
                            {wm}
                        </span>
                    )}
                    {!jd.location_match && jd.location && (
                        <span className="px-2.5 py-1 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 font-bold flex items-center gap-1.5 shadow-sm">
                            <AlertTriangle className="w-3 h-3" />
                            Khác địa điểm
                        </span>
                    )}
                </div>

                <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[10px] uppercase font-bold text-text-muted mr-1 flex items-center gap-1">
                        <Target className="w-3 h-3" /> Chi tiết:
                    </span>
                    <DimTag label="Required" score={jd.skill_required_coverage} />
                    {jd.skill_preferred_coverage > 0 && (
                        <DimTag label="Preferred" score={jd.skill_preferred_coverage} />
                    )}
                    <DimTag label="Exp fit" score={jd.exp_fit} />
                </div>
            </div>

            {/* Description summary */}
            {jd.description_summary && (
                <p className="text-[13px] text-text-secondary/90 leading-relaxed line-clamp-3 relative z-10 bg-black/10 p-3 rounded-xl border border-white/[0.03]">
                    {jd.description_summary}
                </p>
            )}

            {/* Blockers & Missing Skills Container */}
            {(jd.blockers.length > 0 || jd.missing_required.length > 0) && (
                <div className="space-y-2 pt-3 mt-1 border-t border-white/5 relative z-10">
                    {jd.blockers.length > 0 && (
                        <div className="text-[11px] text-rose-400 space-y-1.5">
                            {jd.blockers.map((b, i) => (
                                <div key={i} className="flex items-start gap-1.5">
                                    <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                                    <span className="leading-relaxed font-medium">{b}</span>
                                </div>
                            ))}
                        </div>
                    )}

                    {jd.missing_required.length > 0 && jd.blockers.every(b => !b.includes('skill')) && (
                        <div className="text-xs flex items-center gap-2 flex-wrap">
                            <span className="text-text-muted font-semibold text-[10px] uppercase tracking-wider">Cần bổ sung:</span>
                            <div className="flex gap-1.5 flex-wrap">
                                {jd.missing_required.slice(0, 4).map(skill => (
                                    <span key={skill} className="px-2 py-1 rounded-md text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20 shadow-sm">
                                        {skill}
                                    </span>
                                ))}
                                {jd.missing_required.length > 4 && (
                                    <span className="px-2 py-1 rounded-md text-[10px] font-bold bg-white/5 text-text-muted border border-white/10">
                                        +{jd.missing_required.length - 4}
                                    </span>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </li>
    );
}


function OpportunityWindowInner({ data, loading }: Props) {
    const items = data?.items ?? [];

    return (
        <Card className="bg-surface/80 border border-white/5 shadow-xl">
            <CardHeader className="border-b border-white/5 pb-5">
                <CardTitle className="font-outfit text-xl font-black flex items-center gap-2">
                    <Target className="w-5 h-5 text-accent-primary" />
                    Opportunity Window
                </CardTitle>
                <CardDescription className="text-xs">
                    JD mới (trong {data?.days ?? 7} ngày) phù hợp với CV của bạn — match theo skill, exp, location, work mode
                </CardDescription>
            </CardHeader>
            <CardContent className="pt-5">
                {loading ? (
                    <ListSkeleton rows={3} />
                ) : items.length === 0 ? (
                    <div className="h-24 flex items-center justify-center text-text-secondary/50 text-sm">
                        Không có JD nào phù hợp trong cửa sổ thời gian này
                    </div>
                ) : (
                    <ul className="space-y-4 animate-in fade-in duration-500">
                        {items.map(jd => <OpportunityCard key={jd.jd_key} jd={jd} />)}
                    </ul>
                )}
            </CardContent>
        </Card>
    );
}

export default memo(OpportunityWindowInner);
