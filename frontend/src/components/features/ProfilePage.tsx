import React, { useState, useEffect, useRef } from 'react';
import { 
    User, Mail, Phone, FileText, Camera, Lock, Trash2, 
    Save, X, Check, Globe, Briefcase, TrendingUp, 
    BarChart3, Activity, Shield, RefreshCw 
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { memoryApi, userApi, UserProfile, UserPreferences } from '../../services/api';
import { cn } from '../../lib/utils';
import { Toast } from '../ui/Toast';
import { CustomSelect } from '../ui/Select';
import { AnimatePresence } from 'framer-motion';

interface ProfilePageProps {
    onClose: () => void;
    onLogout: () => void;
    onProfileUpdated?: (payload: { name?: string; language?: string; email?: string }) => void;
}

const ProfilePage: React.FC<ProfilePageProps> = ({ onClose, onLogout, onProfileUpdated }) => {
    const { t } = useTranslation();
    const [profile, setProfile] = useState<UserProfile | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

    // Tabs
    const [activeTab, setActiveTab] = useState<'profile' | 'preferences' | 'activity' | 'security'>('profile');

    // Edit fields
    const [name, setName] = useState('');
    const [bio, setBio] = useState('');
    const [phone, setPhone] = useState('');
    const [language, setLanguage] = useState('vi');
    const [industry, setIndustry] = useState('');
    const [careerLevel, setCareerLevel] = useState('');

    // Change password
    const [showPasswordForm, setShowPasswordForm] = useState(false);
    const [oldPassword, setOldPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');

    // Delete account
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [deletePassword, setDeletePassword] = useState('');

    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => { loadProfile(); }, []);

    const loadProfile = async () => {
        try {
            const res = await userApi.getProfile();
            setProfile(res.data);
            setName(res.data.name || '');
            setBio(res.data.bio || '');
            setPhone(res.data.phone || '');
            setLanguage(res.data.preferences?.language || 'vi');
            setIndustry(res.data.preferences?.industry || '');
            setCareerLevel(res.data.preferences?.careerLevel || '');
        } catch {
            setToast({ message: 'Không thể tải thông tin cá nhân', type: 'error' });
        } finally {
            setIsLoading(false);
        }
    };

    const handleSave = async () => {
        setToast(null); setIsSaving(true);
        try {
            const preferences: UserPreferences = { language, industry, careerLevel };
            const res = await userApi.updateProfile({ name, bio, phone, preferences });
            setProfile(res.data);

            // Two-way sync: profile -> chatbot memory
            try {
                await memoryApi.update(res.data.email, {
                    display_name: name?.trim() || null,
                    language: language || 'vi',
                    career_profile: {
                        current_role: careerLevel || undefined
                    }
                });
            } catch {
                // Keep profile save successful even if memory sync fails
            }

            onProfileUpdated?.({ name: res.data.name, language, email: res.data.email });
            setToast({ message: t('profile.save_success'), type: 'success' });
        } catch (err: any) {
            setToast({ message: err.response?.data?.error || t('profile.save_error'), type: 'error' });
        } finally {
            setIsSaving(false);
        }
    };

    const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        setToast(null);
        try {
            const res = await userApi.uploadAvatar(file);
            setProfile(res.data);
            setToast({ message: t('profile.avatar_success'), type: 'success' });
        } catch (err: any) {
            setToast({ message: err.response?.data?.error || t('profile.avatar_error'), type: 'error' });
        }
    };

    const handleChangePassword = async (e: React.FormEvent) => {
        e.preventDefault();
        setToast(null);
        if (newPassword !== confirmPassword) { setToast({ message: t('profile.password_mismatch'), type: 'error' }); return; }
        if (newPassword.length < 8) { setToast({ message: t('profile.password_min'), type: 'error' }); return; }
        try {
            await userApi.changePassword(oldPassword, newPassword);
            setToast({ message: t('profile.password_success'), type: 'success' });
            setShowPasswordForm(false);
            setOldPassword(''); setNewPassword(''); setConfirmPassword('');
        } catch (err: any) {
            setToast({ message: err.response?.data?.error || t('profile.password_error'), type: 'error' });
        }
    };

    const handleDeleteAccount = async () => {
        setToast(null);
        try {
            await userApi.deleteAccount(deletePassword);
            onLogout();
        } catch (err: any) {
            setToast({ message: err.response?.data?.error || t('profile.delete_error'), type: 'error' });
        }
    };

    if (isLoading) {
        return (
            <div className="fixed inset-0 z-50 bg-canvas/80 backdrop-blur-sm flex items-center justify-center">
                <div className="w-8 h-8 border-2 border-accent-primary/30 border-t-accent-primary rounded-full animate-spin"></div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 z-50 bg-canvas/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-300">
            <div className="w-full max-w-2xl bg-surface rounded-[2.5rem] shadow-2xl border border-white/10 overflow-hidden relative flex flex-col min-h-[500px]">
                {/* Header */}
                <div className="px-8 pt-8 pb-4 flex items-center justify-between">
                    <h2 className="text-2xl font-black tracking-tighter">Profile</h2>
                    <button onClick={onClose} className="p-2 rounded-xl hover:bg-secondary/50 transition-colors">
                        <X className="w-5 h-5 text-text-secondary" />
                    </button>
                </div>

                {/* Tabs Navigation */}
                <div className="px-8 pb-4 flex items-center gap-1 border-b border-white/5">
                    {[
                        { id: 'profile', label: 'General', icon: User },
                        { id: 'preferences', label: 'Preferences', icon: Globe },
                        { id: 'activity', label: 'Activity', icon: Activity },
                        { id: 'security', label: 'Account', icon: Shield }
                    ].map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as any)}
                            className={cn(
                                "flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all duration-300",
                                activeTab === tab.id 
                                    ? "bg-text-primary text-secondary shadow-lg shadow-black/20" 
                                    : "text-text-secondary hover:bg-surface-hover hover:text-text-primary hover:shadow-sm"
                            )}
                        >
                            <tab.icon className="w-4 h-4" strokeWidth={2} />
                            {tab.label}
                        </button>
                    ))}
                </div>

                <div className="flex-1 overflow-y-auto floating-scrollbar px-8 py-8 scroll-smooth">
                    {/* Tab Content: Profile */}
                    {activeTab === 'profile' && (
                        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
                            <div className="flex items-center gap-8">
                                <div className="relative group">
                                    <div className="w-24 h-24 rounded-[2rem] bg-surface-hover flex items-center justify-center text-text-primary text-3xl font-black overflow-hidden ring-1 ring-white/10 shadow-xl shadow-black/40">
                                        {profile?.avatarUrl ? (
                                            <img src={profile.avatarUrl} alt="Avatar" className="w-full h-full object-cover" />
                                        ) : (
                                            profile?.name?.charAt(0)?.toUpperCase() || 'U'
                                        )}
                                    </div>
                                    <button onClick={() => fileInputRef.current?.click()}
                                        className="absolute -bottom-1 -right-1 w-10 h-10 bg-text-primary rounded-full flex items-center justify-center shadow-lg hover:scale-110 active:scale-95 transition-all text-secondary">
                                        <Camera className="w-5 h-5" />
                                    </button>
                                    <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleAvatarUpload} />
                                </div>
                                <div className="space-y-1">
                                    <h3 className="text-xl font-black text-text-primary tracking-tight">{profile?.name}</h3>
                                    <p className="text-sm font-medium text-text-secondary">{profile?.email}</p>
                                    <div className="flex items-center gap-2 mt-2">
                                        {profile?.isEmailVerified ? (
                                            <span className="text-[10px] font-black uppercase tracking-widest text-emerald-500 bg-emerald-500/10 px-3 py-1 rounded-full flex items-center gap-1.5"><Check className="w-3 h-3" /> VERIFIED</span>
                                        ) : (
                                            <span className="text-[10px] font-black uppercase tracking-widest text-amber-500 bg-amber-500/10 px-3 py-1 rounded-full">UNVERIFIED</span>
                                        )}
                                        <span className="text-[10px] font-bold text-text-muted/40 uppercase tracking-widest ml-1">Member since {profile?.createdAt ? new Date(profile.createdAt).getFullYear() : ''}</span>
                                    </div>
                                </div>
                            </div>

                            <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="space-y-2">
                                    <label className="text-[11px] font-black text-text-muted/60 uppercase tracking-widest ml-1">Full Name</label>
                                    <div className="relative">
                                        <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted/40" />
                                        <input type="text" value={name} onChange={(e) => setName(e.target.value)}
                                            className="w-full bg-secondary/50 text-text-primary rounded-2xl pl-12 pr-4 py-3.5 outline-none focus:ring-2 focus:ring-white/10 transition-all text-sm font-bold shadow-sm ring-1 ring-white/5" />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-[11px] font-black text-text-muted/60 uppercase tracking-widest ml-1">Phone Number</label>
                                    <div className="relative">
                                        <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted/40" />
                                        <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="0901234567"
                                            className="w-full bg-secondary/50 text-text-primary rounded-2xl pl-12 pr-4 py-3.5 outline-none focus:ring-2 focus:ring-white/10 transition-all text-sm font-bold placeholder:text-text-muted/20 shadow-sm ring-1 ring-white/5" />
                                    </div>
                                </div>
                                <div className="space-y-2 md:col-span-2">
                                    <label className="text-[11px] font-black text-text-muted/60 uppercase tracking-widest ml-1">Bio / Headline</label>
                                    <div className="relative">
                                        <FileText className="absolute left-4 top-4 w-4 h-4 text-text-muted/40" />
                                        <textarea value={bio} onChange={(e) => setBio(e.target.value)} rows={3} placeholder="Tell us about yourself..."
                                            className="w-full bg-secondary/50 text-text-primary rounded-2xl pl-12 pr-4 py-3.5 outline-none focus:ring-2 focus:ring-white/10 transition-all text-sm font-bold resize-none placeholder:text-text-muted/20 shadow-sm ring-1 ring-white/5" />
                                    </div>
                                </div>
                            </section>
                        </div>
                    )}

                    {/* Tab Content: Preferences */}
                    {activeTab === 'preferences' && (
                        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
                             <div className="space-y-6">
                                <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="space-y-2">
                                        <label className="text-[11px] font-black text-text-muted/60 uppercase tracking-widest ml-1">Interface Language</label>
                                        <CustomSelect 
                                            value={language} 
                                            onChange={setLanguage}
                                            options={[
                                                { value: 'vi', label: 'Tiếng Việt' },
                                                { value: 'en', label: 'English (US)' }
                                            ]}
                                            icon={Globe}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[11px] font-black text-text-muted/60 uppercase tracking-widest ml-1">Primary Industry</label>
                                        <CustomSelect 
                                            value={industry} 
                                            onChange={setIndustry}
                                            options={[
                                                { value: '', label: 'Select industry...' },
                                                { value: 'IT', label: 'IT / Software / AI' },
                                                { value: 'Finance', label: 'Finance & Banking' },
                                                { value: 'Marketing', label: 'Marketing / Digital' },
                                                { value: 'Education', label: 'Education / EdTech' },
                                                { value: 'Healthcare', label: 'Healthcare / Bio' },
                                                { value: 'Other', label: 'Other Category' }
                                            ]}
                                            icon={Briefcase}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[11px] font-black text-text-muted/60 uppercase tracking-widest ml-1">Career Level</label>
                                        <CustomSelect 
                                            value={careerLevel} 
                                            onChange={setCareerLevel}
                                            options={[
                                                { value: '', label: 'Select level...' },
                                                { value: 'intern', label: 'Internship' },
                                                { value: 'junior', label: 'Junior Associate' },
                                                { value: 'junior-mid', label: 'Intermediate' },
                                                { value: 'mid', label: 'Mid-Senior' },
                                                { value: 'senior', label: 'Senior Specialist' },
                                                { value: 'lead', label: 'Management / Lead' }
                                            ]}
                                            icon={TrendingUp}
                                        />
                                    </div>
                                </section>
                             </div>
                        </div>
                    )}

                    {/* Tab Content: Activity */}
                    {activeTab === 'activity' && (
                        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
                             <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                                {[
                                    { label: 'CVs Created', value: profile?.stats?.cvsCreated || 0, icon: FileText, color: 'text-text-primary' },
                                    { label: 'Analyses', value: profile?.stats?.analysesDone || 0, icon: BarChart3, color: 'text-text-primary' },
                                    { label: 'Bookmarks', value: profile?.stats?.coursesBookmarked || 0, icon: TrendingUp, color: 'text-text-primary' },
                                ].map((stat) => (
                                    <div key={stat.label} className="bg-secondary/40 rounded-[2rem] p-8 text-center ring-1 ring-white/5 shadow-xl shadow-black/10">
                                        <stat.icon className={cn("w-6 h-6 mx-auto mb-4", stat.color)} strokeWidth={2.5} />
                                        <p className="text-4xl font-black text-text-primary mb-1 font-outfit">{stat.value}</p>
                                        <p className="text-[10px] font-black text-text-muted/50 uppercase tracking-[0.2em]">{stat.label}</p>
                                    </div>
                                ))}
                            </div>
                            <div className="p-8 rounded-[2rem] bg-secondary/20 border border-white/5 text-center">
                                <Activity className="w-8 h-8 text-text-muted/20 mx-auto mb-4" />
                                <p className="text-sm font-bold text-text-secondary">AI engagement logic is active. Keep creating CVs to build your history.</p>
                            </div>
                        </div>
                    )}

                    {/* Tab Content: Security */}
                    {activeTab === 'security' && (
                        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
                             <div className="space-y-6">
                                <div className="p-6 rounded-[2rem] bg-secondary/30 border border-white/5 space-y-4">
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 rounded-xl bg-text-primary/5 flex items-center justify-center">
                                            <Lock className="w-5 h-5 text-text-primary" />
                                        </div>
                                        <h4 className="text-lg font-bold">Security Settings</h4>
                                    </div>
                                    <p className="text-xs text-text-muted font-medium px-1">Manage your access credentials and account status.</p>
                                    
                                    <div className="flex gap-3 pt-2">
                                        <button onClick={() => setShowPasswordForm(!showPasswordForm)}
                                            className="flex-1 bg-surface-hover border border-white/10 text-text-primary font-black text-xs py-4 px-6 rounded-2xl hover:bg-secondary hover:shadow-lg transition-all duration-300 flex items-center justify-center gap-2">
                                            <RefreshCw className="w-4 h-4" /> CHANGE PASSWORD
                                        </button>
                                        <button onClick={() => setShowDeleteConfirm(!showDeleteConfirm)}
                                            className="flex-1 bg-red-500/10 text-red-500 font-black text-xs py-4 px-6 rounded-2xl hover:bg-red-500/20 hover:shadow-lg transition-all duration-300 flex items-center justify-center gap-2">
                                            <Trash2 className="w-4 h-4" /> DELETE ACCOUNT
                                        </button>
                                    </div>
                                </div>

                                {/* Password Form Overlay/Inline */}
                                {showPasswordForm && (
                                    <form onSubmit={handleChangePassword} className="space-y-4 bg-secondary/40 rounded-[2rem] p-8 animate-in slide-in-from-top-4 duration-500 border border-white/5">
                                        <h4 className="text-base font-black tracking-tight">Security Update</h4>
                                        <input type="password" value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} placeholder="Current password"
                                            className="w-full bg-secondary/50 text-text-primary rounded-2xl px-5 py-4 outline-none focus:ring-2 focus:ring-white/10 text-sm font-bold placeholder:text-text-muted/20 shadow-sm ring-1 ring-white/5" required />
                                        <div className="grid grid-cols-2 gap-4">
                                            <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} placeholder="New password" minLength={8}
                                                className="w-full bg-secondary/50 text-text-primary rounded-2xl px-5 py-4 outline-none focus:ring-2 focus:ring-white/10 text-sm font-bold placeholder:text-text-muted/20 shadow-sm ring-1 ring-white/5" required />
                                            <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="Repeat password" minLength={8}
                                                className="w-full bg-secondary/50 text-text-primary rounded-2xl px-5 py-4 outline-none focus:ring-2 focus:ring-white/10 text-sm font-bold placeholder:text-text-muted/20 shadow-sm ring-1 ring-white/5" required />
                                        </div>
                                        <div className="flex justify-end">
                                            <button type="submit" className="bg-text-primary text-secondary font-black text-[13px] py-3.5 px-8 rounded-2xl hover:bg-text-primary/90 hover:shadow-xl transition-all duration-300 uppercase tracking-widest active:scale-95 flex items-center gap-2">
                                                <Save className="w-4 h-4" /> {t('profile.update')}
                                            </button>
                                        </div>
                                    </form>
                                )}

                                {showDeleteConfirm && (
                                    <div className="space-y-4 bg-red-500/5 border border-red-500/20 rounded-[2rem] p-8 animate-in zoom-in-95 duration-500">
                                        <h4 className="text-base font-black text-red-500">Confirm Soft Deletion</h4>
                                        <p className="text-xs text-text-muted font-medium">This will deactivate your neural sessions. Recovery is available for 30 days. Confirm with your password.</p>
                                        <input type="password" value={deletePassword} onChange={(e) => setDeletePassword(e.target.value)} placeholder="Authorization password"
                                            className="w-full bg-secondary/50 text-text-primary rounded-2xl px-5 py-4 outline-none focus:ring-2 focus:ring-red-500/20 text-sm font-bold placeholder:text-text-muted/20 shadow-sm ring-1 ring-white/5" />
                                        <div className="flex gap-3">
                                            <button onClick={handleDeleteAccount} className="flex-1 bg-red-500 text-white font-black text-xs py-4 px-6 rounded-2xl hover:bg-red-600 hover:shadow-lg transition-all duration-300 uppercase tracking-widest active:scale-95">Request Deletion</button>
                                            <button onClick={() => setShowDeleteConfirm(false)} className="flex-1 bg-secondary/50 text-text-primary font-black text-xs py-4 px-6 rounded-2xl hover:bg-secondary hover:shadow-lg transition-all duration-300 uppercase tracking-widest active:scale-95">Cancel</button>
                                        </div>
                                    </div>
                                )}
                             </div>
                        </div>
                    )}
                </div>

                {/* Status Messages & Save Action */}
                <div className="px-8 pb-8 pt-2 relative z-0">
                    <div className="h-14 flex items-center justify-end">
                        {(activeTab === 'profile' || activeTab === 'preferences') && (
                            <button onClick={handleSave} disabled={isSaving}
                                className="min-w-[160px] bg-text-primary text-secondary font-black text-[13px] py-3.5 px-8 rounded-2xl hover:bg-text-primary/90 hover:shadow-2xl hover:shadow-black/40 transition-all duration-300 disabled:opacity-50 flex items-center justify-center gap-2.5 shadow-xl shadow-black/20 uppercase tracking-widest leading-none active:scale-95">
                                <Save className={cn("w-4 h-4", isSaving && "animate-spin")} /> 
                                <span>{isSaving ? t('profile.saving') : t('profile.save')}</span>
                            </button>
                        )}
                    </div>
                </div>

                {/* Floating Notification */}
                <AnimatePresence>
                    {toast && (
                        <Toast 
                            message={toast.message} 
                            type={toast.type} 
                            onClose={() => setToast(null)} 
                        />
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};

export default ProfilePage;
