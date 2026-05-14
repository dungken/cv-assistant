import { useCallback, useEffect, useState } from 'react';
import { AxiosError } from 'axios';
import {
    cvHealthApi,
    type HealthScoreResponse,
    type FreshnessHistoryResponse,
    type SkillAlertsResponse,
    type OpportunityWindowResponse,
    type LearningPathResponse,
} from '../../../services/api';
import FreshnessGauge from './FreshnessGauge';
import FreshnessTimeSeriesChart from './FreshnessTimeSeriesChart';
import SkillAlertsCard from './SkillAlertsCard';
import OpportunityWindow from './OpportunityWindow';
import LearningPathView from './LearningPathView';
import CVPicker from './CVPicker';
import { Button } from '../../ui/Button';

interface Props {
    userId: string;
}

type Algo = 'greedy' | 'dijkstra' | 'dp';

export default function CVHealthDashboard({ userId }: Props) {
    const [healthScore, setHealthScore] = useState<HealthScoreResponse | null>(null);
    const [history, setHistory] = useState<FreshnessHistoryResponse | null>(null);
    const [alerts, setAlerts] = useState<SkillAlertsResponse | null>(null);
    const [opportunities, setOpportunities] = useState<OpportunityWindowResponse | null>(null);
    const [learningPath, setLearningPath] = useState<LearningPathResponse | null>(null);

    const [loadingScore, setLoadingScore] = useState(false);
    const [loadingHistory, setLoadingHistory] = useState(false);
    const [loadingAlerts, setLoadingAlerts] = useState(false);
    const [loadingOpps, setLoadingOpps] = useState(false);
    const [loadingPath, setLoadingPath] = useState(false);

    const [pathError, setPathError] = useState<string | null>(null);
    const [noCvYet, setNoCvYet] = useState(false);

    const [budgetWeeks, setBudgetWeeks] = useState(12);
    const [algorithm, setAlgorithm] = useState<Algo>('greedy');

    // Tracks whether we've finished the first round of fetches. Path fetch
    // waits for this so it can read the resolved `noCvYet` value instead of
    // racing the initial `false`.
    const [bootstrapped, setBootstrapped] = useState(false);

    const fetchAll = useCallback(async () => {
        setNoCvYet(false);
        setBootstrapped(false);
        setLoadingScore(true);
        setLoadingHistory(true);
        setLoadingAlerts(true);
        setLoadingOpps(true);

        // Parallel fan-out — each card renders independently so one failure
        // doesn't block the others (per §3.5 component isolation).
        const results = await Promise.allSettled([
            cvHealthApi.getHealthScore(userId, true),
            cvHealthApi.getFreshnessHistory(userId),
            cvHealthApi.getSkillAlerts(userId),
            cvHealthApi.getOpportunities(userId, { days: 7, limit: 10, minMatch: 0.5 }),
        ]);

        const [scoreRes, histRes, alertsRes, oppsRes] = results;
        let foundNoCv = false;
        if (scoreRes.status === 'fulfilled') {
            setHealthScore(scoreRes.value.data);
        } else if (scoreRes.reason instanceof AxiosError && scoreRes.reason.response?.status === 404) {
            foundNoCv = true;
            setHealthScore(null);
        }
        if (histRes.status === 'fulfilled') setHistory(histRes.value.data);
        if (alertsRes.status === 'fulfilled') setAlerts(alertsRes.value.data);
        // Opportunity also 404s when no CV — treat the same as health-score.
        if (oppsRes.status === 'fulfilled') {
            setOpportunities(oppsRes.value.data);
        } else if (oppsRes.reason instanceof AxiosError && oppsRes.reason.response?.status === 404) {
            foundNoCv = true;
            setOpportunities(null);
        }
        setNoCvYet(foundNoCv);

        setLoadingScore(false);
        setLoadingHistory(false);
        setLoadingAlerts(false);
        setLoadingOpps(false);
        setBootstrapped(true);
    }, [userId]);

    const fetchPath = useCallback(async (budget: number, algo: Algo) => {
        setLoadingPath(true);
        setPathError(null);
        try {
            const res = await cvHealthApi.getLearningPathMe(userId, {
                budgetWeeks: budget, algorithm: algo, days: 30, maxJds: 50,
            });
            setLearningPath(res.data);
        } catch (err) {
            if (err instanceof AxiosError) {
                const status = err.response?.status;
                // 404 = no CV stored yet; the banner above already explains this.
                // 422 = no JDs in the target window (no crawler data); show inline.
                if (status === 404) {
                    setPathError(null);
                } else {
                    const detail = (err.response?.data as { detail?: string } | undefined)?.detail;
                    setPathError(detail || err.message || 'Không tính được learning path.');
                }
            } else {
                setPathError('Không tính được learning path.');
            }
            setLearningPath(null);
        } finally {
            setLoadingPath(false);
        }
    }, [userId]);

    useEffect(() => {
        if (userId) fetchAll();
    }, [userId, fetchAll]);

    useEffect(() => {
        // Wait for fetchAll to settle so we know the CV exists before firing
        // POST /learning-path/me (which 404s when no CV is stored).
        if (userId && bootstrapped && !noCvYet) {
            fetchPath(budgetWeeks, algorithm);
        }
    }, [userId, bootstrapped, noCvYet, budgetWeeks, algorithm, fetchPath]);

    const handlePathConfigChange = (budget: number, algo: Algo) => {
        setBudgetWeeks(budget);
        setAlgorithm(algo);
    };

    const [showPicker, setShowPicker] = useState(false);

    return (
        <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
            <header className="flex items-end justify-between mb-2">
                <div>
                    <h1 className="text-3xl font-black font-outfit tracking-tight">
                        CV Health Intelligence
                    </h1>
                    <p className="text-sm text-text-secondary mt-1">
                        Theo dõi sức khỏe CV theo thị trường thực tế · user:{' '}
                        <span className="font-mono">{userId}</span>
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    {!noCvYet && (
                        <Button
                            onClick={() => setShowPicker(p => !p)}
                            variant="ghost"
                            size="sm"
                        >
                            {showPicker ? 'Đóng' : 'Đổi CV / role'}
                        </Button>
                    )}
                    <Button onClick={fetchAll} variant="secondary" size="sm">
                        Refresh
                    </Button>
                </div>
            </header>

            {(noCvYet || showPicker) && (
                <CVPicker
                    userId={userId}
                    onLinked={() => { setShowPicker(false); fetchAll(); }}
                />
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <FreshnessGauge data={healthScore} loading={loadingScore} />
                <FreshnessTimeSeriesChart data={history} loading={loadingHistory} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <SkillAlertsCard data={alerts} loading={loadingAlerts} />
                <OpportunityWindow data={opportunities} loading={loadingOpps} />
            </div>

            <LearningPathView
                data={learningPath}
                loading={loadingPath}
                error={pathError}
                budgetWeeks={budgetWeeks}
                algorithm={algorithm}
                onConfigChange={handlePathConfigChange}
            />
        </div>
    );
}
