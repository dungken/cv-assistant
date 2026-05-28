import { useCallback, useEffect, useRef, useState } from 'react';
import { AxiosError } from 'axios';
import { RefreshCw, Activity, AlertCircle, Plus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import {
    cvHealthApi,
    skillApi,
    type HealthScoreResponse,
    type FreshnessHistoryResponse,
    type SkillAlertsResponse,
    type OpportunityWindowResponse,
} from '../../../services/api';
import FreshnessGauge from './FreshnessGauge';
import FreshnessTimeSeriesChart from './FreshnessTimeSeriesChart';
import SkillAlertsCard from './SkillAlertsCard';
import OpportunityWindow from './OpportunityWindow';
import CVPicker from './CVPicker';
import WhatIfSimulation from './WhatIfSimulation';

interface Props {
    userId: string;
}

function formatRelativeTime(date: Date | null): string {
    if (!date) return '';
    const diff = Math.floor((Date.now() - date.getTime()) / 1000);
    if (diff < 5) return 'vừa xong';
    if (diff < 60) return `${diff}s trước`;
    if (diff < 3600) return `${Math.floor(diff / 60)} phút trước`;
    return `${Math.floor(diff / 3600)} giờ trước`;
}

export default function CVHealthDashboard({ userId }: Props) {
    const navigate = useNavigate();
    const [healthScore, setHealthScore] = useState<HealthScoreResponse | null>(null);
    const [history, setHistory] = useState<FreshnessHistoryResponse | null>(null);
    const [alerts, setAlerts] = useState<SkillAlertsResponse | null>(null);
    const [opportunities, setOpportunities] = useState<OpportunityWindowResponse | null>(null);

    const [loadingScore, setLoadingScore] = useState(false);
    const [loadingHistory, setLoadingHistory] = useState(false);
    const [loadingAlerts, setLoadingAlerts] = useState(false);
    const [loadingOpps, setLoadingOpps] = useState(false);
    const [refreshing, setRefreshing] = useState(false);
    const [initialCheckComplete, setInitialCheckComplete] = useState(false);

    // Keep a copy of original data before simulation
    const [originalHealthScore, setOriginalHealthScore] = useState<HealthScoreResponse | null>(null);

    const [hasUploadedCvs, setHasUploadedCvs] = useState<boolean | null>(null);
    const [noCvYet, setNoCvYet] = useState(false);
    const [globalError, setGlobalError] = useState<string | null>(null);
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
    const [tick, setTick] = useState(0);
    const [marketKpis, setMarketKpis] = useState<{ total_jds: number; total_companies: number } | null>(null);

    // Track whether data has been loaded at least once — avoids stale closure in useCallback
    const hasData = useRef({ score: false, history: false, alerts: false, opps: false });

    const fetchAll = useCallback(async () => {
        setNoCvYet(false);
        setGlobalError(null);
        setRefreshing(true);
        // Show skeleton only on first load; re-fetches update silently (no flash)
        if (!hasData.current.score) setLoadingScore(true);
        if (!hasData.current.history) setLoadingHistory(true);
        if (!hasData.current.alerts) setLoadingAlerts(true);
        if (!hasData.current.opps) setLoadingOpps(true);

        const results = await Promise.allSettled([
            cvHealthApi.getHealthScore(userId, true),
            cvHealthApi.getFreshnessHistory(userId),
            cvHealthApi.getSkillAlerts(userId),
            cvHealthApi.getOpportunities(userId, { days: 7, limit: 10, minMatch: 0.5 }),
        ]);

        const [scoreRes, histRes, alertsRes, oppsRes] = results;
        let foundNoCv = false;
        let networkErrorCount = 0;

        const isNotFound = (r: PromiseSettledResult<unknown>) =>
            r.status === 'rejected' &&
            r.reason instanceof AxiosError &&
            r.reason.response?.status === 404;

        const isNetworkError = (r: PromiseSettledResult<unknown>) =>
            r.status === 'rejected' &&
            r.reason instanceof AxiosError &&
            (!r.reason.response || r.reason.response.status >= 500);

        if (scoreRes.status === 'fulfilled') { setHealthScore(scoreRes.value.data); setOriginalHealthScore(scoreRes.value.data); hasData.current.score = true; }
        else if (isNotFound(scoreRes)) { foundNoCv = true; setHealthScore(null); setOriginalHealthScore(null); }
        else if (isNetworkError(scoreRes)) networkErrorCount++;

        if (histRes.status === 'fulfilled') { setHistory(histRes.value.data); hasData.current.history = true; }
        else if (isNetworkError(histRes)) networkErrorCount++;

        if (alertsRes.status === 'fulfilled') { setAlerts(alertsRes.value.data); hasData.current.alerts = true; }
        else if (isNetworkError(alertsRes)) networkErrorCount++;

        if (oppsRes.status === 'fulfilled') { setOpportunities(oppsRes.value.data); hasData.current.opps = true; }
        else if (isNotFound(oppsRes)) { foundNoCv = true; setOpportunities(null); }
        else if (isNetworkError(oppsRes)) networkErrorCount++;

        setNoCvYet(foundNoCv);
        if (networkErrorCount >= 2 && !foundNoCv) {
            setGlobalError('Không kết nối được server. Hãy thử lại.');
        }

        setLoadingScore(false);
        setLoadingHistory(false);
        setLoadingAlerts(false);
        setLoadingOpps(false);
        setRefreshing(false);
        setInitialCheckComplete(true);
        setLastUpdated(new Date());
    }, [userId]);

    useEffect(() => {
        if (userId) fetchAll();
    }, [userId, fetchAll]);

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
            <div className={`sticky top-0 z-30 -mx-6 bg-canvas/60 backdrop-blur-xl border-b border-white/5 ${(!initialCheckComplete || hasUploadedCvs === false) ? 'hidden' : ''}`}>
                <div className="px-6 py-3">
                    <CVPicker userId={userId} onLinked={fetchAll} onEmpty={(empty) => setHasUploadedCvs(!empty)} />
                </div>
                {/* Progress bar — shown while refreshing */}
                <div className={`h-0.5 bg-accent-primary/20 overflow-hidden transition-opacity duration-300 ${refreshing ? 'opacity-100' : 'opacity-0'}`}>
                    <div className="h-full w-[40%] bg-accent-primary animate-progress" />
                </div>
            </div>

            {/* Metrics grid */}
            {(!initialCheckComplete || hasUploadedCvs === null) ? (
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
                                onClick={() => navigate('/cv-upload')}
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
                    <WhatIfSimulation 
                        userId={userId} 
                        originalData={originalHealthScore} 
                        onSimulate={(simulatedData) => {
                            if (simulatedData) {
                                setHealthScore(simulatedData);
                            } else {
                                setHealthScore(originalHealthScore);
                            }
                        }} 
                    />
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <FreshnessTimeSeriesChart data={history} loading={loadingHistory} />
                        <SkillAlertsCard data={alerts} loading={loadingAlerts} />
                    </div>
                    <OpportunityWindow data={opportunities} loading={loadingOpps} />
                </div>
            )}
        </div>
        </div>
    );
}
