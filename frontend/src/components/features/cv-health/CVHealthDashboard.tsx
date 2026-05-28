import { useCallback, useEffect, useRef, useState } from 'react';
import { AxiosError } from 'axios';
import { RefreshCw, Activity, AlertCircle } from 'lucide-react';

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
    const [healthScore, setHealthScore] = useState<HealthScoreResponse | null>(null);
    const [history, setHistory] = useState<FreshnessHistoryResponse | null>(null);
    const [alerts, setAlerts] = useState<SkillAlertsResponse | null>(null);
    const [opportunities, setOpportunities] = useState<OpportunityWindowResponse | null>(null);

    const [loadingScore, setLoadingScore] = useState(false);
    const [loadingHistory, setLoadingHistory] = useState(false);
    const [loadingAlerts, setLoadingAlerts] = useState(false);
    const [loadingOpps, setLoadingOpps] = useState(false);
    const [refreshing, setRefreshing] = useState(false);

    // Keep a copy of original data before simulation
    const [originalHealthScore, setOriginalHealthScore] = useState<HealthScoreResponse | null>(null);

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

    return (
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
            <div className="sticky top-0 z-30 -mx-6 bg-canvas border-b border-white/5">
                <div className="px-6 py-3">
                    <CVPicker userId={userId} onLinked={fetchAll} />
                </div>
                {/* Progress bar — shown while refreshing */}
                <div className={`h-0.5 bg-accent-primary/20 overflow-hidden transition-opacity duration-300 ${refreshing ? 'opacity-100' : 'opacity-0'}`}>
                    <div className="h-full w-[40%] bg-accent-primary animate-progress" />
                </div>
            </div>

            {/* Metrics grid */}
            {noCvYet ? (
                <div className="rounded-2xl border border-accent-primary/20 bg-gradient-to-br from-accent-primary/10 to-accent-secondary/5 p-8">
                    <h2 className="text-lg font-bold font-outfit mb-2">👋 Chọn CV để bắt đầu</h2>
                    <p className="text-sm text-text-secondary leading-relaxed">
                        Chấm điểm CV theo <strong>8 chiều</strong> dựa trên dữ liệu thị trường thực
                        (~1.600 JD crawl ITviec + TopCV). Chọn CV ở trên rồi bấm <strong>Sync CV Health</strong>.
                    </p>
                </div>
            ) : (
                <div className={`space-y-6 transition-opacity duration-300 ${refreshing ? 'opacity-60' : 'opacity-100'}`}>
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
                    <FreshnessGauge data={healthScore} loading={loadingScore} />
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <FreshnessTimeSeriesChart data={history} loading={loadingHistory} />
                        <SkillAlertsCard data={alerts} loading={loadingAlerts} />
                    </div>
                    <OpportunityWindow data={opportunities} loading={loadingOpps} />
                </div>
            )}
        </div>
    );
}
