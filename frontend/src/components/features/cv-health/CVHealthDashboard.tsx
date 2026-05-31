import { useCallback, useEffect, useRef, useState } from 'react';
import { AxiosError } from 'axios';
import { RefreshCw, Activity, AlertCircle, Plus, Target, TrendingUp } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import {
    cvHealthApi,
    skillApi,
    type HealthScoreResponse,
} from '../../../services/api';
import FreshnessGauge from './FreshnessGauge';
import CVPicker from './CVPicker';

interface Props {
    userId: string;
    isAuthenticated: boolean;
    onRequireAuth: () => void;
}

function formatRelativeTime(date: Date | null): string {
    if (!date) return '';
    const diff = Math.floor((Date.now() - date.getTime()) / 1000);
    if (diff < 5) return 'vừa xong';
    if (diff < 60) return `${diff}s trước`;
    if (diff < 3600) return `${Math.floor(diff / 60)} phút trước`;
    return `${Math.floor(diff / 3600)} giờ trước`;
}

export default function CVHealthDashboard({ userId, isAuthenticated, onRequireAuth }: Props) {
    const navigate = useNavigate();
    const [healthScore, setHealthScore] = useState<HealthScoreResponse | null>(null);

    const [loadingScore, setLoadingScore] = useState(false);
    const [refreshing, setRefreshing] = useState(false);
    const [initialCheckComplete, setInitialCheckComplete] = useState(false);

    const [hasUploadedCvs, setHasUploadedCvs] = useState<boolean | null>(null);
    const [noCvYet, setNoCvYet] = useState(false);
    const [globalError, setGlobalError] = useState<string | null>(null);
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
    const [tick, setTick] = useState(0);
    const [marketKpis, setMarketKpis] = useState<{ total_jds: number; total_companies: number } | null>(null);

    // Track whether data has been loaded at least once — avoids stale closure in useCallback
    const hasData = useRef({ score: false });

    const fetchAll = useCallback(async () => {
        if (!isAuthenticated) return;
        setNoCvYet(false);
        setGlobalError(null);
        setRefreshing(true);
        if (!hasData.current.score) setLoadingScore(true);

        let foundNoCv = false;
        let networkErrorCount = 0;
        try {
            const res = await cvHealthApi.getHealthScore(userId);
            setHealthScore(res.data);
            hasData.current.score = true;
        } catch (e) {
            if (e instanceof AxiosError) {
                if (e.response?.status === 404) { foundNoCv = true; setHealthScore(null); }
                else if (!e.response || e.response.status >= 500) networkErrorCount++;
            }
        }

        setNoCvYet(foundNoCv);
        if (networkErrorCount >= 1 && !foundNoCv) {
            setGlobalError('Không kết nối được server. Hãy thử lại.');
        }

        setLoadingScore(false);
        setRefreshing(false);
        setInitialCheckComplete(true);
        setLastUpdated(new Date());
    }, [userId, isAuthenticated]);

    useEffect(() => {
        if (isAuthenticated && userId) fetchAll();
    }, [isAuthenticated, userId, fetchAll]);

    useEffect(() => {
        skillApi.getMarketIntelDashboard({}).then(r => {
            setMarketKpis({ total_jds: r.data.kpis.total_jds, total_companies: r.data.kpis.total_companies });
        }).catch(() => {});
    }, []);

    useEffect(() => {
        const t = setInterval(() => setTick(x => x + 1), 30_000);
        return () => clearInterval(t);
    }, []);
    void tick;

    // Helper to get ambient color based on score
    const getAmbientColor = () => {
        if (!healthScore) return 'from-violet-500/5 to-indigo-600/5';
        const s = healthScore.score;
        if (s >= 75) return 'from-emerald-500/10 to-teal-600/5';
        if (s >= 50) return 'from-blue-500/10 to-indigo-600/5';
        if (s >= 30) return 'from-orange-500/10 to-amber-600/5';
        return 'from-rose-500/10 to-red-600/5';
    };

    return (
        <div className="relative min-h-full transition-colors duration-1000">
        <div className="max-w-7xl mx-auto px-6 pb-6 space-y-6">

            {/* Header */}
            <header className="pt-6">
                <div className="flex items-center gap-3 mb-2">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-violet-500/30 shrink-0">
                        <Activity className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-black font-outfit tracking-tight">CV Health Intelligence</h1>
                        <p className="text-text-secondary text-sm">Chấm điểm CV theo 8 chiều dựa trên dữ liệu thị trường IT Việt Nam</p>
                    </div>
                </div>
                <div className="pl-15 mt-1 flex items-center gap-3">
                    <p className="text-text-secondary text-sm">
                        {marketKpis
                            ? <>Dữ liệu tổng hợp từ <b className="text-text-primary">{marketKpis.total_jds.toLocaleString()}</b> JD · <b className="text-text-primary">{marketKpis.total_companies.toLocaleString()}</b> công ty</>
                            : <>Dữ liệu từ ITviec + TopCV</>
                        }
                        {lastUpdated && (
                            <span className="text-text-muted ml-2">· cập nhật {formatRelativeTime(lastUpdated)}</span>
                        )}
                    </p>
                    {refreshing && (
                        <RefreshCw className="w-3.5 h-3.5 text-text-muted animate-spin shrink-0" />
                    )}
                </div>
            </header>

            {/* Global error banner */}
            {globalError && (
                <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm animate-in fade-in duration-300">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span className="flex-1">{globalError}</span>
                    <button
                        onClick={fetchAll}
                        className="text-xs font-bold uppercase tracking-wider hover:text-rose-100 transition-colors"
                    >
                        Thử lại
                    </button>
                </div>
            )}

            {/* CV picker — sticky filter bar */}
            <div className={`sticky top-0 z-30 -mx-6 bg-canvas/95 border-b border-white/5 ${(!initialCheckComplete || hasUploadedCvs === false) ? 'hidden' : ''}`}>
                <div className="px-6 py-3">
                    <CVPicker userId={userId} onLinked={fetchAll} onEmpty={(empty) => setHasUploadedCvs(!empty)} />
                </div>
                {/* Progress bar — shown while refreshing */}
                <div className={`h-0.5 bg-accent-primary/20 overflow-hidden transition-opacity duration-300 ${refreshing ? 'opacity-100' : 'opacity-0'}`}>
                    <div className="h-full w-[40%] bg-accent-primary animate-progress" />
                </div>
            </div>

            {/* Metrics grid */}
            {!isAuthenticated ? (
                <div className="rounded-3xl border border-accent-primary/20 bg-gradient-to-br from-accent-primary/10 to-accent-secondary/5 p-12 text-center shadow-[0_0_40px_rgba(99,102,241,0.1)] relative overflow-hidden mt-8">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-accent-primary/20 rounded-full blur-[80px] -translate-y-1/2 translate-x-1/2 pointer-events-none" />
                    <div className="absolute bottom-0 left-0 w-64 h-64 bg-accent-secondary/20 rounded-full blur-[80px] translate-y-1/2 -translate-x-1/2 pointer-events-none" />
                    
                    <div className="w-20 h-20 mx-auto rounded-full bg-accent-primary/10 flex items-center justify-center mb-6">
                        <Activity className="w-10 h-10 text-accent-primary" />
                    </div>
                    
                    <h2 className="text-2xl font-black font-outfit mb-3 text-text-primary tracking-tight">Trải nghiệm phân tích CV AI</h2>
                    <p className="text-sm text-text-secondary leading-relaxed max-w-lg mx-auto mb-8">
                        Đăng nhập để trải nghiệm công cụ phân tích độ "tươi" của CV theo 8 chiều chuyên sâu, so khớp với hàng ngàn tin tuyển dụng thực tế.
                    </p>
                    <button 
                        onClick={onRequireAuth}
                        className="px-8 py-3 rounded-full font-bold text-sm bg-accent-primary text-white hover:shadow-[0_0_20px_rgba(37,99,235,0.4)] transition-all inline-flex items-center gap-2 hover:scale-105 active:scale-95"
                    >
                        <Plus className="w-4 h-4" /> Đăng nhập để sử dụng
                    </button>
                </div>
            ) : (!initialCheckComplete || hasUploadedCvs === null) ? (
                <div className="flex items-center justify-center min-h-[40vh]">
                    <Activity className="w-8 h-8 text-accent-primary animate-pulse" />
                </div>
            ) : (noCvYet || hasUploadedCvs === false) ? (
                <div className="rounded-3xl border border-accent-primary/20 bg-gradient-to-br from-accent-primary/10 to-accent-secondary/5 p-12 text-center shadow-[0_0_40px_rgba(99,102,241,0.1)] relative overflow-hidden mt-8">
                    {/* Decorative blurred blobs */}
                    <div className="absolute top-0 right-0 w-64 h-64 bg-accent-primary/20 rounded-full blur-[80px] -translate-y-1/2 translate-x-1/2 pointer-events-none" />
                    <div className="absolute bottom-0 left-0 w-64 h-64 bg-accent-secondary/20 rounded-full blur-[80px] translate-y-1/2 -translate-x-1/2 pointer-events-none" />
                    
                    <div className="w-20 h-20 mx-auto rounded-full bg-accent-primary/10 flex items-center justify-center mb-6">
                        <Activity className="w-10 h-10 text-accent-primary" />
                    </div>
                    
                    {hasUploadedCvs === false ? (
                        <>
                            <h2 className="text-2xl font-black font-outfit mb-3 text-text-primary tracking-tight">Bắt đầu chuẩn đoán sức khỏe CV</h2>
                            <p className="text-sm text-text-secondary leading-relaxed max-w-lg mx-auto mb-8">
                                Chấm điểm CV theo <strong>8 chiều</strong> dựa trên dữ liệu thị trường thực
                                (~1.600 JD crawl từ ITviec + TopCV). Hãy tải lên một CV mới để bắt đầu.
                            </p>
                            <button 
                                onClick={() => {
                                    if (!isAuthenticated) onRequireAuth();
                                    else navigate('/cv-upload');
                                }}
                                className="px-8 py-3 rounded-full font-bold text-sm bg-accent-primary text-white hover:shadow-[0_0_20px_rgba(37,99,235,0.4)] transition-all inline-flex items-center gap-2 hover:scale-105 active:scale-95"
                            >
                                <Plus className="w-4 h-4" /> Tải CV lên ngay
                            </button>
                        </>
                    ) : (
                        <>
                            <h2 className="text-2xl font-black font-outfit mb-3 text-text-primary tracking-tight">Chưa có dữ liệu phân tích</h2>
                            <p className="text-sm text-text-secondary leading-relaxed max-w-lg mx-auto mb-8">
                                CV bạn chọn chưa được tính toán điểm sức khỏe hoặc chưa đồng bộ dữ liệu. 
                                <br/>Vui lòng nhấn nút <strong className="text-accent-primary">Sync CV Health</strong> ở thanh công cụ phía trên để bắt đầu phân tích.
                            </p>
                        </>
                    )}
                </div>
            ) : (
                <div className={`space-y-6 transition-opacity duration-300 ${refreshing ? 'opacity-60' : 'opacity-100'}`}>
                    <FreshnessGauge data={healthScore} loading={loadingScore} />

                    {/* Điều hướng qua lại */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8">
                        <button
                            type="button"
                            onClick={() => navigate('/opportunities')}
                            className="flex flex-col text-left p-5 rounded-2xl bg-surface/80 border border-white/5 hover:bg-white/[0.04] hover:border-accent-primary/30 transition-all group"
                        >
                            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                                <Target className="w-5 h-5 text-indigo-400" />
                            </div>
                            <h3 className="text-sm font-bold text-text-primary mb-1">Opportunity Window</h3>
                            <p className="text-xs text-text-secondary">Xem các cơ hội việc làm phù hợp nhất với CV hiện tại</p>
                        </button>

                        <button
                            type="button"
                            onClick={() => navigate('/market-intel')}
                            className="flex flex-col text-left p-5 rounded-2xl bg-surface/80 border border-white/5 hover:bg-white/[0.04] hover:border-emerald-500/30 transition-all group"
                        >
                            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                                <TrendingUp className="w-5 h-5 text-emerald-400" />
                            </div>
                            <h3 className="text-sm font-bold text-text-primary mb-1">Market Intel</h3>
                            <p className="text-xs text-text-secondary">Khám phá xu hướng kỹ năng và mức lương trên thị trường</p>
                        </button>
                    </div>
                </div>
            )}
        </div>
        </div>
    );
}
