import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AxiosError } from 'axios';
import { UploadCloud, Loader2, ChevronDown, FileText, Eye, Target, Activity, MapPin } from 'lucide-react';
import { cvDocumentApi, cvHealthApi, type CvDocument } from '../../../services/api';

interface Props {
    userId: string;
    onLinked: () => void;
    onEmpty?: (isEmpty: boolean) => void;
}

import { ROLES, SENIORITIES, LOCATIONS, WORK_MODES } from '../../../config/jobMeta';

interface NerEntity { text: string; type: string }
interface NerBlock { entities?: NerEntity[], anchor?: string, description?: string }

const MONTH_MAP: Record<string, number> = {
    jan: 0, january: 0, feb: 1, february: 1, mar: 2, march: 2, apr: 3, april: 3,
    may: 4, jun: 5, june: 5, jul: 6, july: 6, aug: 7, august: 7,
    sep: 8, sept: 8, september: 8, oct: 9, october: 9, nov: 10, november: 10,
    dec: 11, december: 11,
    th01: 0, th02: 1, th03: 2, th04: 3, th05: 4, th06: 5,
    th07: 6, th08: 7, th09: 8, th10: 9, th11: 10, th12: 11,
};

function parseDateString(str: string): Date | null {
    if (!str) return null;
    const s = str.toLowerCase().trim();
    // "Jan 2026" / "January 2026" / "Sept 2025"
    const m1 = s.match(/([a-z]{3,})[a-z]*\.?\s+(\d{4})/);
    if (m1 && MONTH_MAP[m1[1]] !== undefined) {
        return new Date(Number(m1[2]), MONTH_MAP[m1[1]], 1);
    }
    // "Tháng 7/2026" hoặc "T7/2026" hoặc "Th7 2026"
    const mVi = s.match(/(?:tháng|th\.?|t)\s*(\d{1,2})[\s\/\-\.]+(\d{4})/);
    if (mVi) {
        const mo = parseInt(mVi[1], 10) - 1;
        return new Date(Number(mVi[2]), mo >= 0 && mo <= 11 ? mo : 0, 1);
    }
    // "07/2026" / "7-2026" / "7.2026"
    const m2 = s.match(/(\d{1,2})[\/\-\.](\d{4})/);
    if (m2) {
        const mo = parseInt(m2[1], 10) - 1;
        return new Date(Number(m2[2]), mo >= 0 && mo <= 11 ? mo : 0, 1);
    }
    // "2026/07"
    const m2b = s.match(/(\d{4})[\/\-\.](\d{1,2})/);
    if (m2b) {
        const mo = parseInt(m2b[2], 10) - 1;
        return new Date(Number(m2b[1]), mo >= 0 && mo <= 11 ? mo : 0, 1);
    }
    // Năm trần "2025"
    const m3 = s.match(/(\d{4})/);
    if (m3) return new Date(Number(m3[1]), 0, 1);
    return null;
}

const PRESENT_RE = /present|nay|hiện\s*tại|now|hiện|hientai/i;
const DATE_TOKEN = '(?:(?:[a-z]{3,}[a-z]*\\.?\\s+\\d{4})|(?:(?:tháng|th\\.?|t)\\s*\\d{1,2}[\\s\\/\\-\\.]+\\d{4})|(?:\\d{1,2}[\\/\\-\\.]\\d{4})|(?:\\d{4}[\\/\\-\\.]\\d{1,2})|(?:\\d{4}))';
const RANGE_RE = new RegExp(`(${DATE_TOKEN})\\s*(?:-|–|—|to|đến|~)\\s*(${DATE_TOKEN}|present|nay|hiện\\s*tại|hientai|now|hiện)`, 'gi');

function monthsBetween(start: Date, end: Date): number {
    return (end.getFullYear() - start.getFullYear()) * 12 + (end.getMonth() - start.getMonth());
}

function extractMonthsFromText(text: string): number {
    if (!text) return 0;
    let best = 0;
    const today = new Date();
    let m: RegExpExecArray | null;
    RANGE_RE.lastIndex = 0;
    while ((m = RANGE_RE.exec(text)) !== null) {
        const start = parseDateString(m[1]);
        const endStr = m[2].trim();
        let end: Date | null;
        if (PRESENT_RE.test(endStr)) {
            end = today;
        } else {
            end = parseDateString(endStr);
        }
        if (!start || !end) continue;
        // Clamp start to today to avoid future-dated jobs polluting the count
        const effEnd = end > today ? today : end;
        if (effEnd < start) continue;
        const months = monthsBetween(start, effEnd) + 1; // +1 inclusive
        if (months > 0 && months > best) best = months;
    }
    return best;
}

function estimateYearsOfExperience(expBlocks: unknown): number {
    if (!Array.isArray(expBlocks)) return 0;
    let totalMonths = 0;
    for (const block of expBlocks) {
        if (!block) continue;
        let blockMonths = 0;
        // 1. Try DATE/DURATION entities first
        if (Array.isArray(block.entities)) {
            for (const ent of block.entities) {
                if (ent && (ent.type === 'DATE' || ent.type === 'DURATION')) {
                    blockMonths = Math.max(blockMonths, extractMonthsFromText(String(ent.text)));
                }
            }
        }
        // 2. Fallback: regex over raw anchor/description text
        if (blockMonths === 0) {
            const raw = [block.anchor, block.description, block.text, block.title]
                .filter(Boolean).join(' ');
            blockMonths = extractMonthsFromText(raw);
        }
        totalMonths += blockMonths;
    }
    return Number((totalMonths / 12).toFixed(2));
}

// Detect seniority signal from job titles & summary text.
// Returns one of SENIORITIES ids or null if no signal.
function detectSeniority(parsed: unknown): string | null {
    if (!parsed || typeof parsed !== 'object') return null;
    const obj = parsed as Record<string, unknown>;
    const parts: string[] = [];
    if (typeof obj.summary === 'string') parts.push(obj.summary);
    if (typeof obj.title === 'string') parts.push(obj.title);
    const exp = obj.experience as NerBlock[] | undefined;
    if (Array.isArray(exp)) {
        for (const b of exp) {
            if (b?.anchor) parts.push(String(b.anchor));
            for (const e of b?.entities ?? []) {
                if (e?.type === 'JOB_TITLE' && e?.text) parts.push(String(e.text));
            }
        }
    }
    const text = parts.join(' \n ').toLowerCase();
    if (!text.trim()) return null;
    // Order matters — check stronger signals first
    if (/\b(principal|staff|architect|head\s+of|cto|director)\b/.test(text)) return 'lead';
    if (/\b(manager|engineering\s+manager|em\b)/.test(text)) return 'manager';
    if (/\b(tech\s*lead|lead\s+(engineer|developer|dev)|team\s+lead)\b/.test(text)) return 'lead';
    if (/\b(senior|sr\.?|sr\s+(engineer|developer|dev))\b/.test(text)) return 'senior';
    if (/\b(mid[\s-]*level|middle\s+(engineer|developer|dev)|intermediate)\b/.test(text)) return 'mid';
    if (/\b(junior|jr\.?)\b/.test(text)) return 'junior';
    if (/\b(fresher|fresh\s+graduate|intern|internship|thực\s+tập)\b/.test(text)) return 'fresher';
    return null;
}

// Flatten any value (string/array/object) into a single text blob for keyword scanning.
function flattenToText(value: unknown, depth = 0): string {
    if (value == null || depth > 4) return '';
    if (typeof value === 'string') return value;
    if (typeof value === 'number' || typeof value === 'boolean') return String(value);
    if (Array.isArray(value)) return value.map(v => flattenToText(v, depth + 1)).filter(Boolean).join(' \n ');
    if (typeof value === 'object') {
        return Object.values(value as Record<string, unknown>)
            .map(v => flattenToText(v, depth + 1))
            .filter(Boolean)
            .join(' \n ');
    }
    return '';
}

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
        calculated_years_exp: 0,
        detected_seniority: null as string | null,
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

    out.calculated_years_exp = estimateYearsOfExperience(exp);
    out.detected_seniority = detectSeniority(parsed);

    if (Array.isArray(edu)) {
        for (const block of edu) {
            for (const e of block.entities ?? []) {
                if (e?.type === 'DEGREE' && !out.degree) out.degree = e.text;
                if (e?.type === 'MAJOR' && !out.major) out.major = e.text;
            }
            // Fallback: scan anchor/description for degree keywords
            if (!out.degree) {
                const txt = ((block.anchor || '') + ' ' + (block.description || '')).toLowerCase();
                const m = txt.match(/\b(ph\.?d|doctor|master|bachelor|engineer|associate|diploma|college|kỹ sư|cử nhân|thạc sĩ|tiến sĩ|cao đẳng)\b/);
                if (m) out.degree = m[1];
            }
            if (!out.major) {
                const txt = (block.anchor || '') + ' ' + (block.description || '');
                const m = txt.match(/\b(?:in|of|ngành|chuyên ngành)\s+([A-Za-zÀ-ỹ\s]{3,60})/i);
                if (m) out.major = m[1].trim().split(/[,.\n]/)[0];
            }
        }
    }
    if (Array.isArray(exp)) {
        const titles = new Set<string>();
        for (const block of exp) {
            for (const e of block.entities ?? []) {
                if (e?.type === 'JOB_TITLE' && typeof e.text === 'string') titles.add(e.text.trim());
            }
            if (block.anchor && typeof block.anchor === 'string') {
                // anchor often contains the job title as the first line
                const firstLine = block.anchor.split('\n')[0].trim();
                if (firstLine && firstLine.length < 80) titles.add(firstLine);
            }
        }
        out.past_job_titles = Array.from(titles);
    }

    // Count projects from BOTH the dedicated `projects` section AND from `experience`
    // entries (many CVs put real projects under work history). Skill-density uses
    // SKILL/TECH entity counts; if an experience block has its own Stack, that
    // contributes to skill count.
    const projectLikeBlocks: NerBlock[] = [];
    if (Array.isArray(projects)) projectLikeBlocks.push(...projects);
    if (Array.isArray(exp)) projectLikeBlocks.push(...exp);
    if (projectLikeBlocks.length > 0) {
        out.num_projects = projectLikeBlocks.length;
        out.project_skill_counts = projectLikeBlocks.map(p => {
            const fromEntities = (p.entities ?? []).filter(e => e?.type === 'SKILL' || e?.type === 'TECH').length;
            // Bullet/Stack hints in description bump density signal if NER missed them
            const bulletBoost = ((p.description || '').match(/[•\-\*]/g) || []).length;
            return Math.max(fromEntities, Math.min(bulletBoost, 6));
        });
    }

    // Achievement: flatten certs + scan summary/exp for award keywords
    const achievementParts: string[] = [];
    achievementParts.push(flattenToText(obj.certifications));
    achievementParts.push(flattenToText(obj.awards));
    achievementParts.push(flattenToText(obj.achievements));
    // Scan summary too — awards/certs often mentioned there
    if (typeof obj.summary === 'string') achievementParts.push(obj.summary);
    out.achievement_text = achievementParts.filter(Boolean).join(' \n ');

    // Language: scan many possible shapes (NER inconsistent across CVs)
    const langCandidates: unknown[] = [
        obj.languages, obj.language, (obj as any).Languages, (obj as any).Language,
    ];
    if (skillsField && typeof skillsField === 'object') {
        const s = skillsField as Record<string, unknown>;
        langCandidates.push(s.languages, s.language, (s as any).Languages);
    }
    const langText = langCandidates.map(v => flattenToText(v)).filter(Boolean).join(' \n ');
    out.language_text = langText;

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
    // Track whether the user has manually touched these — auto-detection only
    // overrides untouched fields, never user intent.
    const [seniorityTouched, setSeniorityTouched] = useState(false);
    const [yearsTouched, setYearsTouched] = useState(false);
    const [autoNotice, setAutoNotice] = useState<string | null>(null);
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

    // Role & Seniority dropdowns
    const [roleDropOpen, setRoleDropOpen] = useState(false);
    const roleDropRef = useRef<HTMLDivElement>(null);
    const [seniorityDropOpen, setSeniorityDropOpen] = useState(false);
    const seniorityDropRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleClick = (e: MouseEvent) => {
            if (cvDropRef.current && !cvDropRef.current.contains(e.target as Node)) setCvDropOpen(false);
            if (locDropRef.current && !locDropRef.current.contains(e.target as Node)) setLocDropOpen(false);
            if (roleDropRef.current && !roleDropRef.current.contains(e.target as Node)) setRoleDropOpen(false);
            if (seniorityDropRef.current && !seniorityDropRef.current.contains(e.target as Node)) setSeniorityDropOpen(false);
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

    // Prefill form từ config đã lưu (nếu user từng bấm "Tính điểm" trước đó)
    useEffect(() => {
        let cancelled = false;
        cvHealthApi.getSavedConfig(userId)
            .then(res => {
                if (cancelled) return;
                const cfg = res.data;
                if (cfg.target_role) setRole(cfg.target_role);
                if (cfg.seniority) {
                    setSeniority(cfg.seniority);
                    setSeniorityTouched(true);
                }
                if (cfg.years_experience != null) {
                    setYearsExp(Number(cfg.years_experience.toFixed(1)));
                    setYearsTouched(true);
                }
                if (cfg.preferred_location) setLocation(cfg.preferred_location);
                if (cfg.preferred_work_modes && cfg.preferred_work_modes.length > 0) {
                    setWorkModes(cfg.preferred_work_modes);
                }
            })
            .catch(() => { /* 404 lần đầu — bỏ qua, giữ default */ });
        return () => { cancelled = true; };
    }, [userId]);

    function toggleWorkMode(mode: string) {
        setWorkModes(prev => prev.includes(mode) ? prev.filter(m => m !== mode) : [...prev, mode]);
    }

    async function handleUseCv() {
        if (!selectedId) return;
        setLinking(true);
        setLinkError(null);
        setAutoNotice(null);
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

            // ── Auto-detection (only when user didn't override) ─────────────
            const notices: string[] = [];

            // Seniority: if CV signals senior/lead and user is on untouched default 'junior',
            // promote and apply default years for that level.
            let effSeniority = seniority;
            if (!seniorityTouched && extras.detected_seniority && extras.detected_seniority !== seniority) {
                effSeniority = extras.detected_seniority;
                setSeniority(effSeniority);
                notices.push(`Cấp bậc tự động cập nhật → ${effSeniority.toUpperCase()} (phát hiện từ chức danh trong CV)`);
            }

            // Years: prefer auto-calculated when user didn't touch the input.
            // Allow override only when calc > 0 (avoid clobbering a real fresher CV with 0).
            let finalYears = Number.isNaN(yearsExp) ? null : Math.max(0, yearsExp);
            if (!yearsTouched && extras.calculated_years_exp > 0) {
                finalYears = extras.calculated_years_exp;
                setYearsExp(Number(extras.calculated_years_exp.toFixed(1)));
                notices.push(`Số năm KN tự động: ${extras.calculated_years_exp.toFixed(1)} năm (tính từ thời gian các job trong CV)`);
            }

            if (notices.length > 0) setAutoNotice(notices.join(' · '));

            await cvHealthApi.upsertCv(userId, role, skills.map(name => ({ name, last_used_year: currentYear })), {
                yearsExperience: finalYears, preferredLocation: location.trim() || null,
                preferredWorkModes: workModes.length > 0 ? workModes : null,
                seniority: effSeniority, pastJobTitles: extras.past_job_titles,
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

                    <div className="flex flex-wrap items-stretch gap-4">

                        {/* ── BLOCK A: Ảnh hưởng điểm ────────────────── */}
                        <div className="flex flex-col gap-2 p-3 rounded-2xl bg-emerald-500/[0.04] border border-emerald-500/15 min-w-0">
                            <span className="text-[10px] font-bold uppercase tracking-widest text-emerald-400 flex items-center gap-1.5">
                                <Target className="w-3 h-3" /> Ảnh hưởng điểm chấm
                            </span>
                            <div className="flex flex-wrap items-center gap-2">
                                {/* Role */}
                                <div className="relative" ref={roleDropRef}>
                                    <button type="button" onClick={() => setRoleDropOpen(v => !v)}
                                        className="flex items-center gap-2 h-9 px-4 rounded-full bg-black/20 border border-white/5 hover:bg-white/5 transition-all">
                                        <div className="flex items-baseline gap-1.5">
                                            <span className="text-[11px] text-text-muted font-bold">Vị trí</span>
                                            <span className="text-[13px] text-accent-primary font-black">
                                                {ROLES.find(r => r.id === role)?.label ?? role}
                                            </span>
                                        </div>
                                        <ChevronDown className={`w-3.5 h-3.5 text-text-muted transition-transform duration-150 ${roleDropOpen ? 'rotate-180' : ''}`} />
                                    </button>
                                    {roleDropOpen && (
                                        <div className="absolute top-full left-0 mt-2 z-50 w-48 bg-surface border border-white/10 rounded-xl shadow-2xl shadow-black/50 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
                                            <div className="max-h-60 overflow-y-auto p-1.5 space-y-0.5">
                                                {ROLES.map(r => (
                                                    <button key={r.id} type="button"
                                                        onClick={() => { setRole(r.id); setRoleDropOpen(false); }}
                                                        className={`w-full px-3 py-2 rounded-lg text-left text-sm transition-colors ${role === r.id ? 'bg-accent-primary/15 text-accent-primary font-bold' : 'text-text-secondary hover:bg-white/5 hover:text-text-primary'}`}>
                                                        {r.label}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Seniority */}
                                <div className="relative" ref={seniorityDropRef}>
                                    <button type="button" onClick={() => setSeniorityDropOpen(v => !v)}
                                        className="flex items-center gap-2 h-9 px-4 rounded-full bg-black/20 border border-white/5 hover:bg-white/5 transition-all">
                                        <div className="flex items-baseline gap-1.5">
                                            <span className="text-[11px] text-text-muted font-bold">Cấp bậc</span>
                                            <span className="text-[13px] text-emerald-400 font-black">
                                                {SENIORITIES.find(s => s.id === seniority)?.label ?? seniority}
                                            </span>
                                        </div>
                                        <ChevronDown className={`w-3.5 h-3.5 text-text-muted transition-transform duration-150 ${seniorityDropOpen ? 'rotate-180' : ''}`} />
                                    </button>
                                    {seniorityDropOpen && (
                                        <div className="absolute top-full left-0 mt-2 z-50 w-40 bg-surface border border-white/10 rounded-xl shadow-2xl shadow-black/50 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
                                            <div className="p-1.5 space-y-0.5">
                                                {SENIORITIES.map(s => (
                                                    <button key={s.id} type="button"
                                                        onClick={() => { setSeniority(s.id); setSeniorityTouched(true); setSeniorityDropOpen(false); }}
                                                        className={`w-full px-3 py-2 rounded-lg text-left text-sm transition-colors ${seniority === s.id ? 'bg-emerald-500/15 text-emerald-400 font-bold' : 'text-text-secondary hover:bg-white/5 hover:text-text-primary'}`}>
                                                        {s.label}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>

                            </div>
                        </div>

                        {/* ── BLOCK B: Lọc gợi ý việc làm (không ảnh hưởng điểm) ── */}
                        <div className="flex flex-col gap-2 p-3 rounded-2xl bg-white/[0.02] border border-white/5 min-w-0">
                            <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted/80 flex items-center gap-1.5">
                                <MapPin className="w-3 h-3" /> Lọc gợi ý việc làm
                                <span className="ml-1 normal-case font-normal tracking-normal text-text-muted/60 text-[10px]">(không ảnh hưởng điểm)</span>
                            </span>
                            <div className="flex flex-wrap items-center gap-2">
                                <div className="flex items-center gap-1 bg-black/20 p-1 rounded-full border border-white/5">
                                    {WORK_MODES.map(m => (
                                        <button key={m.id} type="button" onClick={() => toggleWorkMode(m.id)}
                                            className={`h-7 px-3 rounded-full text-[12px] font-bold transition-all ${
                                                workModes.includes(m.id)
                                                    ? 'bg-indigo-500/25 text-indigo-200 shadow-inner'
                                                    : 'text-text-muted hover:text-text-primary hover:bg-white/10'
                                            }`}>
                                            {m.label}
                                        </button>
                                    ))}
                                </div>
                                <div className="relative" ref={locDropRef}>
                                    <button
                                        type="button"
                                        onClick={() => setLocDropOpen(v => !v)}
                                        className="flex items-center gap-2 h-9 px-4 rounded-full bg-black/20 border border-white/5 hover:bg-white/5 transition-all"
                                    >
                                        <div className="flex items-baseline gap-1.5">
                                            <span className="text-[11px] text-text-muted font-bold">Tại</span>
                                            <span className="text-[13px] text-text-primary font-bold">
                                                {LOCATIONS.find(l => l.id === location)?.label ?? location}
                                            </span>
                                        </div>
                                        <ChevronDown className={`w-3 h-3 text-text-muted transition-transform duration-150 ${locDropOpen ? 'rotate-180' : ''}`} />
                                    </button>
                                    {locDropOpen && (
                                        <div className="absolute top-full left-0 mt-2 z-50 w-36 bg-surface border border-white/10 rounded-xl shadow-2xl shadow-black/50 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
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

                        {/* Spacer & Hành động */}
                        <div className="flex-1 min-w-[20px]"></div>
                        <div className="flex items-center gap-2 ml-auto">
                            <button type="button" onClick={() => navigate(`/cv-upload?docId=${selectedId}`)}
                                disabled={!selectedId}
                                className="h-9 px-3 rounded-xl text-[12px] font-bold border border-white/10 bg-transparent hover:bg-white/5 disabled:opacity-40 disabled:cursor-not-allowed text-text-muted hover:text-text-primary transition-all flex items-center justify-center gap-1.5"
                                title="Chỉnh sửa nhanh CV">
                                <Eye className="w-4 h-4" />
                            </button>
                            <button type="button" onClick={handleUseCv}
                                disabled={!selectedId || linking}
                                className="h-9 px-5 rounded-xl text-sm font-black bg-gradient-to-r from-accent-primary to-indigo-600 hover:from-accent-primary/90 hover:to-indigo-500 hover:shadow-[0_0_25px_rgba(37,99,235,0.4)] disabled:opacity-40 disabled:cursor-not-allowed text-white transition-all flex items-center justify-center gap-2 md:hover:scale-105 active:scale-95">
                                {linking ? <><Loader2 className="w-4 h-4 animate-spin" />Đang tính…</> : <><Activity className="w-4 h-4"/> Tính điểm</>}
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Auto-detection notice */}
            {autoNotice && (
                <div className="mx-5 mb-3 px-3 py-2 rounded-xl bg-emerald-500/8 border border-emerald-500/15 text-[12px] text-emerald-300 flex items-start gap-2">
                    <Activity className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                    <span>{autoNotice}</span>
                </div>
            )}
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
