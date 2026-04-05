import React, { useState } from 'react';
import { Mail, Lock, KeyRound, ArrowRight, ArrowLeft, Sparkles, ShieldCheck } from 'lucide-react';
import { authApi } from '../../services/api';

interface ForgotPasswordProps {
    onBackToLogin: () => void;
}

type Step = 'email' | 'otp' | 'success';

const ForgotPassword: React.FC<ForgotPasswordProps> = ({ onBackToLogin }) => {
    const [step, setStep] = useState<Step>('email');
    const [email, setEmail] = useState('');
    const [otp, setOtp] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSendOtp = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);
        try {
            await authApi.forgotPassword(email);
            setStep('otp');
        } catch (err: any) {
            setError(err.response?.data?.error || 'Failed to send OTP');
        } finally {
            setIsLoading(false);
        }
    };

    const handleResetPassword = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        if (newPassword !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }
        if (newPassword.length < 8) {
            setError('Password must be at least 8 characters');
            return;
        }
        setIsLoading(true);
        try {
            await authApi.resetPassword(email, otp, newPassword);
            setStep('success');
        } catch (err: any) {
            setError(err.response?.data?.error || 'Failed to reset password');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex w-full max-w-6xl bg-secondary/30 backdrop-blur-xl rounded-[3rem] overflow-hidden shadow-2xl animate-in zoom-in-95 duration-700">
            {/* Left Column */}
            <div className="hidden lg:flex lg:w-1/2 bg-linear-to-br from-emerald-600 via-teal-700 to-cyan-900 p-12 flex-col justify-between relative overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 blur-[100px] rounded-full -mr-20 -mt-20"></div>
                <div className="absolute bottom-0 left-0 w-64 h-64 bg-teal-400/20 blur-[100px] rounded-full -ml-20 -mb-20"></div>

                <div className="relative z-10">
                    <div className="w-16 h-16 bg-white/10 backdrop-blur-md rounded-2xl flex items-center justify-center mb-10 border border-white/20 shadow-xl">
                        <ShieldCheck className="w-8 h-8 text-white" />
                    </div>
                    <h1 className="text-5xl font-black text-white tracking-tighter leading-tight mb-6">
                        Account <br /> Recovery.
                    </h1>
                    <p className="text-white/80 text-lg font-medium">
                        We'll send a verification code to your email to help you reset your password securely.
                    </p>
                </div>

                <div className="relative z-10 mt-auto">
                    <p className="text-white/40 text-xs font-bold uppercase tracking-[0.2em]">&copy; 2026 Resume Assistant Intelligence</p>
                </div>
            </div>

            {/* Right Column */}
            <div className="w-full lg:w-1/2 p-10 md:p-16 flex flex-col justify-center bg-surface">
                <div className="mb-10 text-center lg:text-left">
                    <div className="lg:hidden flex justify-center mb-8">
                        <div className="w-14 h-14 bg-emerald-500 rounded-2xl flex items-center justify-center shadow-lg">
                            <Sparkles className="w-7 h-7 text-white" />
                        </div>
                    </div>
                    <span className="inline-block px-4 py-1.5 rounded-full bg-emerald-500/10 text-emerald-500 text-[10px] font-black tracking-widest uppercase mb-4">
                        {step === 'email' ? 'Step 1 of 2' : step === 'otp' ? 'Step 2 of 2' : 'Complete'}
                    </span>
                    <h2 className="text-4xl font-black text-text-primary mb-2 tracking-tighter">
                        {step === 'email' ? 'Reset password.' : step === 'otp' ? 'Enter code.' : 'All done!'}
                    </h2>
                    <p className="text-text-secondary font-medium tracking-tight">
                        {step === 'email' ? 'Enter your email to receive a reset code' :
                         step === 'otp' ? 'Check your email for the 6-digit code' :
                         'Your password has been reset successfully'}
                    </p>
                </div>

                {step === 'email' && (
                    <form onSubmit={handleSendOtp} className="space-y-5">
                        <div className="space-y-1.5">
                            <label className="text-[11px] font-black text-text-secondary/60 uppercase tracking-widest ml-1">Email Address</label>
                            <div className="relative group">
                                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-secondary/40 group-focus-within:text-emerald-500 transition-colors" />
                                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="name@company.com"
                                    className="w-full bg-secondary/50 text-text-primary rounded-2xl pl-12 pr-4 py-4 outline-none focus:border-emerald-500 focus:bg-surface focus:ring-2 focus:ring-emerald-500/10 transition-all font-medium placeholder:text-text-secondary/30" required />
                            </div>
                        </div>

                        {error && <div className="bg-red-500/10 border border-red-500/20 text-red-500 text-[11px] py-4 px-4 rounded-2xl text-center font-bold animate-in fade-in slide-in-from-top-2">{error.toUpperCase()}</div>}

                        <button type="submit" disabled={isLoading}
                            className="w-full bg-emerald-500 text-white font-black text-sm py-5 rounded-2xl shadow-2xl hover:bg-emerald-600 active:scale-[0.98] transition-all disabled:opacity-50 flex items-center justify-center gap-3 mt-6">
                            {isLoading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div> : <><span>SEND RESET CODE</span><ArrowRight className="w-5 h-5" /></>}
                        </button>
                    </form>
                )}

                {step === 'otp' && (
                    <form onSubmit={handleResetPassword} className="space-y-5">
                        <div className="space-y-1.5">
                            <label className="text-[11px] font-black text-text-secondary/60 uppercase tracking-widest ml-1">Verification Code</label>
                            <div className="relative group">
                                <KeyRound className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-secondary/40 group-focus-within:text-emerald-500 transition-colors" />
                                <input type="text" value={otp} onChange={(e) => setOtp(e.target.value)} placeholder="123456" maxLength={6}
                                    className="w-full bg-secondary/50 text-text-primary rounded-2xl pl-12 pr-4 py-4 outline-none focus:border-emerald-500 focus:bg-surface focus:ring-2 focus:ring-emerald-500/10 transition-all font-medium placeholder:text-text-secondary/30 tracking-[0.3em] text-center text-lg" required />
                            </div>
                        </div>
                        <div className="space-y-1.5">
                            <label className="text-[11px] font-black text-text-secondary/60 uppercase tracking-widest ml-1">New Password</label>
                            <div className="relative group">
                                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-secondary/40 group-focus-within:text-emerald-500 transition-colors" />
                                <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} placeholder="••••••••" minLength={8}
                                    className="w-full bg-secondary/50 text-text-primary rounded-2xl pl-12 pr-4 py-4 outline-none focus:border-emerald-500 focus:bg-surface focus:ring-2 focus:ring-emerald-500/10 transition-all font-medium placeholder:text-text-secondary/30" required />
                            </div>
                        </div>
                        <div className="space-y-1.5">
                            <label className="text-[11px] font-black text-text-secondary/60 uppercase tracking-widest ml-1">Confirm Password</label>
                            <div className="relative group">
                                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-secondary/40 group-focus-within:text-emerald-500 transition-colors" />
                                <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="••••••••" minLength={8}
                                    className="w-full bg-secondary/50 text-text-primary rounded-2xl pl-12 pr-4 py-4 outline-none focus:border-emerald-500 focus:bg-surface focus:ring-2 focus:ring-emerald-500/10 transition-all font-medium placeholder:text-text-secondary/30" required />
                            </div>
                        </div>

                        {error && <div className="bg-red-500/10 border border-red-500/20 text-red-500 text-[11px] py-4 px-4 rounded-2xl text-center font-bold animate-in fade-in slide-in-from-top-2">{error.toUpperCase()}</div>}

                        <button type="submit" disabled={isLoading}
                            className="w-full bg-emerald-500 text-white font-black text-sm py-5 rounded-2xl shadow-2xl hover:bg-emerald-600 active:scale-[0.98] transition-all disabled:opacity-50 flex items-center justify-center gap-3 mt-6">
                            {isLoading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div> : <><span>RESET PASSWORD</span><ArrowRight className="w-5 h-5" /></>}
                        </button>
                    </form>
                )}

                {step === 'success' && (
                    <div className="text-center space-y-6">
                        <div className="w-20 h-20 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto">
                            <ShieldCheck className="w-10 h-10 text-emerald-500" />
                        </div>
                        <p className="text-text-secondary font-medium">Your password has been updated. You can now sign in with your new password.</p>
                        <button onClick={onBackToLogin}
                            className="w-full bg-emerald-500 text-white font-black text-sm py-5 rounded-2xl shadow-2xl hover:bg-emerald-600 active:scale-[0.98] transition-all flex items-center justify-center gap-3">
                            <span>BACK TO SIGN IN</span>
                            <ArrowRight className="w-5 h-5" />
                        </button>
                    </div>
                )}

                <div className="mt-12 pt-8 border-t text-center">
                    <p className="text-text-secondary text-xs font-bold uppercase tracking-widest">
                        <button onClick={onBackToLogin} className="text-emerald-500 hover:underline flex items-center gap-2 mx-auto">
                            <ArrowLeft className="w-3 h-3" /> Back to sign in
                        </button>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default ForgotPassword;
