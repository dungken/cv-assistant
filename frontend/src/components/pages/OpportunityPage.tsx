import OpportunityWindow from '../features/cv-health/OpportunityWindow';

interface Props {
    userId: string;
    isAuthenticated: boolean;
    onRequireAuth: () => void;
}

export default function OpportunityPage({ userId, isAuthenticated, onRequireAuth }: Props) {
    if (!isAuthenticated) {
        return (
            <div className="max-w-7xl mx-auto px-6 pt-12 pb-6">
                <div className="rounded-3xl border border-accent-primary/20 bg-gradient-to-br from-accent-primary/10 to-accent-secondary/5 p-12 text-center shadow-[0_0_40px_rgba(99,102,241,0.1)] relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-accent-primary/20 rounded-full blur-[80px] -translate-y-1/2 translate-x-1/2 pointer-events-none" />
                    <div className="absolute bottom-0 left-0 w-64 h-64 bg-accent-secondary/20 rounded-full blur-[80px] translate-y-1/2 -translate-x-1/2 pointer-events-none" />
                    <div className="w-20 h-20 mx-auto rounded-full bg-accent-primary/10 flex items-center justify-center mb-6">
                        <svg className="w-10 h-10 text-accent-primary" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="m16 12-4-4-4 4"/><path d="M12 16V8"/></svg>
                    </div>
                    <h2 className="text-2xl font-black font-outfit mb-3 text-text-primary tracking-tight">Opportunity Window</h2>
                    <p className="text-sm text-text-secondary leading-relaxed max-w-lg mx-auto mb-8">
                        Đăng nhập để xem các JD phù hợp nhất với CV của bạn, được sắp xếp theo mức độ match.
                    </p>
                    <button
                        onClick={onRequireAuth}
                        className="px-8 py-3 rounded-full font-bold text-sm bg-accent-primary text-white hover:shadow-[0_0_20px_rgba(37,99,235,0.4)] transition-all inline-flex items-center gap-2 hover:scale-105 active:scale-95"
                    >
                        Đăng nhập để xem
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto px-6 pt-6 pb-6">
            <OpportunityWindow userId={userId} />
        </div>
    );
}
