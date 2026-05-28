import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AxiosError } from 'axios';
import { UploadCloud, Loader2, ChevronDown, FileText, Eye } from 'lucide-react';
import { cvDocumentApi, cvHealthApi, nerApi, type CvDocument } from '../../../services/api';
import CVPreviewPanel from './CVPreviewPanel';

interface Props {
    userId: string;
    onLinked: () => void;
    onEmpty?: (isEmpty: boolean) => void;
}

const ROLES: Array<{ id: string; label: string }> = [
    { id: 'backend', label: 'Backend' },
    { id: 'frontend', label: 'Frontend' },
    { id: 'data', label: 'Data' },
    { id: 'devops', label: 'DevOps' },
    { id: 'ai_engineer', label: 'AI Eng' },
    { id: 'fullstack', label: 'Fullstack' },
    { id: 'mobile', label: 'Mobile' },
];

const SENIORITIES = [
    { id: 'junior', label: 'Junior' },
    { id: 'mid', label: 'Mid' },
    { id: 'senior', label: 'Senior' },
    { id: 'lead', label: 'Lead' },
];

const LOCATIONS = [
    { id: 'HCM', label: 'HCM' },
    { id: 'HN', label: 'Hà Nội' },
    { id: 'DN', label: 'Đà Nẵng' },
    { id: 'Remote', label: 'Remote' },
    { id: 'Any', label: 'Bất kỳ' },
];

const WORK_MODES = [
    { id: 'onsite', label: 'Onsite' },
    { id: 'hybrid', label: 'Hybrid' },
    { id: 'remote', label: 'Remote' },
];

interface NerEntity { text: string; type: string }
interface NerBlock { entities?: NerEntity[] }

function extractProfileExtras(parsed: unknown) {
    const out = {
        degree: undefined as string | undefined,
        major: undefined as string | undefined,
        past_job_titles: [] as string[],
        num_projects: 0,
        project_skill_counts: [] as number[],
        achievement_text: '',
        language_text: '',
        has_contact: true, has_summary: false, has_education: false,
        has_experience: false, has_skills: false, has_projects: false,
    };
    if (!parsed || typeof parsed !== 'object') return out;
    const obj = parsed as Record<string, unknown>;
    out.has_summary = typeof obj.summary === 'string' && obj.summary.trim().length > 0;
    const exp = obj.experience as NerBlock[] | undefined;
    out.has_experience = Array.isArray(exp) && exp.length > 0;
    const edu = obj.education as NerBlock[] | undefined;
    out.has_education = Array.isArray(edu) && edu.length > 0;
    const projects = obj.projects as NerBlock[] | undefined;
    out.has_projects = Array.isArray(projects) && projects.length > 0;
    const skillsField = obj.skills;
    out.has_skills = (Array.isArray(skillsField) && skillsField.length > 0)
        || (typeof skillsField === 'object' && skillsField !== null && Object.keys(skillsField).length > 0);
    if (Array.isArray(edu)) {
        for (const block of edu) {
            for (const e of block.entities ?? []) {
                if (e?.type === 'DEGREE' && !out.degree) out.degree = e.text;
                if (e?.type === 'MAJOR' && !out.major) out.major = e.text;
            }
        }
    }
    if (Array.isArray(exp)) {
        const titles = new Set<string>();
        for (const block of exp) {
            for (const e of block.entities ?? []) {
                if (e?.type === 'JOB_TITLE' && typeof e.text === 'string') titles.add(e.text.trim());
            }
        }
        out.past_job_titles = Array.from(titles);
    }
    if (Array.isArray(projects)) {
        out.num_projects = projects.length;
        out.project_skill_counts = projects.map(p =>
            (p.entities ?? []).filter(e => e?.type === 'SKILL' || e?.type === 'TECH').length,
        );
    }
    const certs = obj.certifications as Array<{ description?: string; anchor?: string }> | undefined;
    const achievementParts: string[] = [];
    if (Array.isArray(certs)) {
        for (const c of certs) {
            if (c.anchor) achievementParts.push(c.anchor);
            if (c.description) achievementParts.push(c.description);
        }
    }
    out.achievement_text = achievementParts.join(' ');
    const langs = obj.languages;
    if (Array.isArray(langs)) {
        out.language_text = langs.join(', ');
    } else if (skillsField && typeof skillsField === 'object') {
        const s = skillsField as Record<string, unknown>;
        const b = s.languages ?? s.language ?? s.Languages;
        if (Array.isArray(b)) out.language_text = b.join(', ');
    }
    return out;
}

function extractSkills(parsed: unknown): string[] {
    if (!parsed || typeof parsed !== 'object') return [];
    const obj = parsed as Record<string, unknown>;
    const out = new Set<string>();
    const push = (s: unknown) => { if (typeof s === 'string' && s.trim()) out.add(s.trim()); };
    const skillsField = obj.skills;
    if (Array.isArray(skillsField)) skillsField.forEach(push);
    else if (skillsField && typeof skillsField === 'object')
        Object.values(skillsField as Record<string, unknown>).forEach(arr => { if (Array.isArray(arr)) arr.forEach(push); });
    for (const key of ['experience', 'projects'] as const) {
        const blocks = obj[key];
        if (!Array.isArray(blocks)) continue;
        for (const b of blocks as NerBlock[]) {
            for (const e of b.entities ?? []) {
                if (e && (e.type === 'SKILL' || e.type === 'TECH')) push(e.text);
            }
        }
    }
    return Array.from(out);
}

export default function CVPicker({ userId, onLinked, onEmpty }: Props) {
    const [docs, setDocs] = useState<CvDocument[] | null>(null);
    const [loadingList, setLoadingList] = useState(false);
    const [listError, setListError] = useState<string | null>(null);

    const [selectedId, setSelectedId] = useState<number | null>(null);
    const [role, setRole] = useState('backend');
    const [seniority, setSeniority] = useState('junior');
    const [yearsExp, setYearsExp] = useState(1);
    const [location, setLocation] = useState('HCM');
    const [workModes, setWorkModes] = useState(['onsite', 'hybrid', 'remote']);
    const [linking, setLinking] = useState(false);
    const [linkError, setLinkError] = useState<string | null>(null);

    const navigate = useNavigate();

    // CV dropdown
    const [cvDropOpen, setCvDropOpen] = useState(false);
    const cvDropRef = useRef<HTMLDivElement>(null);

    // Loc dropdown
    const [locDropOpen, setLocDropOpen] = useState(false);
    const locDropRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleClick = (e: MouseEvent) => {
            if (cvDropRef.current && !cvDropRef.current.contains(e.target as Node)) setCvDropOpen(false);
            if (locDropRef.current && !locDropRef.current.contains(e.target as Node)) setLocDropOpen(false);
        };
        document.addEventListener('mousedown', handleClick);
        return () => document.removeEventListener('mousedown', handleClick);
    }, []);

    // Load CV list on mount
    useEffect(() => {
        let cancelled = false;
        setLoadingList(true);
        cvDocumentApi.list()
            .then(res => {
                if (cancelled) return;
                setDocs(res.data);
                if (res.data.length > 0) setSelectedId(res.data[0].id);
                if (onEmpty) onEmpty(res.data.length === 0);
            })
            .catch(err => {
                if (cancelled) return;
                setListError(err instanceof AxiosError ? err.message : 'Không tải được danh sách CV.');
            })
            .finally(() => { if (!cancelled) setLoadingList(false); });
        return () => { cancelled = true; };
    }, []);

    function toggleWorkMode(mode: string) {
        setWorkModes(prev => prev.includes(mode) ? prev.filter(m => m !== mode) : [...prev, mode]);
    }

    async function handleUseCv() {
        if (!selectedId) return;
        setLinking(true);
        setLinkError(null);
        try {
            const docRes = await cvDocumentApi.getById(selectedId);
            const latestVer = docRes.data.versions.slice().sort((a, b) => b.versionNumber - a.versionNumber)[0];
            if (!latestVer) throw new Error('CV không có version nào.');
            const verRes = await cvDocumentApi.getVersion(docRes.data.id, latestVer.id);
            const parsed = JSON.parse(verRes.data.dataJson);
            const skills = extractSkills(parsed);
            const extras = extractProfileExtras(parsed);
            if (skills.length === 0) throw new Error('CV này chưa có kỹ năng nào được trích xuất.');
            const currentYear = new Date().getFullYear();
            const yearsValue = Number.isNaN(yearsExp) ? null : Math.max(0, yearsExp);
            await cvHealthApi.upsertCv(userId, role, skills.map(name => ({ name, last_used_year: currentYear })), {
                yearsExperience: yearsValue, preferredLocation: location.trim() || null,
                preferredWorkModes: workModes.length > 0 ? workModes : null,
                seniority, pastJobTitles: extras.past_job_titles,
                numProjects: extras.num_projects, projectSkillCounts: extras.project_skill_counts,
                degree: extras.degree || null, major: extras.major || null,
                achievementText: extras.achievement_text || null, languageText: extras.language_text || null,
                hasContact: extras.has_contact, hasSummary: extras.has_summary,
                hasEducation: extras.has_education, hasExperience: extras.has_experience,
                hasSkills: extras.has_skills, hasProjects: extras.has_projects,
            });
            onLinked();
        } catch (err) {
            setLinkError(
                err instanceof AxiosError
                    ? (err.response?.data as { detail?: string } | undefined)?.detail || err.message
                    : err instanceof Error ? err.message : 'Không liên kết được CV.',
            );
        } finally {
            setLinking(false);
        }
    }

    const selectedDoc = docs?.find(d => d.id === selectedId);

    return (
        <>
        <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm overflow-visible">
            <div className="px-5 py-4 flex items-start gap-4">
            {/* Filter groups — wrap freely */}
            <div className="flex flex-wrap gap-x-6 gap-y-4 flex-1 min-w-0">

                {/* CV */}
                <div className="flex flex-col gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted">CV</span>
                    <div className="relative" ref={cvDropRef}>
                        <button
                            type="button"
                            onClick={() => setCvDropOpen(v => !v)}
                            className="flex items-center gap-2 h-8 pl-3 pr-2.5 rounded-xl bg-white/6 border border-white/10 hover:border-white/20 hover:bg-white/8 transition-all text-sm font-semibold min-w-[160px] max-w-[220px]"
                        >
                            <FileText className="w-3.5 h-3.5 text-accent-primary shrink-0" />
                            <span className="truncate flex-1 text-left text-text-primary">
                                {loadingList ? 'Đang tải…' : selectedDoc ? selectedDoc.name : 'Chọn CV'}
                            </span>
                            <ChevronDown className={`w-3.5 h-3.5 text-text-muted shrink-0 transition-transform duration-150 ${cvDropOpen ? 'rotate-180' : ''}`} />
                        </button>

                        {cvDropOpen && (
                            <div className="absolute top-full left-0 mt-2 z-50 w-72 bg-surface border border-white/10 rounded-2xl shadow-2xl shadow-black/50 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
                                <div className="p-2 space-y-0.5 max-h-52 overflow-y-auto">
                                    {listError ? (
                                        <div className="p-3 text-sm text-rose-400">{listError}</div>
                                    ) : !docs || docs.length === 0 ? (
                                        <div className="p-3 text-sm text-text-secondary text-center">Chưa có CV. Upload bên dưới.</div>
                                    ) : docs.map(d => (
                                        <button key={d.id} type="button"
                                            onClick={() => { setSelectedId(d.id); setCvDropOpen(false); }}
                                            className={`w-full flex items-center justify-between gap-2 px-3 py-2.5 rounded-xl text-left transition-colors ${selectedId === d.id ? 'bg-accent-primary/12 text-accent-primary' : 'hover:bg-white/5 text-text-primary'}`}
                                        >
                                            <div className="min-w-0 flex-1">
                                                <div className="text-sm font-semibold truncate">{d.name}</div>
                                                <div className="text-xs text-text-muted mt-0.5">v{d.currentVersion} · {new Date(d.updatedAt).toLocaleDateString('vi-VN')}</div>
                                            </div>
                                            {selectedId === d.id && (
                                                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-md bg-accent-primary/20 text-accent-primary shrink-0">Active</span>
                                            )}
                                        </button>
                                    ))}
                                </div>
                                <div className="border-t border-white/5 p-2">
                                    <button type="button"
                                        onClick={() => navigate('/cv-upload')}
                                        className="w-full flex items-center justify-center gap-2.5 px-3 py-2.5 rounded-xl text-sm transition-all border border-dashed border-white/10 hover:border-accent-primary/30 hover:bg-accent-primary/5 cursor-pointer"
                                    >
                                        <UploadCloud className="w-3.5 h-3.5 text-accent-primary shrink-0" />
                                        <span className="text-text-primary text-xs font-bold uppercase tracking-wider">Upload CV mới & Review</span>
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Role */}
                <div className="flex flex-col gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted">Role</span>
                    <div className="flex items-center flex-wrap gap-1">
                        {ROLES.map(r => (
                            <button key={r.id} type="button" onClick={() => setRole(r.id)}
                                className={`h-8 px-3 rounded-xl text-sm font-semibold transition-all ${
                                    r.id === role
                                        ? 'bg-white/10 text-text-primary'
                                        : 'text-text-muted hover:text-text-secondary hover:bg-white/5'
                                }`}>
                                {r.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Level */}
                <div className="flex flex-col gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted">Level</span>
                    <div className="flex items-center gap-1 p-1 rounded-xl bg-white/5 border border-white/8">
                        {SENIORITIES.map(s => (
                            <button key={s.id} type="button" onClick={() => setSeniority(s.id)}
                                className={`h-6 px-3.5 rounded-lg text-sm font-semibold transition-all ${
                                    s.id === seniority
                                        ? 'bg-white/12 text-text-primary shadow-sm'
                                        : 'text-text-muted hover:text-text-secondary'
                                }`}>
                                {s.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Mode */}
                <div className="flex flex-col gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted">Mode</span>
                    <div className="flex items-center gap-1">
                        {WORK_MODES.map(m => (
                            <button key={m.id} type="button" onClick={() => toggleWorkMode(m.id)}
                                className={`h-8 px-3 rounded-xl text-sm font-semibold transition-all ${
                                    workModes.includes(m.id)
                                        ? 'bg-white/10 text-text-primary'
                                        : 'text-text-muted hover:text-text-secondary hover:bg-white/5'
                                }`}>
                                {m.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Filters */}
                <div className="flex flex-col gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted">Filters</span>
                    <div className="flex items-center gap-2">
                        {/* YOE — custom stepper, no browser spinner */}
                        <div className="flex items-center gap-2 h-8 px-3 rounded-xl bg-white/5 border border-white/8">
                            <span className="text-xs text-text-muted font-bold">YOE</span>
                            <input
                                type="number" min={0} max={40} step={1} value={yearsExp}
                                onChange={e => setYearsExp(Number(e.target.value))}
                                className="w-8 bg-transparent text-sm text-text-primary text-center focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                            />
                            <div className="flex flex-col -gap-0.5">
                                <button type="button" onClick={() => setYearsExp(v => Math.min(40, v + 1))}
                                    className="w-4 h-3.5 flex items-center justify-center text-text-muted hover:text-text-primary transition-colors leading-none text-[10px]">▲</button>
                                <button type="button" onClick={() => setYearsExp(v => Math.max(0, v - 1))}
                                    className="w-4 h-3.5 flex items-center justify-center text-text-muted hover:text-text-primary transition-colors leading-none text-[10px]">▼</button>
                            </div>
                        </div>
                        {/* Loc — custom dropdown */}
                        <div className="relative" ref={locDropRef}>
                            <button
                                type="button"
                                onClick={() => setLocDropOpen(v => !v)}
                                className="flex items-center gap-1.5 h-8 px-3 rounded-xl bg-white/5 border border-white/8 hover:border-white/20 hover:bg-white/8 transition-all"
                            >
                                <span className="text-xs text-text-muted font-bold">Loc</span>
                                <span className="text-sm text-text-primary font-semibold">
                                    {LOCATIONS.find(l => l.id === location)?.label ?? location}
                                </span>
                                <ChevronDown className={`w-3 h-3 text-text-muted transition-transform duration-150 ${locDropOpen ? 'rotate-180' : ''}`} />
                            </button>
                            {locDropOpen && (
                                <div className="absolute top-full left-0 mt-2 z-50 w-36 bg-surface border border-white/10 rounded-xl shadow-2xl shadow-black/50 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
                                    {LOCATIONS.map(l => (
                                        <button key={l.id} type="button"
                                            onClick={() => { setLocation(l.id); setLocDropOpen(false); }}
                                            className={`w-full px-3 py-2 text-left text-sm transition-colors ${location === l.id ? 'bg-accent-primary/12 text-accent-primary font-semibold' : 'text-text-secondary hover:bg-white/5 hover:text-text-primary'}`}>
                                            {l.label}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

            </div>{/* end filter groups */}

                {/* Actions — fixed right, outside wrap */}
                <div className="flex flex-col items-end justify-start gap-2 shrink-0 pt-5">
                    <button type="button" onClick={() => navigate(`/cv-upload?docId=${selectedId}`)}
                        disabled={!selectedId}
                        className="h-8 px-3.5 rounded-xl text-sm font-semibold border border-white/10 bg-white/5 hover:bg-white/10 disabled:opacity-40 disabled:cursor-not-allowed text-text-primary transition-all flex items-center gap-1.5">
                        <Eye className="w-3.5 h-3.5" /> Xem / Sửa CV
                    </button>
                    <button type="button" onClick={handleUseCv}
                        disabled={!selectedId || linking}
                        className="h-8 px-4 rounded-xl text-sm font-bold bg-accent-primary hover:bg-accent-primary/90 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-all flex items-center gap-1.5">
                        {linking ? <><Loader2 className="w-3.5 h-3.5 animate-spin" />Syncing…</> : 'Sync CV Health'}
                    </button>
                </div>
            </div>

            {/* Error */}
            {linkError && (
                <div className="mx-5 mb-4 px-3 py-2 rounded-xl bg-rose-500/8 border border-rose-500/15 text-sm text-rose-400">
                    {linkError}
                </div>
            )}
        </div>

        </>
    );
}
