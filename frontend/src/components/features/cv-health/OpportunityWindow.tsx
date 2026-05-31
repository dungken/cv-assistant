import { memo, useState, useEffect, useCallback, useMemo, useRef, Fragment } from 'react';
import {
    ExternalLink, MapPin, Building2, Calendar, CircleDollarSign,
    Briefcase, GraduationCap, AlertTriangle, Target, Bookmark, BookmarkCheck,
    SortAsc, Filter, Sparkles, X, Info, Send, Calendar as CalIcon, Ban, Hourglass,
    CheckCircle2, ChevronLeft, ChevronRight, ChevronDown, Loader2
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../ui/Card';
import { ListSkeleton } from '../../ui/Skeleton';
import {
    Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from '../../ui/Dialog';
import { cvHealthApi, type OpportunityJD, type OpportunityWindowResponse, type JdStatus } from '../../../services/api';
import { LOCATIONS } from '../../../config/jobMeta';

interface Props {
    userId: string;
}

const WORK_MODE_OPTIONS = [
    { id: 'remote', label: 'Remote' },
    { id: 'hybrid', label: 'Hybrid' },
    { id: 'onsite', label: 'Onsite' },
];
const DAYS_OPTIONS = [7, 14, 30, 60, 90];
const PAGE_SIZE = 10;
const SORT_OPTIONS: { id: 'match' | 'newest' | 'salary'; label: string }[] = [
    { id: 'match', label: 'Best match' },
    { id: 'newest', label: 'Mới nhất' },
    { id: 'salary', label: 'Salary cao' },
];

const STATUS_META: Record<JdStatus, { label: string; color: string; icon: typeof Send }> = {
    new: { label: 'Mới', color: 'text-text-muted', icon: Sparkles },
    saved: { label: 'Đã lưu', color: 'text-indigo-400', icon: BookmarkCheck },
    applied: { label: 'Đã apply', color: 'text-blue-400', icon: Send },
    interview: { label: 'Phỏng vấn', color: 'text-amber-400', icon: CalIcon },
    rejected: { label: 'Đã reject', color: 'text-rose-400', icon: Ban },
};

const STATUS_ORDER: JdStatus[] = ['new', 'saved', 'applied', 'interview', 'rejected'];

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

function scoreToneClass(score: number): string {
    return score >= 0.8 ? 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20'
        : score >= 0.6 ? 'text-blue-400 bg-blue-400/10 border-blue-400/20'
        : 'text-amber-400 bg-amber-400/10 border-amber-400/20';
}

function DimTag({ label, score }: { label: string; score: number }) {
    return (
        <div className={`px-2 py-0.5 rounded text-[10px] font-bold border flex items-center gap-1.5 ${scoreToneClass(score)}`}>
            {label}
            <span className="opacity-70">{(score * 100).toFixed(0)}%</span>
        </div>
    );
}

interface CardProps {
    jd: OpportunityJD;
    onStatusChange: (jdKey: string, status: JdStatus) => void;
    onOpenBreakdown: (jd: OpportunityJD) => void;
}

const OpportunityCard = memo(function OpportunityCard({ jd, onStatusChange, onOpenBreakdown }: CardProps) {
    const salary = formatSalary(jd.salary_min, jd.salary_max, jd.salary_currency);
    const wm = workModeLabel(jd.work_mode);
    const sen = seniorityLabel(jd.seniority);
    const exp = expRange(jd.min_exp, jd.max_exp);
    const scoreColor = scoreToneClass(jd.match_score);
    const [statusOpen, setStatusOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const status = jd.status || 'new';
    const StatusIcon = STATUS_META[status].icon;
    const isSaved = status !== 'new' && status !== 'rejected';

    useEffect(() => {
        if (!statusOpen) return;
        const handler = (e: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
                setStatusOpen(false);
            }
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, [statusOpen]);

    return (
        <li className="relative flex flex-col gap-4 p-5 rounded-2xl bg-white/[0.02] hover:bg-white/[0.04] transition-all duration-300 border border-white/5 hover:border-white/10 group">
            {/* Header: Title & Match Score */}
            <div className="flex items-start justify-between gap-4 relative z-10">
                <div className="flex-1 min-w-0 space-y-2">
                    {jd.url ? (
                        <a href={jd.url} target="_blank" rel="noopener noreferrer"
                            className="text-base font-extrabold font-outfit text-text-primary hover:text-accent-primary transition-colors flex items-center gap-2 group/link">
                            <span className="truncate">{jd.title}</span>
                            <ExternalLink className="w-3.5 h-3.5 opacity-0 group-hover/link:opacity-100 transition-opacity text-accent-primary shrink-0" />
                        </a>
                    ) : (
                        <span className="text-base font-extrabold font-outfit text-text-primary block truncate">{jd.title}</span>
                    )}
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-text-secondary">
                        <div className="flex items-center gap-1.5 font-medium text-text-primary/80">
                            <Building2 className="w-3.5 h-3.5 text-text-muted" />{jd.company}
                        </div>
                        {jd.location && (
                            <div className="flex items-center gap-1.5"><MapPin className="w-3.5 h-3.5 text-text-muted" />{jd.location}</div>
                        )}
                        <div className="flex items-center gap-1.5">
                            <Calendar className="w-3.5 h-3.5 text-text-muted" />{jd.posted_date}
                        </div>
                        {salary && (
                            <div className="flex items-center gap-1.5 text-emerald-400 font-bold bg-emerald-400/10 px-2 py-0.5 rounded-md border border-emerald-400/20">
                                <CircleDollarSign className="w-3.5 h-3.5" />{salary}
                            </div>
                        )}
                    </div>
                </div>

                <div className="flex flex-col items-end gap-2">
                    <button type="button"
                        onClick={() => onOpenBreakdown(jd)}
                        className={`shrink-0 flex flex-col items-center justify-center w-14 h-14 rounded-xl border ${scoreColor} shadow-sm hover:scale-105 transition-transform cursor-pointer relative z-10`}
                        title="Xem chi tiết match score"
                    >
                        <span className="text-base font-black leading-none">{(jd.match_score * 100).toFixed(0)}</span>
                        <span className="text-[8px] font-bold uppercase tracking-widest opacity-80 mt-0.5">Match</span>
                    </button>
                    {/* Status pill + dropdown */}
                    <div className="relative" ref={dropdownRef}>
                        <button type="button"
                            onClick={(e) => { e.stopPropagation(); setStatusOpen(v => !v); }}
                            className={`flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-bold border bg-white/[0.03] hover:bg-white/[0.06] border-white/10 transition-colors cursor-pointer ${STATUS_META[status].color}`}
                            title="Cập nhật status"
                        >
                            <StatusIcon className="w-3 h-3" />
                            <span className="uppercase tracking-wider">{STATUS_META[status].label}</span>
                        </button>
                        {statusOpen && (
                            <div className="absolute top-full right-0 mt-1 z-50 bg-surface border border-white/10 rounded-xl shadow-2xl p-1 space-y-0.5 w-36"
                                onClick={(e) => e.stopPropagation()}>
                                {STATUS_ORDER.map(s => {
                                    const m = STATUS_META[s];
                                    const I = m.icon;
                                    return (
                                        <button key={s} type="button"
                                            onClick={(e) => { e.stopPropagation(); onStatusChange(jd.jd_key, s); setStatusOpen(false); }}
                                            className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-[11px] font-semibold text-left hover:bg-white/5 transition-colors cursor-pointer ${s === status ? 'bg-white/[0.05]' : ''}`}
                                        >
                                            <I className={`w-3 h-3 ${m.color}`} />
                                            <span className={m.color}>{m.label}</span>
                                            {s === status && <CheckCircle2 className="w-3 h-3 text-emerald-400 ml-auto" />}
                                        </button>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Enriched Signals & Dim Breakdown */}
            <div className="flex flex-col gap-3 relative z-10">
                <div className="flex items-center gap-2 flex-wrap text-[11px]">
                    {sen && (
                        <span className="px-2.5 py-1 rounded-lg bg-surface border border-white/5 text-text-secondary font-medium flex items-center gap-1.5">
                            <GraduationCap className="w-3 h-3 text-text-muted" />{sen}
                        </span>
                    )}
                    {exp && (
                        <span className="px-2.5 py-1 rounded-lg bg-surface border border-white/5 text-text-secondary font-medium flex items-center gap-1.5">
                            <Briefcase className="w-3 h-3 text-text-muted" />{exp}
                        </span>
                    )}
                    {wm && (
                        <span className={[
                            'px-2.5 py-1 rounded-lg border font-bold flex items-center gap-1.5',
                            jd.work_mode_match ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-amber-500/10 border-amber-500/20 text-amber-400',
                        ].join(' ')}>{wm}</span>
                    )}
                    {!jd.location_match && jd.location && (
                        <span className="px-2.5 py-1 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 font-bold flex items-center gap-1.5">
                            <AlertTriangle className="w-3 h-3" />Khác địa điểm
                        </span>
                    )}
                </div>

                <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[10px] uppercase font-bold text-text-muted mr-1 flex items-center gap-1">
                        <Target className="w-3 h-3" /> Chi tiết:
                    </span>
                    <DimTag label="Required" score={jd.skill_required_coverage} />
                    {jd.skill_preferred_coverage > 0 && <DimTag label="Preferred" score={jd.skill_preferred_coverage} />}
                    <DimTag label="Exp fit" score={jd.exp_fit} />
                </div>

                {/* Matched + Missing skills inline (visual diff) */}
                {(jd.matched_skills.length > 0 || jd.missing_required.length > 0) && (
                    <div className="flex flex-wrap gap-1.5 pt-2 border-t border-white/5">
                        {jd.matched_skills.slice(0, 6).map(s => (
                            <span key={'m-' + s} className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                                ✓ {s}
                            </span>
                        ))}
                        {jd.missing_required.slice(0, 4).map(s => (
                            <span key={'x-' + s} className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-rose-500/10 text-rose-300 border border-rose-500/20">
                                ✗ {s}
                            </span>
                        ))}
                        {(jd.matched_skills.length > 6 || jd.missing_required.length > 4) && (
                            <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-white/5 text-text-muted border border-white/10">
                                +{Math.max(0, jd.matched_skills.length - 6) + Math.max(0, jd.missing_required.length - 4)}
                            </span>
                        )}
                    </div>
                )}
            </div>

            {/* Description summary */}
            {jd.description_summary && (
                <p className="text-[13px] text-text-secondary/90 leading-relaxed line-clamp-3 relative z-10 bg-black/10 p-3 rounded-xl border border-white/[0.03]">
                    {jd.description_summary}
                </p>
            )}

            {/* Bookmark quick action (when status=new) */}
            {!isSaved && status === 'new' && (
                <button type="button"
                    onClick={() => onStatusChange(jd.jd_key, 'saved')}
                    className="absolute bottom-3 right-3 flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-bold bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 hover:bg-indigo-500/20 cursor-pointer transition-all opacity-0 group-hover:opacity-100"
                >
                    <Bookmark className="w-3 h-3" />Lưu
                </button>
            )}
        </li>
    );
});


function OpportunityWindowInner({ userId }: Props) {
    // ── Filter state ───────────────────────────────────────────────
    const [days, setDays] = useState(30);
    const [sort, setSort] = useState<'match' | 'newest' | 'salary'>('match');
    const [minMatch, setMinMatch] = useState(0.4);
    const [workModes, setWorkModes] = useState<string[]>(['onsite', 'hybrid', 'remote']);
    const [locations, setLocations] = useState<string[]>(['HCM', 'HN', 'DN', 'Remote', 'Any']);
    const [statusFilter, setStatusFilter] = useState<JdStatus | 'all'>('all');
    const [page, setPage] = useState(1);

    // ── Dropdown state ─────────────────────────────────────────────
    const [locDropOpen, setLocDropOpen] = useState(false);
    const locDropRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleClick = (e: MouseEvent) => {
            if (locDropRef.current && !locDropRef.current.contains(e.target as Node)) setLocDropOpen(false);
        };
        document.addEventListener('mousedown', handleClick);
        return () => document.removeEventListener('mousedown', handleClick);
    }, []);

    // ── Data state ─────────────────────────────────────────────────
    const [data, setData] = useState<OpportunityWindowResponse | null>(null);
    const [statusStats, setStatusStats] = useState<Partial<Record<JdStatus, number>>>({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // ── Match score breakdown popup ────────────────────────────────
    const [breakdownJd, setBreakdownJd] = useState<OpportunityJD | null>(null);

    const fetch = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [oppsRes, statsRes] = await Promise.allSettled([
                cvHealthApi.getOpportunities(userId, { days, sort, minMatch, workModes, locations, limit: 30 }),
                cvHealthApi.getJdStatusStats(userId),
            ]);
            if (oppsRes.status === 'fulfilled') setData(oppsRes.value.data);
            else setError('Không tải được JD');
            if (statsRes.status === 'fulfilled') setStatusStats(statsRes.value.data.counts || {});
        } finally {
            setLoading(false);
        }
    }, [userId, days, sort, minMatch, workModes, locations]);

    useEffect(() => { fetch(); }, [fetch]);

    const handleStatusChange = useCallback(async (jdKey: string, status: JdStatus) => {
        // Optimistic update
        setData(prev => {
            if (!prev) return prev;
            return {
                ...prev,
                items: prev.items.map(j => j.jd_key === jdKey ? { ...j, status } : j),
            };
        });
        try {
            await cvHealthApi.updateJdStatus(userId, jdKey, status);
            const stats = await cvHealthApi.getJdStatusStats(userId);
            setStatusStats(stats.data.counts || {});
        } catch (e) {
            console.error('Failed to update JD status', e);
        }
    }, [userId]);

    const toggleWorkMode = (m: string) => {
        setWorkModes(prev => prev.includes(m) ? prev.filter(x => x !== m) : [...prev, m]);
    };

    const toggleLocation = (loc: string) => {
        setLocations(prev => prev.includes(loc) ? prev.filter(x => x !== loc) : [...prev, loc]);
    };

    const filteredItems = useMemo(() => {
        const items = data?.items ?? [];
        if (statusFilter === 'all') return items;
        return items.filter(j => (j.status || 'new') === statusFilter);
    }, [data, statusFilter]);

    const totalPages = Math.max(1, Math.ceil(filteredItems.length / PAGE_SIZE));
    const safePage = Math.min(page, totalPages);
    const paginatedItems = useMemo(
        () => filteredItems.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE),
        [filteredItems, safePage],
    );

    // Reset page when filters change
    useEffect(() => { setPage(1); }, [statusFilter, days, sort, minMatch, workModes, locations]);

    const aggregate = data?.aggregate;

    return (
        <Fragment>
        <Card className="bg-surface/80 border border-white/5 shadow-xl relative">
            {/* ── Header Title (Not Sticky) ────────────────── */}
            <div className="px-8 pt-8 pb-2">
                <div className="flex items-start justify-between gap-4">
                    <div>
                        <CardTitle className="font-outfit text-xl font-black flex items-center gap-2">
                            <Target className="w-5 h-5 text-accent-primary" />
                            Opportunity Window
                        </CardTitle>
                        <CardDescription className="text-xs mt-1">
                            JD trong {days} ngày qua phù hợp với CV của bạn — sort theo {SORT_OPTIONS.find(s => s.id === sort)?.label}
                        </CardDescription>
                    </div>
                    {aggregate && (
                        <div className="text-right shrink-0">
                            <div className="text-[10px] text-text-muted font-bold uppercase tracking-widest">Đã quét</div>
                            <div className="text-sm font-black text-text-primary tabular-nums">
                                <span className="text-emerald-400">{aggregate.total_passed}</span>
                                <span className="text-text-muted font-normal">/{aggregate.total_scanned}</span>
                                <span className="text-text-muted font-normal text-xs"> JD match</span>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* ── Filter Bar (Sticky) ──────────────────────── */}
            <div className="sticky top-0 z-40 bg-surface/95 backdrop-blur-xl border-b border-white/5 px-8 pb-4 pt-3 shadow-sm mt-[-1px]">
                <div className="flex flex-wrap items-center gap-2">
                    {/* Days */}
                    <div className="flex items-center gap-1 bg-black/20 p-1 rounded-full border border-white/5">
                        <Calendar className="w-3 h-3 text-text-muted ml-2" />
                        {DAYS_OPTIONS.map(d => (
                            <button key={d} type="button" onClick={() => setDays(d)}
                                className={`h-6 px-2.5 rounded-full text-[11px] font-bold transition-all ${days === d ? 'bg-accent-primary/20 text-accent-primary' : 'text-text-muted hover:text-text-primary'}`}
                            >{d}d</button>
                        ))}
                    </div>

                    {/* Sort */}
                    <div className="flex items-center gap-1 bg-black/20 p-1 rounded-full border border-white/5">
                        <SortAsc className="w-3 h-3 text-text-muted ml-2" />
                        {SORT_OPTIONS.map(s => (
                            <button key={s.id} type="button" onClick={() => setSort(s.id)}
                                className={`h-6 px-2.5 rounded-full text-[11px] font-bold transition-all ${sort === s.id ? 'bg-accent-primary/20 text-accent-primary' : 'text-text-muted hover:text-text-primary'}`}
                            >{s.label}</button>
                        ))}
                    </div>

                    {/* Work modes */}
                    <div className="flex items-center gap-1 bg-black/20 p-1 rounded-full border border-white/5">
                        <Briefcase className="w-3 h-3 text-text-muted ml-2" />
                        {WORK_MODE_OPTIONS.map(m => (
                            <button key={m.id} type="button" onClick={() => toggleWorkMode(m.id)}
                                className={`h-6 px-2.5 rounded-full text-[11px] font-bold transition-all ${workModes.includes(m.id) ? 'bg-indigo-500/25 text-indigo-200' : 'text-text-muted hover:text-text-primary'}`}
                            >{m.label}</button>
                        ))}
                    </div>

                    {/* Locations */}
                    <div className="relative" ref={locDropRef}>
                        <button type="button" onClick={() => setLocDropOpen(v => !v)}
                            className="flex items-center gap-1.5 h-8 px-3 rounded-full bg-black/20 border border-white/5 hover:bg-white/5 transition-all text-[11px] font-bold text-text-muted hover:text-text-primary">
                            <MapPin className="w-3 h-3" />
                            {locations.length === LOCATIONS.length ? 'Mọi địa điểm' : `${locations.length} địa điểm`}
                            <ChevronDown className={`w-3 h-3 transition-transform ${locDropOpen ? 'rotate-180' : ''}`} />
                        </button>
                        {locDropOpen && (
                            <div className="absolute top-full left-0 mt-1 z-50 w-40 bg-surface border border-white/10 rounded-xl shadow-2xl overflow-hidden py-1">
                                {LOCATIONS.map(l => {
                                    const active = locations.includes(l.id);
                                    return (
                                        <button key={l.id} type="button" onClick={() => toggleLocation(l.id)}
                                            className={`w-full flex items-center justify-between px-3 py-1.5 text-[11px] font-bold transition-colors ${active ? 'text-accent-primary bg-accent-primary/10' : 'text-text-secondary hover:bg-white/5 hover:text-text-primary'}`}>
                                            {l.label}
                                            {active && <CheckCircle2 className="w-3 h-3" />}
                                        </button>
                                    );
                                })}
                            </div>
                        )}
                    </div>

                    {/* Min match slider */}
                    <div className="flex items-center gap-2 bg-black/20 px-3 h-8 rounded-full border border-white/5">
                        <Filter className="w-3 h-3 text-text-muted" />
                        <span className="text-[11px] text-text-muted font-bold">≥</span>
                        <input
                            type="range" min={20} max={80} step={5}
                            value={Math.round(minMatch * 100)}
                            onChange={e => setMinMatch(Number(e.target.value) / 100)}
                            className="w-20 accent-accent-primary"
                        />
                        <span className="text-[11px] font-black text-accent-primary tabular-nums">{Math.round(minMatch * 100)}%</span>
                    </div>
                </div>

                {/* ── Status filter tabs ────────────────── */}
                <div className="mt-3 flex items-center gap-1 flex-wrap">
                    {(['all', ...STATUS_ORDER] as const).map(s => {
                        const count = s === 'all'
                            ? (data?.items.length ?? 0)
                            : (statusStats[s] ?? 0);
                        const isActive = statusFilter === s;
                        if (s !== 'all' && count === 0 && !isActive) return null;
                        const label = s === 'all' ? 'Tất cả' : STATUS_META[s].label;
                        return (
                            <button key={s} type="button" onClick={() => setStatusFilter(s)}
                                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all ${isActive ? 'bg-accent-primary/15 text-accent-primary border border-accent-primary/30' : 'bg-white/[0.02] text-text-muted hover:text-text-primary border border-white/5'}`}
                            >
                                {label}
                                <span className={`text-[9px] tabular-nums px-1 rounded ${isActive ? 'bg-accent-primary/20' : 'bg-white/5'}`}>{count}</span>
                            </button>
                        );
                    })}
                </div>
            </div>


            <CardContent className="pt-5">
                {/* ── Top missing skills insight ─────────────── */}
                {aggregate && aggregate.top_missing_skills.length > 0 && (
                    <div className="mb-5 p-4 rounded-2xl bg-gradient-to-br from-amber-500/[0.06] to-amber-500/[0.02] border border-amber-500/15">
                        <div className="flex items-center gap-2 mb-2.5">
                            <Sparkles className="w-4 h-4 text-amber-400" />
                            <h4 className="text-[11px] font-black uppercase tracking-widest text-amber-400">
                                Skill xuất hiện nhiều nhất trong các JD bạn đang thiếu
                            </h4>
                        </div>
                        <p className="text-[11px] text-text-secondary/80 mb-3 leading-relaxed">
                            Học ưu tiên các skill này sẽ mở khoá nhiều JD nhất.
                        </p>
                        <div className="flex flex-wrap gap-2">
                            {aggregate.top_missing_skills.map(s => (
                                <div key={s.skill} className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/[0.03] border border-white/[0.08]">
                                    <span className="text-[12px] font-bold text-text-primary">{s.skill}</span>
                                    <span className="text-[10px] tabular-nums text-amber-400 font-black">
                                        {s.count} JD <span className="opacity-60">({s.pct.toFixed(0)}%)</span>
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* ── Body ───────────────────────────────────── */}
                {error ? (
                    <div className="h-24 flex items-center justify-center text-rose-400 text-sm">{error}</div>
                ) : !data && loading ? (
                    <ListSkeleton rows={3} />
                ) : !data && !loading ? (
                    <div className="h-24 flex items-center justify-center text-text-muted text-sm">Chưa có dữ liệu</div>
                ) : filteredItems.length === 0 ? (
                    <div className={`py-12 flex flex-col items-center gap-3 text-center transition-opacity duration-300 relative ${loading ? 'opacity-50 pointer-events-none' : 'opacity-100'}`}>
                        {loading && (
                            <div className="absolute inset-0 flex items-center justify-center z-10">
                                <Loader2 className="w-8 h-8 text-accent-primary animate-spin" />
                            </div>
                        )}
                        <Hourglass className="w-8 h-8 text-text-muted/60" />
                        <div className="text-sm text-text-secondary">
                            {statusFilter !== 'all'
                                ? `Chưa có JD nào ở trạng thái "${STATUS_META[statusFilter as JdStatus].label}"`
                                : 'Không có JD nào match với filter hiện tại'}
                        </div>
                        {statusFilter !== 'all' ? (
                            <button type="button" onClick={() => setStatusFilter('all')}
                                className="text-[11px] font-bold text-accent-primary hover:underline cursor-pointer">
                                Hiện tất cả →
                            </button>
                        ) : (
                            <div className="text-[11px] text-text-muted flex flex-col gap-1">
                                <span>Thử: nới <strong className="text-text-primary">{days}d → 90d</strong>, giảm <strong className="text-text-primary">min match {Math.round(minMatch * 100)}% → 30%</strong>,</span>
                                <span>hoặc bật thêm <strong className="text-text-primary">Remote/Hybrid</strong> nếu chưa.</span>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className={`transition-opacity duration-300 relative min-h-[200px] ${loading ? 'opacity-50 pointer-events-none' : 'opacity-100'}`}>
                        {loading && (
                            <div className="absolute inset-0 top-10 flex items-start justify-center z-10">
                                <Loader2 className="w-8 h-8 text-accent-primary animate-spin" />
                            </div>
                        )}
                        <ul className="space-y-4">
                            {paginatedItems.map(jd => (
                                <OpportunityCard key={jd.jd_key} jd={jd}
                                    onStatusChange={handleStatusChange}
                                    onOpenBreakdown={setBreakdownJd}
                                />
                            ))}
                        </ul>

                        {/* ── Pagination ─────────────────────────── */}
                        {totalPages > 1 && (
                            <div className="mt-5 flex items-center justify-between border-t border-white/5 pt-4">
                                <span className="text-[11px] text-text-muted tabular-nums">
                                    {(safePage - 1) * PAGE_SIZE + 1}–{Math.min(safePage * PAGE_SIZE, filteredItems.length)} / {filteredItems.length} JD
                                </span>
                                <div className="flex items-center gap-1">
                                    <button type="button" disabled={safePage <= 1}
                                        onClick={() => setPage(p => Math.max(1, p - 1))}
                                        className="h-8 w-8 flex items-center justify-center rounded-lg border border-white/10 bg-white/[0.03] text-text-muted hover:text-text-primary hover:bg-white/[0.06] disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer">
                                        <ChevronLeft className="w-4 h-4" />
                                    </button>
                                    {Array.from({ length: totalPages }, (_, i) => i + 1).map(p => (
                                        <button key={p} type="button" onClick={() => setPage(p)}
                                            className={`h-8 min-w-[2rem] px-1 rounded-lg text-[11px] font-bold tabular-nums transition-colors cursor-pointer ${p === safePage ? 'bg-accent-primary/20 text-accent-primary border border-accent-primary/30' : 'text-text-muted hover:text-text-primary hover:bg-white/[0.04]'}`}>
                                            {p}
                                        </button>
                                    ))}
                                    <button type="button" disabled={safePage >= totalPages}
                                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                        className="h-8 w-8 flex items-center justify-center rounded-lg border border-white/10 bg-white/[0.03] text-text-muted hover:text-text-primary hover:bg-white/[0.06] disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer">
                                        <ChevronRight className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </CardContent>
        </Card>

        {/* ── Match score breakdown popup ───────────────────────── */}
        <Dialog open={!!breakdownJd} onOpenChange={(open) => { if (!open) setBreakdownJd(null); }}>
            <DialogContent className="max-w-lg p-0 border-white/10 bg-surface" onClick={(e: React.MouseEvent) => e.stopPropagation()}>
                {breakdownJd && (
                    <>
                        <button type="button" onClick={() => setBreakdownJd(null)}
                            className="absolute right-5 top-5 z-20 rounded-full p-1.5 bg-black/30 backdrop-blur-md border border-white/10 text-text-muted hover:text-text-primary cursor-pointer">
                            <X className="w-4 h-4" />
                        </button>
                        <div className="relative pt-7 pb-6 px-6 border-b border-white/5"
                            style={{ background: `radial-gradient(circle at 20% 0%, ${breakdownJd.match_score >= 0.8 ? '#10b981' : breakdownJd.match_score >= 0.6 ? '#6366f1' : '#f59e0b'}28 0%, transparent 55%)` }}>
                            <DialogHeader>
                                <DialogTitle className="text-lg font-extrabold flex items-center gap-3 pr-8">
                                    <span className="line-clamp-2">{breakdownJd.title}</span>
                                    <span className="text-3xl font-black tabular-nums shrink-0" style={{ color: breakdownJd.match_score >= 0.8 ? '#10b981' : breakdownJd.match_score >= 0.6 ? '#6366f1' : '#f59e0b' }}>
                                        {(breakdownJd.match_score * 100).toFixed(0)}
                                    </span>
                                </DialogTitle>
                                <DialogDescription className="text-text-secondary text-xs mt-1">
                                    {breakdownJd.company} · {breakdownJd.location}
                                </DialogDescription>
                            </DialogHeader>
                        </div>
                        <div className="px-6 py-5 space-y-4">
                            <div>
                                <h4 className="text-[10px] font-black uppercase tracking-widest text-text-muted mb-2 flex items-center gap-1.5">
                                    <Info className="w-3 h-3" /> Cách tính
                                </h4>
                                <div className="rounded-xl bg-black/30 border border-white/10 px-4 py-3 font-mono text-[12px] text-emerald-300/95 leading-relaxed">
                                    match = Σ (score × weight) cho 5 chiều dưới đây
                                </div>
                            </div>
                            <div className="space-y-2">
                                {[
                                    { label: 'Required skills', score: breakdownJd.skill_required_coverage, weight: 0.55, hint: `Match ${breakdownJd.matched_skills.length}/${breakdownJd.matched_skills.length + breakdownJd.missing_required.length} skill bắt buộc` },
                                    { label: 'Preferred skills', score: breakdownJd.skill_preferred_coverage, weight: 0.15, hint: 'Skill nice-to-have' },
                                    { label: 'Exp fit', score: breakdownJd.exp_fit, weight: 0.20, hint: 'Khoảng năm KN khớp JD' },
                                    { label: 'Location', score: breakdownJd.location_match ? 1 : 0, weight: 0.05, hint: breakdownJd.location_match ? '✓ Cùng địa điểm' : '✗ Khác địa điểm' },
                                    { label: 'Work mode', score: breakdownJd.work_mode_match ? 1 : 0, weight: 0.05, hint: breakdownJd.work_mode_match ? '✓ Khớp work mode' : '✗ Khác work mode' },
                                ].map(r => {
                                    const tone = scoreToneClass(r.score);
                                    return (
                                        <div key={r.label} className="flex items-center gap-3 p-2.5 rounded-xl bg-white/[0.02] border border-white/[0.05]">
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-baseline gap-2">
                                                    <span className="text-[13px] font-bold text-text-primary">{r.label}</span>
                                                    <span className="text-[9px] font-mono text-text-muted">×{r.weight.toFixed(2)}</span>
                                                </div>
                                                <div className="text-[10px] text-text-muted/80 mt-0.5">{r.hint}</div>
                                            </div>
                                            <div className={`px-2 py-0.5 rounded text-[11px] font-bold border tabular-nums ${tone}`}>
                                                {(r.score * 100).toFixed(0)}%
                                            </div>
                                            <div className="text-[10px] text-text-muted/70 w-12 text-right tabular-nums font-mono">
                                                +{(r.score * r.weight * 100).toFixed(1)}đ
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                            {breakdownJd.blockers.length > 0 && (
                                <div className="rounded-xl bg-rose-500/[0.06] border border-rose-500/20 p-3 space-y-1.5">
                                    <h4 className="text-[10px] font-black uppercase tracking-widest text-rose-400 mb-1">Blockers</h4>
                                    {breakdownJd.blockers.map((b, i) => (
                                        <div key={i} className="text-[12px] text-rose-200/90 flex items-start gap-2">
                                            <AlertTriangle className="w-3 h-3 shrink-0 mt-0.5" />{b}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </>
                )}
            </DialogContent>
        </Dialog>
        </Fragment>
    );
}

export default memo(OpportunityWindowInner);
