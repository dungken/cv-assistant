import { memo, useState } from 'react';
import { ChevronRight } from 'lucide-react';
import { cn } from '../../../lib/utils';

const TYPE_DOT: Record<string, string> = {
    SKILL:     'bg-sky-400',
    TECH:      'bg-sky-400',
    ORG:       'bg-violet-400',
    JOB_TITLE: 'bg-amber-400',
    DATE:      'bg-slate-400',
    DEGREE:    'bg-emerald-400',
    MAJOR:     'bg-teal-400',
    CERT:      'bg-lime-400',
    PROJECT:   'bg-orange-400',
    LOC:       'bg-rose-400',
    PER:       'bg-pink-400',
    EMAIL:     'bg-cyan-400',
    PHONE:     'bg-cyan-400',
};

interface Entity { type: string; text: string }
interface SectionBlock { anchor?: string; description?: string; entities?: Entity[] }
interface Props { parsed: any; source: 'upload' | 'select' }

function Chip({ ent }: { ent: Entity }) {
    const dot = TYPE_DOT[ent.type] ?? 'bg-white/30';
    return (
        <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-base text-text-primary whitespace-nowrap">
            <span className={cn('w-2 h-2 rounded-full shrink-0', dot)} />
            {ent.text}
        </span>
    );
}

function Section({ title, blocks, defaultOpen = true }: {
    title: string; blocks: SectionBlock[]; defaultOpen?: boolean;
}) {
    const [open, setOpen] = useState(defaultOpen);
    if (!blocks || blocks.length === 0) return null;
    return (
        <div>
            <button
                type="button"
                onClick={() => setOpen(v => !v)}
                className="w-full flex items-center gap-2 py-3 text-left"
            >
                <ChevronRight className={cn('w-4 h-4 text-text-muted transition-transform duration-150 shrink-0', open && 'rotate-90')} />
                <span className="text-sm font-bold text-text-primary uppercase tracking-wider">{title}</span>
                <span className="text-sm text-text-muted ml-1">({blocks.length})</span>
            </button>
            {open && (
                <div className="ml-6 space-y-4 pb-2">
                    {blocks.map((b, i) => (
                        <div key={i}>
                            {b.anchor && (
                                <div className="text-base font-semibold text-text-primary mb-1">{b.anchor}</div>
                            )}
                            {b.description && (
                                <div className="text-base text-text-secondary leading-relaxed mb-2 whitespace-pre-line">
                                    {b.description}
                                </div>
                            )}
                            {b.entities && b.entities.length > 0 && (
                                <div className="flex flex-wrap gap-2">
                                    {b.entities.map((e, j) => <Chip key={j} ent={e} />)}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function CVPreviewPanelInner({ parsed, source }: Props) {
    if (!parsed || typeof parsed !== 'object') return null;
    const obj = parsed as Record<string, any>;

    const summary    = typeof obj.summary === 'string' ? obj.summary.trim() : '';
    const experience: SectionBlock[] = Array.isArray(obj.experience)      ? obj.experience      : [];
    const projects:   SectionBlock[] = Array.isArray(obj.projects)         ? obj.projects         : [];
    const education:  SectionBlock[] = Array.isArray(obj.education)        ? obj.education        : [];
    const certs:      SectionBlock[] = Array.isArray(obj.certifications)   ? obj.certifications   : [];
    const languages:  string[]       = Array.isArray(obj.languages)        ? obj.languages        : [];
    const meta = obj.metadata ?? {};

    const skillGroups: Record<string, string[]> = {};
    const sf = obj.skills;
    if (Array.isArray(sf)) {
        skillGroups['Skills'] = sf.filter((s): s is string => typeof s === 'string');
    } else if (sf && typeof sf === 'object') {
        for (const [cat, arr] of Object.entries(sf)) {
            if (Array.isArray(arr)) skillGroups[cat] = arr.filter((s): s is string => typeof s === 'string');
        }
    }

    const counts: Record<string, number> = {};
    for (const blocks of [experience, projects, education, certs]) {
        for (const b of blocks) for (const e of b.entities ?? []) {
            if (e?.type) counts[e.type] = (counts[e.type] ?? 0) + 1;
        }
    }
    const totalEnt = Object.values(counts).reduce((a, b) => a + b, 0);

    return (
        <div className="space-y-0">
            {/* Meta bar */}
            <div className="flex items-center gap-4 pb-3 border-b border-white/8 flex-wrap">
                <span className="text-sm font-semibold text-text-secondary">
                    {source === 'upload' ? 'Upload · NER' : 'Saved CV · NER'}
                </span>
                {meta.pages      && <span className="text-sm text-text-muted">{meta.pages} trang</span>}
                {meta.parse_time_ms !== undefined && <span className="text-sm text-text-muted">{meta.parse_time_ms}ms</span>}
                {totalEnt > 0 && (
                    <div className="flex items-center gap-3 ml-auto flex-wrap">
                        {Object.entries(counts).sort((a, b) => b[1] - a[1]).map(([type, n]) => (
                            <span key={type} className="inline-flex items-center gap-1.5 text-sm text-text-muted">
                                <span className={cn('w-2 h-2 rounded-full shrink-0', TYPE_DOT[type] ?? 'bg-white/30')} />
                                {type} <span className="text-text-secondary font-semibold">{n}</span>
                            </span>
                        ))}
                    </div>
                )}
            </div>

            {/* Summary */}
            {summary && (
                <div className="py-3 border-b border-white/8">
                    <div className="text-xs font-bold uppercase tracking-widest text-text-muted mb-2">Summary</div>
                    <p className="text-base text-text-secondary leading-relaxed">{summary}</p>
                </div>
            )}

            {/* Skills */}
            {Object.entries(skillGroups).map(([cat, arr]) => arr.length > 0 && (
                <div key={cat} className="py-3 border-b border-white/8">
                    <div className="text-xs font-bold uppercase tracking-widest text-text-muted mb-2">
                        {cat} <span className="font-normal opacity-60">({arr.length})</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {arr.map((s, i) => (
                            <span key={i} className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-base text-text-primary">
                                {s}
                            </span>
                        ))}
                    </div>
                </div>
            ))}

            {/* Sections */}
            <div className="divide-y divide-white/8">
                <Section title="Kinh nghiệm" blocks={experience} />
                <Section title="Dự án"       blocks={projects}   defaultOpen={false} />
                <Section title="Học vấn"     blocks={education}  />
                <Section title="Chứng chỉ"   blocks={certs}      defaultOpen={false} />
            </div>

            {/* Languages */}
            {languages.length > 0 && (
                <div className="pt-3 flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-bold uppercase tracking-widest text-text-muted">Ngôn ngữ</span>
                    {languages.map((l, i) => (
                        <span key={i} className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-base text-text-primary">{l}</span>
                    ))}
                </div>
            )}
        </div>
    );
}

export default memo(CVPreviewPanelInner);
