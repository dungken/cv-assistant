import React, { useState, useEffect, useRef } from 'react';
import {
    CheckCircle2, Sparkles, Target,
    ChevronLeft, SkipForward, Bot,
    AlertCircle, AlertTriangle, Palette, Plus, Trash2,
    Download, Loader2
} from 'lucide-react';
import {
    chatbotApi, collectorApi, CVData, cvBuilderApi, nerApi,
    BulletSuggestion, CVDraftData,
    OptimizationResponse
} from '../../services/api';
import CVPreview from './CVPreview';
import CVSectionEditor from './CVSectionEditor';
import ATSScoreDashboard from './ATSScoreDashboard';
import OptimizationPanel from './OptimizationPanel';
import AISuggestionCards from './AISuggestionCards';
import SkillAutocompleteInput from './SkillAutocompleteInput';
import TemplatePickerModal from './TemplatePickerModal';
import { cn } from '../../lib/utils';

interface CVBuilderViewProps {
    sessionId: number;
    initialCvData: CVData;
    initialStep: number;
    onDataSync?: (data: CVData) => void;
    onStepSync?: (step: number) => void;
    isArtifactMode?: boolean;
    userId?: string | null;
}

const STEP_LABELS = ["Cá nhân", "Học vấn", "Kinh nghiệm", "Kỹ năng", "Dự án", "Chứng chỉ"];

// Draft resume banner
const DraftBanner: React.FC<{
    draft: CVDraftData;
    onResume: () => void;
    onDiscard: () => void;
}> = ({ draft, onResume, onDiscard }) => (
    <div className="flex items-center justify-between gap-3 px-4 py-3 bg-amber-500/10 border border-amber-500/30 rounded-xl text-sm">
        <div className="flex items-center gap-2 text-amber-400">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>
                Bạn có bản nháp chưa hoàn thành (bước {draft.current_step}/6 — {draft.progress_percent}% xong).
            </span>
        </div>
        <div className="flex gap-2 shrink-0">
            <button onClick={onResume} className="px-3 py-1 bg-amber-500 hover:bg-amber-400 text-black rounded-lg text-xs font-bold transition-all">Tiếp tục</button>
            <button onClick={onDiscard} className="px-3 py-1 bg-white/5 hover:bg-white/10 text-slate-400 rounded-lg text-xs transition-all">Bắt đầu mới</button>
        </div>
    </div>
);

const ValidationMessage: React.FC<{ error?: string | null; warning?: string | null }> = ({ error, warning }) => {
    if (error) return <div className="flex items-center gap-1.5 mt-1 text-xs text-red-400"><AlertCircle className="w-3 h-3" /> {error}</div>;
    if (warning) return <div className="flex items-center gap-1.5 mt-1 text-xs text-amber-400"><AlertTriangle className="w-3 h-3" /> {warning}</div>;
    return null;
};

// Small reusable form primitives
const Field: React.FC<{ label: string; children: React.ReactNode; hint?: string }> = ({ label, children, hint }) => (
    <div>
        <label className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">{label}</label>
        <div className="mt-1">{children}</div>
        {hint && <div className="text-[10px] text-slate-500 mt-1">{hint}</div>}
    </div>
);

const inputClass = "w-full bg-slate-950/50 border border-white/10 rounded-xl px-3 py-2 text-sm text-slate-200 outline-none focus:border-accent-primary transition-all placeholder:text-slate-500";
const textareaClass = inputClass + " resize-none min-h-[80px]";

const SectionCard: React.FC<{ title: string; icon?: React.ReactNode; children: React.ReactNode }> = ({ title, icon, children }) => (
    <div className="bg-slate-900/60 border border-white/10 rounded-2xl p-5 space-y-4">
        <div className="flex items-center gap-2 text-sm font-bold text-white">
            {icon || <Sparkles className="w-4 h-4 text-accent-primary" />}
            {title}
        </div>
        {children}
    </div>
);

const CVBuilderView: React.FC<CVBuilderViewProps> = ({
    sessionId, initialCvData, initialStep, onDataSync, onStepSync, userId
}) => {
    const [cvData, setCvData] = useState<CVData>(initialCvData);
    const [currentStep, setCurrentStep] = useState(initialStep);
    const [jdText, setJdText] = useState('');
    const [optimizationRes, setOptimizationRes] = useState<OptimizationResponse | null>(null);
    const [isOptimizing, setIsOptimizing] = useState(false);
    const [activeTab, setActiveTab] = useState<'editor' | 'preview' | 'analysis'>('preview');

    // Draft state
    const [pendingDraft, setPendingDraft] = useState<CVDraftData | null>(null);
    const [draftChecked, setDraftChecked] = useState(false);
    const [lastSavedAt, setLastSavedAt] = useState<string | null>(null);

    // AI suggestions
    const [suggestions, setSuggestions] = useState<BulletSuggestion[]>([]);
    const [isSuggesting, setIsSuggesting] = useState(false);
    const [rawExpInput, setRawExpInput] = useState('');
    const [suggestTargetIdx, setSuggestTargetIdx] = useState(0);

    // Validation
    const [fieldErrors, setFieldErrors] = useState<Record<string, { error: string | null; warning: string | null }>>({});

    // Template picker
    const [templatePickerOpen, setTemplatePickerOpen] = useState(false);
    const [selectedTemplate, setSelectedTemplate] = useState<{ id: number; name: string } | null>(null);

    // Export
    const [isExporting, setIsExporting] = useState(false);

    const autoSaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const progressPercent = Math.round((Math.min(currentStep, 6) / 6) * 100);

    // ─── Data mutation helpers ────────────────────────────────────────────
    const commitCv = (next: CVData) => {
        setCvData(next);
        onDataSync?.(next);
        collectorApi
            .updateProgress(sessionId, currentStep, JSON.stringify(next), currentStep >= 7)
            .catch(() => {});
    };

    const updatePersonal = (field: keyof CVData['personal_info'], value: string) =>
        commitCv({ ...cvData, personal_info: { ...cvData.personal_info, [field]: value } });

    const updateArrayItem = <K extends 'education' | 'experience' | 'projects' | 'certifications'>(
        key: K, idx: number, patch: Record<string, any>
    ) => {
        const list = [...(cvData[key] || [])] as any[];
        list[idx] = { ...list[idx], ...patch };
        commitCv({ ...cvData, [key]: list } as CVData);
    };

    const addArrayItem = <K extends 'education' | 'experience' | 'projects' | 'certifications'>(
        key: K, template: any
    ) => {
        commitCv({ ...cvData, [key]: [...(cvData[key] || []), template] } as CVData);
    };

    const removeArrayItem = <K extends 'education' | 'experience' | 'projects' | 'certifications'>(
        key: K, idx: number
    ) => {
        commitCv({ ...cvData, [key]: (cvData[key] || []).filter((_: any, i: number) => i !== idx) } as CVData);
    };

    // ─── Draft load / autosave ────────────────────────────────────────────
    useEffect(() => {
        if (!userId || draftChecked) return;
        setDraftChecked(true);
        cvBuilderApi.getDraft(userId).then(res => {
            if (res.data.current_step >= 2 && res.data.current_step < 7) {
                setPendingDraft(res.data);
            }
        }).catch(() => {/* no draft */});
    }, [userId, draftChecked]);

    useEffect(() => {
        if (!userId) return;
        if (autoSaveTimerRef.current) clearTimeout(autoSaveTimerRef.current);
        autoSaveTimerRef.current = setTimeout(() => {
            const completedSteps = STEP_LABELS.slice(0, Math.max(0, currentStep - 1)).map(s => s.toLowerCase());
            cvBuilderApi.saveDraft(userId, {
                user_id: userId,
                current_step: currentStep,
                completed_steps: completedSteps,
                progress_percent: progressPercent,
                data: cvData,
            })
                .then(() => setLastSavedAt(new Date().toLocaleTimeString()))
                .catch(() => {/* silent */});
        }, 30000);
        return () => { if (autoSaveTimerRef.current) clearTimeout(autoSaveTimerRef.current); };
    }, [cvData, currentStep, userId, progressPercent]);

    useEffect(() => {
        setCvData(initialCvData);
        setCurrentStep(initialStep);
        if (initialStep >= 7 && activeTab !== 'analysis') setActiveTab('editor');
    }, [initialCvData, initialStep]);

    const handleResumeDraft = () => {
        if (!pendingDraft) return;
        setCvData(pendingDraft.data);
        setCurrentStep(pendingDraft.current_step);
        onDataSync?.(pendingDraft.data);
        onStepSync?.(pendingDraft.current_step);
        setPendingDraft(null);
    };

    const handleDiscardDraft = () => {
        if (userId) cvBuilderApi.deleteDraft(userId).catch(() => {});
        setPendingDraft(null);
    };

    // ─── AI suggestions ───────────────────────────────────────────────────
    const handleGetSuggestions = async (targetIdx: number) => {
        if (!rawExpInput.trim()) return;
        setIsSuggesting(true);
        setSuggestions([]);
        setSuggestTargetIdx(targetIdx);
        try {
            const exp = cvData.experience[targetIdx];
            const res = await cvBuilderApi.suggest({
                job_title: exp?.position || cvData.personal_info.title || 'Developer',
                company: exp?.company,
                raw_input: rawExpInput,
                section: 'experience',
            });
            setSuggestions(res.data.suggestions);
        } catch {
            /* silent */
        }
        setIsSuggesting(false);
    };

    const handleSuggestionSelect = (bullet: string) => {
        const list = [...cvData.experience];
        if (!list[suggestTargetIdx]) return;
        const exp = { ...list[suggestTargetIdx] };
        const desc = Array.isArray(exp.description) ? exp.description : [];
        exp.description = [...desc, bullet];
        list[suggestTargetIdx] = exp;
        commitCv({ ...cvData, experience: list });
    };

    // ─── Validation (persists to cvData on blur) ──────────────────────────
    const handleFieldBlur = async (field: keyof CVData['personal_info'], fieldType: string) => {
        const value = cvData.personal_info[field] || '';
        if (!String(value).trim()) {
            setFieldErrors(prev => ({ ...prev, [field]: { error: null, warning: null } }));
            return;
        }
        try {
            const res = await cvBuilderApi.validate(field, String(value), fieldType);
            setFieldErrors(prev => ({
                ...prev,
                [field]: { error: res.data.error, warning: res.data.warning }
            }));
        } catch {/* silent */}
    };

    // ─── Template ─────────────────────────────────────────────────────────
    const handleTemplateConfirm = (tpl: { id: number; name: string }) => {
        setSelectedTemplate({ id: tpl.id, name: tpl.name });
        setTemplatePickerOpen(false);
        commitCv({ ...cvData, template_id: tpl.id } as any);
    };

    // ─── Export PDF ───────────────────────────────────────────────────────
    const handleExportPdf = async () => {
        setIsExporting(true);
        try {
            const res = await nerApi.generatePdf(cvData);
            const blob = new Blob([res.data as any], { type: 'application/pdf' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            const name = (cvData.personal_info.full_name || 'cv').replace(/\s+/g, '_').toLowerCase();
            a.download = `${name}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (e) {
            console.error('Export PDF failed:', e);
        }
        setIsExporting(false);
    };

    // ─── ATS Optimize (post-completion) ───────────────────────────────────
    const handleOptimize = async () => {
        setIsOptimizing(true);
        setActiveTab('analysis');
        try {
            const res = await chatbotApi.getOptimizationSuggestions(cvData, jdText);
            setOptimizationRes(res.data);
        } catch (error) {
            console.error("Optimization failed:", error);
        }
        setIsOptimizing(false);
    };

    const handleApplySuggestion = async (id: string, preview?: string) => {
        if (!preview) return;
        const updatedData = { ...cvData };
        if (id.includes('summary')) {
            updatedData.summary = preview;
        } else if (id.includes('keyword') || id.includes('skill')) {
            const newSkills = [...updatedData.skills];
            preview.split(',').map(s => s.trim()).forEach(s => {
                if (!newSkills.includes(s)) newSkills.push(s);
            });
            updatedData.skills = newSkills;
        }
        commitCv(updatedData);
        if (optimizationRes) {
            setOptimizationRes({
                ...optimizationRes,
                suggestions: optimizationRes.suggestions.filter(s => s.id !== id)
            });
        }
    };

    const handleSectionUpdate = (type: string, index: number | null, newData: any) => {
        const updatedData = { ...cvData };
        if (type === 'personal_info') updatedData.personal_info = newData;
        else if (type === 'experience' && index !== null) updatedData.experience[index] = newData;
        else if (type === 'projects' && index !== null) updatedData.projects[index] = newData;
        else if (type === 'summary') updatedData.summary = newData;
        commitCv(updatedData);
    };

    return (
        <div className="flex flex-col h-full bg-canvas overflow-hidden">
            {/* Progress Header */}
            <div className="p-6 bg-slate-900/40 backdrop-blur-md border-b border-white/5">
                {pendingDraft && (
                    <div className="mb-4">
                        <DraftBanner draft={pendingDraft} onResume={handleResumeDraft} onDiscard={handleDiscardDraft} />
                    </div>
                )}

                <div className="flex justify-between items-center mb-4">
                    <div className="flex flex-col gap-1">
                        <h3 className="text-sm font-black uppercase tracking-[0.2em] text-accent-primary flex items-center gap-2">
                            {currentStep >= 7 ? (
                                <span className="flex items-center gap-2 text-emerald-500 font-black tracking-widest">
                                    <CheckCircle2 className="w-4 h-4" /> CV Construction Complete
                                </span>
                            ) : (
                                <>Step {currentStep}/6: {STEP_LABELS[currentStep - 1]}</>
                            )}
                        </h3>
                        <span className="text-[10px] font-bold text-text-muted bg-white/5 px-2 py-1 rounded tracking-widest uppercase w-fit">
                            {progressPercent}% Complete
                        </span>
                    </div>

                    <div className="flex items-center gap-2">
                        {currentStep > 1 && currentStep < 7 && (
                            <button
                                onClick={() => { const p = Math.max(1, currentStep - 1); setCurrentStep(p); onStepSync?.(p); }}
                                className="flex items-center gap-1 px-3 py-2 rounded-xl font-bold text-xs bg-white/5 hover:bg-white/10 text-text-muted border border-white/10 transition-all"
                            >
                                <ChevronLeft className="w-3.5 h-3.5" /> Quay lại
                            </button>
                        )}
                        {currentStep < 7 && (
                            <button
                                onClick={() => { const n = Math.min(7, currentStep + 1); setCurrentStep(n); onStepSync?.(n); }}
                                className="flex items-center gap-1 px-3 py-2 rounded-xl font-bold text-xs bg-white/5 hover:bg-white/10 text-text-muted border border-white/10 transition-all"
                            >
                                <SkipForward className="w-3.5 h-3.5" /> Bỏ qua
                            </button>
                        )}
                        <button
                            onClick={() => setTemplatePickerOpen(true)}
                            className="flex items-center gap-1.5 px-3 py-2 rounded-xl font-bold text-xs bg-accent-primary/10 hover:bg-accent-primary/20 text-accent-primary border border-accent-primary/20 transition-all"
                            title="Chọn template CV"
                        >
                            <Palette className="w-3.5 h-3.5" />
                            {selectedTemplate ? selectedTemplate.name : 'Template'}
                        </button>
                        <button
                            onClick={handleExportPdf}
                            disabled={isExporting}
                            className={cn(
                                "flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-xs transition-all duration-500 shadow-lg",
                                currentStep >= 7
                                    ? "bg-emerald-500 hover:bg-emerald-600 text-white shadow-[0_0_20px_rgba(16,185,129,0.3)]"
                                    : "bg-white/5 hover:bg-white/10 text-text-muted border border-white/10",
                                isExporting && "opacity-50 cursor-wait"
                            )}
                        >
                            {isExporting
                                ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Đang xuất...</>
                                : <><Download className="w-3.5 h-3.5" /> Export PDF</>}
                        </button>
                    </div>
                </div>

                {/* Step bar */}
                <div className="flex gap-1.5 h-1.5 w-full">
                    {STEP_LABELS.map((_, idx) => (
                        <div
                            key={idx}
                            className={cn(
                                "flex-1 rounded-full transition-all duration-500",
                                idx + 1 < currentStep ? "bg-emerald-500" :
                                    idx + 1 === currentStep ? "bg-accent-primary animate-pulse" : "bg-white/5"
                            )}
                        />
                    ))}
                </div>

                <div className="flex gap-1.5 mt-2">
                    {STEP_LABELS.map((label, idx) => (
                        <div key={idx} className="flex-1 text-center">
                            <span className={cn(
                                "text-[9px] font-bold uppercase tracking-wide",
                                idx + 1 < currentStep ? "text-emerald-400" :
                                    idx + 1 === currentStep ? "text-accent-primary" : "text-slate-600"
                            )}>{label}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-y-auto no-scrollbar p-6 space-y-8">
                {currentStep >= 7 && (
                    <div className="flex p-1 bg-white/5 border border-white/10 rounded-2xl w-fit mx-auto sticky top-0 z-10 backdrop-blur-md">
                        <button onClick={() => setActiveTab('preview')} className={cn("flex items-center gap-2 px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all", activeTab === 'preview' ? "bg-white/10 text-white shadow-lg" : "text-text-muted hover:text-white")}>Preview</button>
                        <button onClick={() => setActiveTab('analysis')} className={cn("flex items-center gap-2 px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all", activeTab === 'analysis' ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/20" : "text-text-muted hover:text-white")}><Target className="w-3.5 h-3.5" /> Market Analysis</button>
                        <button onClick={() => setActiveTab('editor')} className={cn("flex items-center gap-2 px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all", activeTab === 'editor' ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/20" : "text-text-muted hover:text-white")}>Builder</button>
                    </div>
                )}

                {/* CV Preview (always shown on lg screens while stepping) */}
                {(activeTab === 'preview' || currentStep < 7) && (
                    <div className={cn(
                        "max-w-[800px] mx-auto rounded-2xl overflow-hidden shadow-2xl border border-white/5 bg-white scale-95 origin-top transition-transform duration-500",
                        currentStep < 7 ? "hidden lg:block" : ""
                    )}>
                        <CVPreview data={cvData} />
                    </div>
                )}

                {/* Post-completion analysis tab */}
                {activeTab === 'analysis' && currentStep >= 7 && (
                    <div className="max-w-[1000px] mx-auto space-y-8 animate-in fade-in zoom-in duration-500">
                        {optimizationRes ? (
                            <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
                                <div className="lg:col-span-3 space-y-8">
                                    <ATSScoreDashboard data={{
                                        total_score: optimizationRes.ats_score,
                                        breakdown: optimizationRes.breakdown,
                                        issues: optimizationRes.suggestions.map(s => ({
                                            category: s.category,
                                            severity: s.priority === 'critical' ? 'high' : s.priority === 'important' ? 'medium' : 'low',
                                            message: s.title,
                                            suggestion: s.description
                                        })),
                                        benchmark_avg: 72
                                    }} />
                                </div>
                                <div className="lg:col-span-2">
                                    <OptimizationPanel suggestions={optimizationRes.suggestions} onApply={handleApplySuggestion} isLoading={isOptimizing} />
                                </div>
                            </div>
                        ) : (
                            <div className="bg-slate-900/60 border border-white/5 rounded-3xl p-12 text-center space-y-6">
                                <div className="w-20 h-20 bg-indigo-500/10 rounded-full flex items-center justify-center mx-auto border border-indigo-500/20">
                                    <Target className="w-10 h-10 text-indigo-400" />
                                </div>
                                <div className="max-w-md mx-auto space-y-2">
                                    <h3 className="text-xl font-black text-white uppercase tracking-tighter">ATS & Market Optimization</h3>
                                    <p className="text-slate-400 text-sm">Paste the Job Description for the role you're targeting to get professional AI suggestions and ATS scoring.</p>
                                </div>
                                <div className="max-w-xl mx-auto space-y-4">
                                    <textarea value={jdText} onChange={(e) => setJdText(e.target.value)} placeholder="Paste Job Description text here..." className="w-full bg-slate-950/50 border border-white/10 rounded-2xl p-6 text-sm text-slate-300 outline-none focus:border-indigo-500 transition-all min-h-[200px] resize-none" />
                                    <button onClick={handleOptimize} disabled={!jdText.trim() || isOptimizing} className="w-full py-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-2xl text-sm font-black uppercase tracking-[0.2em] shadow-xl shadow-indigo-500/20 flex items-center justify-center gap-2 transition-all disabled:opacity-50">
                                        {isOptimizing ? <><Loader2 className="w-5 h-5 animate-spin" /> ANALYZING...</> : <><Sparkles className="w-5 h-5" /> REVEAL OPTIMIZATION PATH</>}
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Builder / Editor Tab (post-completion) */}
                {activeTab === 'editor' && currentStep >= 7 && (
                    <div className="max-w-[800px] mx-auto space-y-4 animate-in fade-in zoom-in duration-500">
                        <CVSectionEditor title="Personal Information" sectionType="personal_info" initialData={cvData.personal_info} onSave={(d) => handleSectionUpdate('personal_info', null, d)} />
                        <CVSectionEditor title="Professional Summary" sectionType="summary" initialData={cvData.summary || ""} onSave={(d) => handleSectionUpdate('summary', null, d)} />
                        {cvData.experience.map((exp, idx) => (
                            <CVSectionEditor key={`exp-${idx}`} title={`Experience: ${exp.company}`} sectionType="experience" initialData={exp} onSave={(d) => handleSectionUpdate('experience', idx, d)} />
                        ))}
                    </div>
                )}

                {/* ─── In-flow step panels (1-6) ───────────────────────────── */}
                {currentStep < 7 && (
                    <div className="max-w-[900px] mx-auto space-y-6">

                        {/* STEP 1: Personal info + validation */}
                        {currentStep === 1 && (
                            <SectionCard title="Thông tin cá nhân">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                    <Field label="Họ tên">
                                        <input type="text" className={inputClass} placeholder="Nguyễn Văn A"
                                            value={cvData.personal_info.full_name || ''}
                                            onChange={e => updatePersonal('full_name', e.target.value)} />
                                    </Field>
                                    <Field label="Vị trí ứng tuyển">
                                        <input type="text" className={inputClass} placeholder="Backend Developer"
                                            value={cvData.personal_info.title || ''}
                                            onChange={e => updatePersonal('title', e.target.value)} />
                                    </Field>
                                    <Field label="Email">
                                        <input type="text" className={inputClass} placeholder="name@email.com"
                                            value={cvData.personal_info.email || ''}
                                            onChange={e => updatePersonal('email', e.target.value)}
                                            onBlur={() => handleFieldBlur('email', 'email')} />
                                        <ValidationMessage {...(fieldErrors['email'] || {})} />
                                    </Field>
                                    <Field label="Số điện thoại">
                                        <input type="text" className={inputClass} placeholder="0901234567"
                                            value={cvData.personal_info.phone || ''}
                                            onChange={e => updatePersonal('phone', e.target.value)}
                                            onBlur={() => handleFieldBlur('phone', 'phone')} />
                                        <ValidationMessage {...(fieldErrors['phone'] || {})} />
                                    </Field>
                                    <Field label="Địa chỉ">
                                        <input type="text" className={inputClass} placeholder="Hà Nội, Việt Nam"
                                            value={cvData.personal_info.location || ''}
                                            onChange={e => updatePersonal('location', e.target.value)} />
                                    </Field>
                                </div>
                                <Field label="Tóm tắt nghề nghiệp (tùy chọn)">
                                    <textarea className={textareaClass} placeholder="1-2 câu giới thiệu bản thân, điểm mạnh, mục tiêu..."
                                        value={cvData.summary || ''}
                                        onChange={e => commitCv({ ...cvData, summary: e.target.value })} />
                                </Field>
                            </SectionCard>
                        )}

                        {/* STEP 2: Education */}
                        {currentStep === 2 && (
                            <SectionCard title="Học vấn">
                                {(cvData.education || []).length === 0 && (
                                    <p className="text-xs text-slate-500 italic">Chưa có học vấn nào. Nhấn "Thêm học vấn" để bắt đầu.</p>
                                )}
                                {(cvData.education || []).map((edu: any, idx: number) => (
                                    <div key={idx} className="bg-slate-950/40 border border-white/5 rounded-xl p-4 space-y-3">
                                        <div className="flex justify-between items-center">
                                            <span className="text-xs font-bold text-slate-400">Mục #{idx + 1}</span>
                                            <button onClick={() => removeArrayItem('education', idx)} className="text-red-400 hover:text-red-300 p-1 rounded"><Trash2 className="w-3.5 h-3.5" /></button>
                                        </div>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                            <Field label="Trường">
                                                <input className={inputClass} placeholder="ĐH Bách Khoa Hà Nội" value={edu.school || ''} onChange={e => updateArrayItem('education', idx, { school: e.target.value })} />
                                            </Field>
                                            <Field label="Bằng cấp">
                                                <input className={inputClass} placeholder="Cử nhân CNTT" value={edu.degree || ''} onChange={e => updateArrayItem('education', idx, { degree: e.target.value })} />
                                            </Field>
                                            <Field label="Chuyên ngành">
                                                <input className={inputClass} placeholder="Kỹ thuật phần mềm" value={edu.major || ''} onChange={e => updateArrayItem('education', idx, { major: e.target.value })} />
                                            </Field>
                                            <Field label="GPA (tùy chọn)">
                                                <input className={inputClass} placeholder="3.5" value={edu.gpa ?? ''} onChange={e => updateArrayItem('education', idx, { gpa: e.target.value ? parseFloat(e.target.value) : null })} />
                                            </Field>
                                            <Field label="Bắt đầu">
                                                <input className={inputClass} placeholder="2018" value={edu.start_date || ''} onChange={e => updateArrayItem('education', idx, { start_date: e.target.value })} />
                                            </Field>
                                            <Field label="Kết thúc">
                                                <input className={inputClass} placeholder="2022" value={edu.end_date || ''} onChange={e => updateArrayItem('education', idx, { end_date: e.target.value })} />
                                            </Field>
                                        </div>
                                    </div>
                                ))}
                                <button onClick={() => addArrayItem('education', { school: '', degree: '', major: '', start_date: '', end_date: '', gpa: null })}
                                    className="w-full py-2 border border-dashed border-white/10 rounded-lg text-xs font-bold text-slate-400 hover:bg-white/5 hover:text-white transition-all flex items-center justify-center gap-1.5">
                                    <Plus className="w-3.5 h-3.5" /> Thêm học vấn
                                </button>
                            </SectionCard>
                        )}

                        {/* STEP 3: Experience + AI bullet generator */}
                        {currentStep === 3 && (
                            <>
                                <SectionCard title="Kinh nghiệm làm việc">
                                    {(cvData.experience || []).length === 0 && (
                                        <p className="text-xs text-slate-500 italic">Chưa có kinh nghiệm nào. Nhấn "Thêm kinh nghiệm" để bắt đầu.</p>
                                    )}
                                    {(cvData.experience || []).map((exp: any, idx: number) => (
                                        <div key={idx} className="bg-slate-950/40 border border-white/5 rounded-xl p-4 space-y-3">
                                            <div className="flex justify-between items-center">
                                                <span className="text-xs font-bold text-slate-400">Mục #{idx + 1}</span>
                                                <button onClick={() => removeArrayItem('experience', idx)} className="text-red-400 hover:text-red-300 p-1 rounded"><Trash2 className="w-3.5 h-3.5" /></button>
                                            </div>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                                <Field label="Vị trí">
                                                    <input className={inputClass} placeholder="Backend Developer" value={exp.position || ''} onChange={e => updateArrayItem('experience', idx, { position: e.target.value })} />
                                                </Field>
                                                <Field label="Công ty">
                                                    <input className={inputClass} placeholder="FPT Software" value={exp.company || ''} onChange={e => updateArrayItem('experience', idx, { company: e.target.value })} />
                                                </Field>
                                                <Field label="Bắt đầu">
                                                    <input className={inputClass} placeholder="2022-01" value={exp.start_date || ''} onChange={e => updateArrayItem('experience', idx, { start_date: e.target.value })} />
                                                </Field>
                                                <Field label="Kết thúc">
                                                    <input className={inputClass} placeholder="Hiện tại / 2024-06" value={exp.end_date || ''} onChange={e => updateArrayItem('experience', idx, { end_date: e.target.value })} />
                                                </Field>
                                            </div>
                                            <Field label="Bullet points mô tả công việc">
                                                <div className="space-y-2">
                                                    {(exp.description || []).map((pt: string, di: number) => (
                                                        <div key={di} className="flex gap-2">
                                                            <span className="text-accent-primary mt-2">•</span>
                                                            <textarea className={textareaClass + " !min-h-[50px]"} value={pt} onChange={e => {
                                                                const desc = [...(exp.description || [])];
                                                                desc[di] = e.target.value;
                                                                updateArrayItem('experience', idx, { description: desc });
                                                            }} />
                                                            <button onClick={() => {
                                                                const desc = (exp.description || []).filter((_: any, i: number) => i !== di);
                                                                updateArrayItem('experience', idx, { description: desc });
                                                            }} className="text-red-400 hover:text-red-300 p-1 h-fit mt-1"><Trash2 className="w-3 h-3" /></button>
                                                        </div>
                                                    ))}
                                                    <button onClick={() => updateArrayItem('experience', idx, { description: [...(exp.description || []), ''] })}
                                                        className="text-xs text-slate-400 hover:text-white flex items-center gap-1"><Plus className="w-3 h-3" /> Thêm bullet</button>
                                                </div>
                                            </Field>
                                            <div className="pt-2 border-t border-white/5">
                                                <button onClick={() => { setSuggestTargetIdx(idx); setRawExpInput(''); setSuggestions([]); }}
                                                    className="text-xs font-bold text-accent-primary hover:underline">Dùng AI tạo bullet points cho mục này →</button>
                                            </div>
                                        </div>
                                    ))}
                                    <button onClick={() => addArrayItem('experience', { company: '', position: '', location: '', start_date: '', end_date: '', description: [] })}
                                        className="w-full py-2 border border-dashed border-white/10 rounded-lg text-xs font-bold text-slate-400 hover:bg-white/5 hover:text-white transition-all flex items-center justify-center gap-1.5">
                                        <Plus className="w-3.5 h-3.5" /> Thêm kinh nghiệm
                                    </button>
                                </SectionCard>

                                <SectionCard title="AI Bullet Point Generator" icon={<Bot className="w-4 h-4 text-accent-primary" />}>
                                    <p className="text-xs text-slate-400">
                                        Mô tả ngắn gọn công việc bạn đã làm ở mục <strong>#{suggestTargetIdx + 1}</strong> — AI sẽ sinh ra các bullet points chuẩn STAR.
                                    </p>
                                    <textarea
                                        value={rawExpInput}
                                        onChange={e => setRawExpInput(e.target.value)}
                                        placeholder="Ví dụ: Làm backend ở FPT Software 2 năm, dùng .NET Core và SQL Server..."
                                        className={textareaClass}
                                    />
                                    <button
                                        onClick={() => handleGetSuggestions(suggestTargetIdx)}
                                        disabled={!rawExpInput.trim() || isSuggesting || !cvData.experience[suggestTargetIdx]}
                                        className="flex items-center gap-2 px-4 py-2 bg-accent-primary/20 hover:bg-accent-primary/30 border border-accent-primary/30 text-accent-primary rounded-xl text-xs font-bold transition-all disabled:opacity-50"
                                    >
                                        <Sparkles className="w-3.5 h-3.5" />
                                        {isSuggesting ? "Đang tạo gợi ý..." : "Gợi ý bullet points"}
                                    </button>
                                    {(suggestions.length > 0 || isSuggesting) && (
                                        <AISuggestionCards suggestions={suggestions} isLoading={isSuggesting} onSelect={handleSuggestionSelect} />
                                    )}
                                </SectionCard>
                            </>
                        )}

                        {/* STEP 4: Skills autocomplete */}
                        {currentStep === 4 && (
                            <SectionCard title="Kỹ năng — Auto-complete từ Skill Ontology">
                                <SkillAutocompleteInput
                                    selectedSkills={cvData.skills}
                                    onChange={(skills) => commitCv({ ...cvData, skills })}
                                    jobTitle={cvData.personal_info.title}
                                />
                                <ValidationMessage warning={cvData.skills.length > 0 && cvData.skills.length < 3 ? "Nên có ít nhất 3 kỹ năng để CV được đánh giá cao" : null} />
                            </SectionCard>
                        )}

                        {/* STEP 5: Projects */}
                        {currentStep === 5 && (
                            <SectionCard title="Dự án">
                                {(cvData.projects || []).length === 0 && (
                                    <p className="text-xs text-slate-500 italic">Chưa có dự án nào. Nhấn "Thêm dự án" để bắt đầu.</p>
                                )}
                                {(cvData.projects || []).map((proj: any, idx: number) => (
                                    <div key={idx} className="bg-slate-950/40 border border-white/5 rounded-xl p-4 space-y-3">
                                        <div className="flex justify-between items-center">
                                            <span className="text-xs font-bold text-slate-400">Dự án #{idx + 1}</span>
                                            <button onClick={() => removeArrayItem('projects', idx)} className="text-red-400 hover:text-red-300 p-1 rounded"><Trash2 className="w-3.5 h-3.5" /></button>
                                        </div>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                            <Field label="Tên dự án">
                                                <input className={inputClass} placeholder="E-commerce Platform" value={proj.name || ''} onChange={e => updateArrayItem('projects', idx, { name: e.target.value })} />
                                            </Field>
                                            <Field label="Link (tùy chọn)">
                                                <input className={inputClass} placeholder="https://github.com/..." value={proj.link || ''} onChange={e => updateArrayItem('projects', idx, { link: e.target.value })} />
                                            </Field>
                                            <Field label="Công nghệ">
                                                <input className={inputClass} placeholder="React, Node.js, PostgreSQL (phân cách bằng dấu phẩy)"
                                                    value={(proj.technologies || []).join(', ')}
                                                    onChange={e => updateArrayItem('projects', idx, { technologies: e.target.value.split(',').map((s: string) => s.trim()).filter(Boolean) })} />
                                            </Field>
                                        </div>
                                        <Field label="Mô tả">
                                            <div className="space-y-2">
                                                {(proj.description || []).map((pt: string, di: number) => (
                                                    <div key={di} className="flex gap-2">
                                                        <span className="text-accent-primary mt-2">•</span>
                                                        <textarea className={textareaClass + " !min-h-[50px]"} value={pt} onChange={e => {
                                                            const desc = [...(proj.description || [])];
                                                            desc[di] = e.target.value;
                                                            updateArrayItem('projects', idx, { description: desc });
                                                        }} />
                                                        <button onClick={() => {
                                                            const desc = (proj.description || []).filter((_: any, i: number) => i !== di);
                                                            updateArrayItem('projects', idx, { description: desc });
                                                        }} className="text-red-400 hover:text-red-300 p-1 h-fit mt-1"><Trash2 className="w-3 h-3" /></button>
                                                    </div>
                                                ))}
                                                <button onClick={() => updateArrayItem('projects', idx, { description: [...(proj.description || []), ''] })}
                                                    className="text-xs text-slate-400 hover:text-white flex items-center gap-1"><Plus className="w-3 h-3" /> Thêm bullet</button>
                                            </div>
                                        </Field>
                                    </div>
                                ))}
                                <button onClick={() => addArrayItem('projects', { name: '', description: [], technologies: [], link: '' })}
                                    className="w-full py-2 border border-dashed border-white/10 rounded-lg text-xs font-bold text-slate-400 hover:bg-white/5 hover:text-white transition-all flex items-center justify-center gap-1.5">
                                    <Plus className="w-3.5 h-3.5" /> Thêm dự án
                                </button>
                            </SectionCard>
                        )}

                        {/* STEP 6: Certifications */}
                        {currentStep === 6 && (
                            <SectionCard title="Chứng chỉ">
                                {(cvData.certifications || []).length === 0 && (
                                    <p className="text-xs text-slate-500 italic">Bước này có thể bỏ qua nếu bạn chưa có chứng chỉ.</p>
                                )}
                                {(cvData.certifications || []).map((cert: any, idx: number) => (
                                    <div key={idx} className="bg-slate-950/40 border border-white/5 rounded-xl p-4 space-y-3">
                                        <div className="flex justify-between items-center">
                                            <span className="text-xs font-bold text-slate-400">Chứng chỉ #{idx + 1}</span>
                                            <button onClick={() => removeArrayItem('certifications', idx)} className="text-red-400 hover:text-red-300 p-1 rounded"><Trash2 className="w-3.5 h-3.5" /></button>
                                        </div>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                            <Field label="Tên chứng chỉ">
                                                <input className={inputClass} placeholder="AWS Certified Solutions Architect" value={cert.name || ''} onChange={e => updateArrayItem('certifications', idx, { name: e.target.value })} />
                                            </Field>
                                            <Field label="Tổ chức cấp">
                                                <input className={inputClass} placeholder="Amazon Web Services" value={cert.organization || ''} onChange={e => updateArrayItem('certifications', idx, { organization: e.target.value })} />
                                            </Field>
                                            <Field label="Ngày cấp">
                                                <input className={inputClass} placeholder="2024-01" value={cert.issue_date || ''} onChange={e => updateArrayItem('certifications', idx, { issue_date: e.target.value })} />
                                            </Field>
                                            <Field label="Ngày hết hạn (tùy chọn)">
                                                <input className={inputClass} placeholder="2027-01" value={cert.expiry_date || ''} onChange={e => updateArrayItem('certifications', idx, { expiry_date: e.target.value })} />
                                            </Field>
                                        </div>
                                    </div>
                                ))}
                                <button onClick={() => addArrayItem('certifications', { name: '', organization: '', issue_date: '', expiry_date: '' })}
                                    className="w-full py-2 border border-dashed border-white/10 rounded-lg text-xs font-bold text-slate-400 hover:bg-white/5 hover:text-white transition-all flex items-center justify-center gap-1.5">
                                    <Plus className="w-3.5 h-3.5" /> Thêm chứng chỉ
                                </button>
                            </SectionCard>
                        )}
                    </div>
                )}
            </div>

            {/* Footer: autosave indicator */}
            {userId && lastSavedAt && (
                <div className="px-6 py-2 border-t border-white/5 text-[10px] text-slate-500 bg-slate-950/40 flex items-center gap-2">
                    <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                    Đã lưu nháp tự động lúc {lastSavedAt}
                </div>
            )}

            <TemplatePickerModal
                isOpen={templatePickerOpen}
                currentTemplateId={selectedTemplate?.id}
                onClose={() => setTemplatePickerOpen(false)}
                onConfirm={handleTemplateConfirm}
            />
        </div>
    );
};

export default CVBuilderView;
