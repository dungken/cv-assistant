import React, { useState } from 'react';
import { UserPlus, Mail, Lock, User, ArrowRight, Sparkles, BookOpen, Target } from 'lucide-react';
import { authApi } from '../../services/api';

interface RegisterProps {
    onRegisterSuccess: (token: string, name: string) => void;
    onSwitchToLogin: () => void;
}

const Register: React.FC<RegisterProps> = ({ onRegisterSuccess, onSwitchToLogin }) => {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);
        try {
            const res = await authApi.register({ name, email, password });
            localStorage.setItem('token', res.data.token);
            localStorage.setItem('userName', res.data.name);
            onRegisterSuccess(res.data.token, res.data.name);
        } catch (err: any) {
            setError(err.response?.data?.error || 'Registration failed. Try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex w-full max-w-6xl bg-secondary/30 backdrop-blur-xl rounded-[3rem] overflow-hidden border border-border-main shadow-2xl animate-in zoom-in-95 duration-700">
            {/* Left Column: Visuals & Mission */}
            <div className="hidden lg:flex lg:w-1/2 bg-linear-to-br from-purple-600 via-indigo-700 to-indigo-900 p-12 flex-col justify-between relative overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 blur-[100px] rounded-full -mr-20 -mt-20 anim-pulse"></div>
                <div className="absolute bottom-0 left-0 w-64 h-64 bg-purple-400/20 blur-[100px] rounded-full -ml-20 -mb-20"></div>

                <div className="relative z-10">
                    <div className="w-16 h-16 bg-white/10 backdrop-blur-md rounded-2xl flex items-center justify-center mb-10 border border-white/20 shadow-xl">
                        <Sparkles className="w-8 h-8 text-white" />
                    </div>
                    <h1 className="text-5xl font-black text-white tracking-tighter leading-tight mb-6">
                        Start Your <br /> Career Journey.
                    </h1>
                    <p className="text-white/80 text-lg mb-10 font-medium">Join 50,000+ professionals using AI to optimize their career paths.</p>

                    <ul className="space-y-6">
                        {[
                            { icon: <BookOpen />, text: "Expert CV Templates" },
                            { icon: <Target />, text: "Precision Career Roadmaps" },
                            { icon: <Sparkles />, text: "AI-Powered Skill Analysis" }
                        ].map((item, idx) => (
                            <li key={idx} className="flex items-center gap-4 text-white/90 font-medium text-sm">
                                <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center border border-white/10 flex-shrink-0">
                                    {React.cloneElement(item.icon as React.ReactElement<any>, { size: 16, className: "text-white" })}
                                </div>
                                {item.text}
                            </li>
                        ))}
                    </ul>
                </div>

                <div className="relative z-10 mt-auto">
                    <p className="text-white/40 text-xs font-bold uppercase tracking-[0.2em]">© 2026 CV Assistant Intelligence</p>
                </div>
            </div>

            {/* Right Column: Registration Form */}
            <div className="w-full lg:w-1/2 p-10 md:p-16 flex flex-col justify-center bg-surface">
                <div className="mb-10 text-center lg:text-left">
                    <div className="lg:hidden flex justify-center mb-8">
                        <div className="w-14 h-14 bg-accent-secondary rounded-2xl flex items-center justify-center shadow-lg">
                            <Sparkles className="w-7 h-7 text-white" />
                        </div>
                    </div>
                    <span className="inline-block px-4 py-1.5 rounded-full bg-accent-secondary/10 text-accent-secondary text-[10px] font-black tracking-widest uppercase mb-4">
                        Join the Future
                    </span>
                    <h2 className="text-4xl font-black text-text-primary mb-2 tracking-tighter">Start here.</h2>
                    <p className="text-text-secondary font-medium tracking-tight">Create your account to begin</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div className="space-y-1.5">
                        <label className="text-[11px] font-black text-text-secondary/60 uppercase tracking-widest ml-1">Full Name</label>
                        <div className="relative group">
                            <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-secondary/40 group-focus-within:text-accent-secondary transition-colors" />
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="Dung Ken"
                                className="w-full bg-secondary/50 border border-border-main text-text-primary rounded-2xl pl-12 pr-4 py-4 outline-none focus:border-accent-secondary focus:bg-surface focus:ring-2 focus:ring-accent-secondary/10 transition-all font-medium placeholder:text-text-secondary/30"
                                required
                            />
                        </div>
                    </div>
                    <div className="space-y-1.5">
                        <label className="text-[11px] font-black text-text-secondary/60 uppercase tracking-widest ml-1">Email Address</label>
                        <div className="relative group">
                            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-secondary/40 group-focus-within:text-accent-secondary transition-colors" />
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="name@company.com"
                                className="w-full bg-secondary/50 border border-border-main text-text-primary rounded-2xl pl-12 pr-4 py-4 outline-none focus:border-accent-secondary focus:bg-surface focus:ring-2 focus:ring-accent-secondary/10 transition-all font-medium placeholder:text-text-secondary/30"
                                required
                            />
                        </div>
                    </div>
                    <div className="space-y-1.5">
                        <label className="text-[11px] font-black text-text-secondary/60 uppercase tracking-widest ml-1">Password</label>
                        <div className="relative group">
                            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-secondary/40 group-focus-within:text-accent-secondary transition-colors" />
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                minLength={8}
                                className="w-full bg-secondary/50 border border-border-main text-text-primary rounded-2xl pl-12 pr-4 py-4 outline-none focus:border-accent-secondary focus:bg-surface focus:ring-2 focus:ring-accent-secondary/10 transition-all font-medium placeholder:text-text-secondary/30"
                                required
                            />
                        </div>
                    </div>

                    {error && (
                        <div className="bg-red-500/10 border border-red-500/20 text-red-500 text-[11px] py-4 px-4 rounded-2xl text-center font-bold animate-in fade-in slide-in-from-top-2">
                            {error.toUpperCase()}
                        </div>
                    )}

                    <button
                        type="submit"
                        className="w-full bg-accent-secondary text-white font-black text-sm py-5 rounded-2xl shadow-2xl hover:bg-purple-700 hover:shadow-accent-secondary/20 active:scale-[0.98] transition-all disabled:opacity-50 flex items-center justify-center gap-3 mt-6"
                        disabled={isLoading}
                    >
                        {isLoading ? (
                            <div className="w-5 h-5 border-2 border-bg-primary/30 border-t-bg-primary rounded-full animate-spin"></div>
                        ) : (
                            <>
                                CREATE ACCOUNT
                                <ArrowRight className="w-5 h-5" />
                            </>
                        )}
                    </button>
                </form>

                <div className="mt-12 pt-8 border-t border-border-main/50 text-center">
                    <p className="text-text-secondary text-xs font-bold uppercase tracking-widest">
                        Already have an account? <button onClick={onSwitchToLogin} className="text-accent-secondary hover:underline ml-1">Sign in here</button>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Register;
