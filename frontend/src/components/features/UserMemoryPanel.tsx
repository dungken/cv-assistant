import React, { useEffect, useMemo, useState } from 'react';
import { Brain, Save, Trash2, X, RotateCcw, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { MemoryUpdatePayload, memoryApi, UserMemory, userApi } from '../../services/api';

interface UserMemoryPanelProps {
    userId: string;
    userName: string;
    onClose: () => void;
    onProfileSynced?: (payload: { name?: string; language?: string; email?: string }) => void;
}

const parseList = (raw: string): string[] =>
    raw
        .split(',')
        .map((v) => v.trim())
        .filter(Boolean);

const UserMemoryPanel: React.FC<UserMemoryPanelProps> = ({ userId, userName, onClose, onProfileSynced }) => {
    const { t } = useTranslation();
    const [memory, setMemory] = useState<UserMemory | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const [displayName, setDisplayName] = useState('');
    const [tone, setTone] = useState<'professional' | 'casual'>('professional');
    const [language, setLanguage] = useState<'vi' | 'en'>('vi');
    const [currentRole, setCurrentRole] = useState('');
    const [targetRole, setTargetRole] = useState('');
    const [timelineMonths, setTimelineMonths] = useState('');
    const [currentSkillsText, setCurrentSkillsText] = useState('');
    const [skillGapsText, setSkillGapsText] = useState('');

    const loadMemory = async () => {
        setLoading(true);
        setError('');
        try {
            const res = await memoryApi.get(userId);
            const data = res.data;
            setMemory(data);
            setDisplayName(data.display_name || '');
            setTone((data.tone_preference === 'casual' ? 'casual' : 'professional'));
            setLanguage(data.language === 'en' ? 'en' : 'vi');
            setCurrentRole(data.career_profile?.current_role || '');
            setTargetRole(data.career_profile?.target_role || '');
            setTimelineMonths(data.career_profile?.timeline_months ? String(data.career_profile.timeline_months) : '');
            setCurrentSkillsText((data.career_profile?.current_skills || []).join(', '));
            setSkillGapsText((data.skill_gaps || []).join(', '));
        } catch {
            setError(t('memory.load_error'));
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadMemory();
    }, [userId]);

    const lastUpdated = useMemo(() => {
        if (!memory?.updated_at) return '-';
        const date = new Date(memory.updated_at);
        if (Number.isNaN(date.getTime())) return memory.updated_at;
        return date.toLocaleString();
    }, [memory]);

    const handleSave = async () => {
        setSaving(true);
        setError('');
        setSuccess('');
        try {
            const payload: MemoryUpdatePayload = {
                display_name: displayName || null,
                tone_preference: tone,
                language,
                career_profile: {
                    current_role: currentRole || undefined,
                    target_role: targetRole || undefined,
                    timeline_months: timelineMonths ? Number(timelineMonths) : undefined,
                    current_skills: parseList(currentSkillsText),
                },
                skill_gaps: parseList(skillGapsText),
            };

            const res = await memoryApi.update(userId, payload);
            setMemory(res.data);

            // Two-way sync: memory -> profile (safe fields only)
            try {
                const profileRes = await userApi.getProfile();
                const profile = profileRes.data;
                await userApi.updateProfile({
                    name: displayName?.trim() || profile.name,
                    preferences: {
                        ...(profile.preferences || {}),
                        language
                    }
                });
                onProfileSynced?.({ name: displayName?.trim() || profile.name, language, email: profile.email });
            } catch {
                // Memory save should not fail because profile sync failed
            }

            setSuccess(t('memory.save_success'));
        } catch {
            setError(t('memory.save_error'));
        } finally {
            setSaving(false);
        }
    };

    const handleResetField = async (field: string) => {
        setError('');
        setSuccess('');
        try {
            await memoryApi.deleteField(userId, field);
            await loadMemory();
            setSuccess(t('memory.reset_success'));
        } catch {
            setError(t('memory.save_error'));
        }
    };

    const handleDeleteAll = async () => {
        const ok = window.confirm(t('memory.delete_all_confirm'));
        if (!ok) return;
        setError('');
        setSuccess('');
        try {
            await memoryApi.deleteAll(userId);
            await loadMemory();
            setSuccess(t('memory.delete_all_success'));
        } catch {
            setError(t('memory.save_error'));
        }
    };

    return (
        <div className="fixed inset-0 z-50 bg-canvas/70 backdrop-blur-sm flex justify-end animate-in fade-in duration-200">
            <div className="h-full w-full max-w-2xl bg-surface border-l border-white/10 shadow-2xl flex flex-col">
                <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-xl bg-accent-primary/20 flex items-center justify-center text-accent-primary">
                            <Brain className="w-5 h-5" />
                        </div>
                        <div>
                            <h2 className="text-lg font-black tracking-tight">{t('memory.title')}</h2>
                            <p className="text-xs text-text-secondary">{t('memory.subtitle', { name: userName || userId })}</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 rounded-xl hover:bg-surface-hover text-text-secondary">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {loading ? (
                    <div className="flex-1 flex items-center justify-center text-text-secondary gap-2">
                        <Loader2 className="w-5 h-5 animate-spin" />
                        <span>{t('memory.loading')}</span>
                    </div>
                ) : (
                    <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <label className="space-y-1">
                                <span className="text-xs font-bold uppercase tracking-wider text-text-secondary">{t('memory.fields.display_name')}</span>
                                <div className="flex gap-2">
                                    <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} className="w-full bg-secondary/50 rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-accent-primary/25" />
                                    <button onClick={() => handleResetField('display_name')} className="px-2 rounded-xl bg-secondary/50 hover:bg-surface-hover" title={t('memory.forget_field')}>
                                        <Trash2 className="w-4 h-4 text-text-secondary" />
                                    </button>
                                </div>
                            </label>

                            <label className="space-y-1">
                                <span className="text-xs font-bold uppercase tracking-wider text-text-secondary">{t('memory.fields.tone')}</span>
                                <div className="grid grid-cols-[1fr_auto] gap-2">
                                    <select value={tone} onChange={(e) => setTone(e.target.value as 'professional' | 'casual')} className="w-full bg-secondary/50 rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-accent-primary/25">
                                        <option value="professional">{t('memory.tone.professional')}</option>
                                        <option value="casual">{t('memory.tone.casual')}</option>
                                    </select>
                                    <button onClick={() => handleResetField('tone_preference')} className="px-2 rounded-xl bg-secondary/50 hover:bg-surface-hover" title={t('memory.forget_field')}>
                                        <Trash2 className="w-4 h-4 text-text-secondary" />
                                    </button>
                                </div>
                            </label>

                            <label className="space-y-1 md:col-span-2">
                                <span className="text-xs font-bold uppercase tracking-wider text-text-secondary">{t('memory.fields.language')}</span>
                                <div className="grid grid-cols-[1fr_auto] gap-2">
                                    <select value={language} onChange={(e) => setLanguage(e.target.value as 'vi' | 'en')} className="w-full bg-secondary/50 rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-accent-primary/25">
                                        <option value="vi">Tiếng Việt</option>
                                        <option value="en">English</option>
                                    </select>
                                    <button onClick={() => handleResetField('language')} className="px-2 rounded-xl bg-secondary/50 hover:bg-surface-hover" title={t('memory.forget_field')}>
                                        <Trash2 className="w-4 h-4 text-text-secondary" />
                                    </button>
                                </div>
                            </label>

                            <label className="space-y-1">
                                <span className="text-xs font-bold uppercase tracking-wider text-text-secondary">{t('memory.fields.current_role')}</span>
                                <input value={currentRole} onChange={(e) => setCurrentRole(e.target.value)} className="w-full bg-secondary/50 rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-accent-primary/25" />
                            </label>

                            <label className="space-y-1">
                                <span className="text-xs font-bold uppercase tracking-wider text-text-secondary">{t('memory.fields.target_role')}</span>
                                <input value={targetRole} onChange={(e) => setTargetRole(e.target.value)} className="w-full bg-secondary/50 rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-accent-primary/25" />
                            </label>

                            <label className="space-y-1 md:col-span-2">
                                <span className="text-xs font-bold uppercase tracking-wider text-text-secondary">{t('memory.fields.timeline_months')}</span>
                                <input
                                    type="number"
                                    min={0}
                                    value={timelineMonths}
                                    onChange={(e) => setTimelineMonths(e.target.value)}
                                    className="w-full bg-secondary/50 rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-accent-primary/25"
                                />
                            </label>

                            <label className="space-y-1 md:col-span-2">
                                <span className="text-xs font-bold uppercase tracking-wider text-text-secondary">{t('memory.fields.current_skills')}</span>
                                <div className="grid grid-cols-[1fr_auto] gap-2">
                                    <textarea value={currentSkillsText} onChange={(e) => setCurrentSkillsText(e.target.value)} rows={2} placeholder={t('memory.placeholder_csv')} className="w-full bg-secondary/50 rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-accent-primary/25 resize-none" />
                                    <button onClick={() => handleResetField('career_profile.current_skills')} className="px-2 rounded-xl bg-secondary/50 hover:bg-surface-hover h-fit" title={t('memory.forget_field')}>
                                        <Trash2 className="w-4 h-4 text-text-secondary" />
                                    </button>
                                </div>
                            </label>

                            <label className="space-y-1 md:col-span-2">
                                <span className="text-xs font-bold uppercase tracking-wider text-text-secondary">{t('memory.fields.skill_gaps')}</span>
                                <div className="grid grid-cols-[1fr_auto] gap-2">
                                    <textarea value={skillGapsText} onChange={(e) => setSkillGapsText(e.target.value)} rows={2} placeholder={t('memory.placeholder_csv')} className="w-full bg-secondary/50 rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-accent-primary/25 resize-none" />
                                    <button onClick={() => handleResetField('skill_gaps')} className="px-2 rounded-xl bg-secondary/50 hover:bg-surface-hover h-fit" title={t('memory.forget_field')}>
                                        <Trash2 className="w-4 h-4 text-text-secondary" />
                                    </button>
                                </div>
                            </label>
                        </div>

                        <div className="rounded-xl bg-secondary/30 p-3 text-xs text-text-secondary">
                            {t('memory.updated_at')}: <span className="text-text-primary font-medium">{lastUpdated}</span>
                        </div>

                        {error && <div className="rounded-xl bg-red-500/10 text-red-400 px-3 py-2 text-sm">{error}</div>}
                        {success && <div className="rounded-xl bg-emerald-500/10 text-emerald-400 px-3 py-2 text-sm">{success}</div>}
                    </div>
                )}

                <div className="px-6 py-4 border-t border-white/10 flex flex-wrap items-center gap-2 justify-between">
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => handleResetField('career_profile')}
                            className="inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-secondary/50 hover:bg-surface-hover text-sm"
                        >
                            <RotateCcw className="w-4 h-4" />
                            {t('memory.reset_profile')}
                        </button>
                        <button
                            onClick={handleDeleteAll}
                            className="inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 text-sm"
                        >
                            <Trash2 className="w-4 h-4" />
                            {t('memory.delete_all')}
                        </button>
                    </div>

                    <button
                        onClick={handleSave}
                        disabled={loading || saving}
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-accent-primary text-white font-bold disabled:opacity-60"
                    >
                        {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                        {saving ? t('memory.saving') : t('memory.save')}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default UserMemoryPanel;
