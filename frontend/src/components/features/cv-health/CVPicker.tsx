import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AxiosError } from 'axios';
import { UploadCloud, Loader2, ChevronDown, FileText, Eye, Target, Activity } from 'lucide-react';
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
    { id: 'fresher', label: 'Fresher' },
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
        <div className="rounded-2xl border border-white/10 bg-surface/80 backdrop-blur-md shadow-2xl overflow-visible">
            <div className="px-5 py-4 flex flex-col md:flex-row md:items-start gap-6">
                
                {/* --- Group 1: Nguồn Dữ Liệu --- */}
                <div className="flex flex-col gap-2 shrink-0 w-full md:w-[220px]">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted flex items-center gap-1.5">
                        <FileText className="w-3.5 h-3.5" /> Nguồn Dữ Liệu CV
                    </span>
                    <div className="relative" ref={cvDropRef}>
                        <button
                            type="button"
                            onClick={() => setCvDropOpen(v => !v)}
                            className="w-full flex items-center justify-between gap-2 h-10 pl-3 pr-2.5 rounded-xl bg-black/20 border border-white/10 hover:border-accent-primary/50 hover:bg-black/40 transition-all text-sm font-semibold shadow-inner"
                        >
                            <div className="flex items-center gap-2 truncate">
                                <div className="w-6 h-6 rounded bg-accent-primary/20 flex items-center justify-center shrink-0">
                                    <FileText className="w-3.5 h-3.5 text-accent-primary" />
                                </div>
                                <span className="truncate text-left text-text-primary">
                                    {loadingList ? 'Đang tải…' : selectedDoc ? selectedDoc.name : 'Chọn CV'}
                                </span>
                            </div>
                            <ChevronDown className={`w-3.5 h-3.5 text-text-muted shrink-0 transition-transform duration-150 ${cvDropOpen ? 'rotate-180' : ''}`} />
                        </button>

                        {cvDropOpen && (
                            <div className="absolute top-full left-0 mt-2 z-50 w-full md:w-80 bg-surface border border-white/10 rounded-2xl shadow-2xl shadow-black/50 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
                                <div className="p-2 space-y-0.5 max-h-52 overflow-y-auto">
                                    {listError ? (
                                        <div className="p-3 text-sm text-rose-400">{listError}</div>
                                    ) : !docs || docs.length === 0 ? (
                                        <div className="p-3 text-sm text-text-secondary text-center">Chưa có CV. Upload bên dưới.</div>
                                    ) : docs.map(d => (
                                        <button key={d.id} type="button"
                                            onClick={() => { setSelectedId(d.id); setCvDropOpen(false); }}
                                            className={`w-full flex items-center justify-between gap-2 px-3 py-2.5 rounded-xl text-left transition-colors ${selectedId === d.id ? 'bg-accent-primary/15 text-accent-primary' : 'hover:bg-white/5 text-text-primary'}`}
                                        >
                                            <div className="min-w-0 flex-1">
                                                <div className="text-sm font-semibold truncate">{d.name}</div>
                                                <div className="text-[11px] text-text-muted mt-0.5">v{d.currentVersion} · {new Date(d.updatedAt).toLocaleDateString('vi-VN')}</div>
                                            </div>
                                            {selectedId === d.id && (
                                                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-md bg-accent-primary/20 text-accent-primary shrink-0">Đang chọn</span>
                                            )}
                                        </button>
                                    ))}
                                </div>
                                <div className="border-t border-white/5 p-2 bg-black/20">
                                    <button type="button"
                                        onClick={() => navigate('/cv-upload')}
                                        className="w-full flex items-center justify-center gap-2.5 px-3 py-2.5 rounded-xl text-sm transition-all border border-dashed border-white/15 hover:border-accent-primary/50 hover:bg-accent-primary/10 cursor-pointer text-accent-primary font-semibold"
                                    >
                                        <UploadCloud className="w-4 h-4" /> Thêm CV Mới
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* --- Vertical Divider --- */}
                <div className="hidden md:block w-px min-h-[50px] bg-white/10 self-stretch mt-6"></div>

                {/* --- Group 2: Mục tiêu Ứng tuyển --- */}
                <div className="flex flex-col gap-3 flex-1 min-w-0">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted flex items-center gap-1.5">
                        <Target className="w-3.5 h-3.5 text-emerald-400" /> Cấu hình Mục tiêu Ứng tuyển
                    </span>
                    
                    <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
                        {/* Vị trí & Cấp bậc */}
                        <div className="flex flex-wrap items-center gap-2">
                            <div className="flex items-center flex-wrap gap-1 bg-black/20 p-1 rounded-full border border-white/5">
                                {ROLES.map(r => (
                                    <button key={r.id} type="button" onClick={() => setRole(r.id)}
                                        className={`h-7 px-3 rounded-full text-[12px] font-bold transition-all ${
                                            r.id === role
                                                ? 'bg-accent-primary text-white shadow-[0_0_15px_rgba(37,99,235,0.3)]'
                                                : 'text-text-muted hover:text-text-primary hover:bg-white/10'
                                        }`}>
                                        {r.label}
                                    </button>
                                ))}
                            </div>
                            
                            <div className="flex items-center flex-wrap gap-1 bg-black/20 p-1 rounded-full border border-white/5">
                                {SENIORITIES.map(s => (
                                    <button key={s.id} type="button" onClick={() => setSeniority(s.id)}
                                        className={`h-7 px-3 rounded-full text-[12px] font-bold transition-all ${
                                            s.id === seniority
                                                ? 'bg-emerald-500 text-white shadow-[0_0_15px_rgba(16,185,129,0.3)]'
                                                : 'text-text-muted hover:text-text-primary hover:bg-white/10'
                                        }`}>
                                        {s.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Thông số phụ */}
                        <div className="flex flex-wrap items-center gap-3">
                            <div className="flex items-center gap-1 bg-black/20 p-1 rounded-full border border-white/5">
                                {WORK_MODES.map(m => (
                                    <button key={m.id} type="button" onClick={() => toggleWorkMode(m.id)}
                                        className={`h-7 px-3 rounded-full text-[12px] font-bold transition-all ${
                                            workModes.includes(m.id)
                                                ? 'bg-indigo-500/30 text-indigo-200 shadow-inner'
                                                : 'text-text-muted hover:text-text-primary hover:bg-white/10'
                                        }`}>
                                        {m.label}
                                    </button>
                                ))}
                            </div>

                            <div className="flex items-center gap-2 h-9 px-3 rounded-full bg-black/20 border border-white/5">
                                <span className="text-[11px] text-text-muted font-bold">K.Nghiệm</span>
                                <input
                                    type="number" min={0} max={40} step={1} value={yearsExp}
                                    onChange={e => setYearsExp(Number(e.target.value))}
                                    className="w-6 bg-transparent text-[13px] font-black text-emerald-400 text-center focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                                />
                                <span className="text-[11px] text-text-muted">Năm</span>
                            </div>

                            <div className="relative" ref={locDropRef}>
                                <button
                                    type="button"
                                    onClick={() => setLocDropOpen(v => !v)}
                                    className="flex items-center gap-1.5 h-9 px-4 rounded-full bg-black/20 border border-white/5 hover:bg-white/5 transition-all"
                                >
                                    <span className="text-[11px] text-text-muted font-bold">Tại</span>
                                    <span className="text-[13px] text-text-primary font-bold">
                                        {LOCATIONS.find(l => l.id === location)?.label ?? location}
                                    </span>
                                    <ChevronDown className={`w-3 h-3 text-text-muted transition-transform duration-150 ${locDropOpen ? 'rotate-180' : ''}`} />
                                </button>
                                {locDropOpen && (
                                    <div className="absolute top-full right-0 mt-2 z-50 w-36 bg-surface border border-white/10 rounded-xl shadow-2xl shadow-black/50 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
                                        {LOCATIONS.map(l => (
                                            <button key={l.id} type="button"
                                                onClick={() => { setLocation(l.id); setLocDropOpen(false); }}
                                                className={`w-full px-3 py-2 text-left text-sm transition-colors ${location === l.id ? 'bg-accent-primary/12 text-accent-primary font-bold' : 'text-text-secondary hover:bg-white/5 hover:text-text-primary'}`}>
                                                {l.label}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* --- Group 3: Hành động --- */}
                <div className="flex flex-col items-stretch md:items-end justify-center gap-2 shrink-0 md:self-end w-full md:w-auto">
                    <button type="button" onClick={handleUseCv}
                        disabled={!selectedId || linking}
                        className="h-11 px-6 rounded-xl text-sm font-black bg-gradient-to-r from-accent-primary to-indigo-600 hover:from-accent-primary/90 hover:to-indigo-500 hover:shadow-[0_0_25px_rgba(37,99,235,0.4)] disabled:opacity-40 disabled:cursor-not-allowed text-white transition-all flex items-center justify-center gap-2 md:hover:scale-105 active:scale-95">
                        {linking ? <><Loader2 className="w-4 h-4 animate-spin" />Đang tính toán…</> : <><Activity className="w-4 h-4"/> Tính điểm Sức khỏe</>}
                    </button>
                    <button type="button" onClick={() => navigate(`/cv-upload?docId=${selectedId}`)}
                        disabled={!selectedId}
                        className="h-8 px-4 rounded-xl text-[12px] font-bold border border-white/10 bg-transparent hover:bg-white/5 disabled:opacity-40 disabled:cursor-not-allowed text-text-muted hover:text-text-primary transition-all flex items-center justify-center gap-1.5">
                        <Eye className="w-3.5 h-3.5" /> Chỉnh sửa nhanh CV
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
