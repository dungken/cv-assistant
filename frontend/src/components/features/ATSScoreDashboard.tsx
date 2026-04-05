import React from 'react';
import { 
  CheckCircle2, AlertCircle, XCircle, 
  Info, Target, Zap, TrendingUp, ArrowUpRight 
} from 'lucide-react';
import { 
  ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts';

interface ATSIssue {
  category: string;
  severity: 'high' | 'medium' | 'low';
  message: string;
  suggestion: string;
}

interface ATSScoreData {
  total_score: number;
  breakdown: Record<string, number>;
  issues: ATSIssue[];
  benchmark_avg: number;
}

interface ATSScoreDashboardProps {
  data: ATSScoreData;
  isLoading?: boolean;
}

const ATSScoreDashboard: React.FC<ATSScoreDashboardProps> = ({ data, isLoading }) => {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-4 animate-pulse">
        <div className="w-48 h-48 rounded-full bg-slate-800/50" />
        <div className="w-64 h-8 bg-slate-800/50 rounded" />
      </div>
    );
  }

  const { total_score, breakdown, issues, benchmark_avg } = data;

  // Pie chart data for the Gauge
  const gaugeData = [
    { value: total_score },
    { value: 100 - total_score }
  ];

  const getScoreColor = (score: number) => {
    if (score >= 80) return '#10b981'; // green-500
    if (score >= 60) return '#f59e0b'; // amber-500
    return '#ef4444'; // red-500
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high': return <XCircle className="w-5 h-5 text-red-500" />;
      case 'medium': return <AlertCircle className="w-5 h-5 text-amber-500" />;
      case 'low': return <Info className="w-5 h-5 text-blue-500" />;
      default: return <CheckCircle2 className="w-5 h-5 text-green-500" />;
    }
  };

  const barData = Object.entries(breakdown).map(([name, score]) => ({
    name: name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
    score
  }));

  const criticalCount = issues.filter(i => i.severity === 'high').length;
  const mediumCount = issues.filter(i => i.severity === 'medium').length;
  const lowCount = issues.filter(i => i.severity === 'low').length;

  return (
    <div className="space-y-5 animate-in fade-in slide-in-from-bottom-2 duration-500 pb-8 px-4 md:px-6">
      {/* Header & Gauge */}
      <div className="grid grid-cols-1 md:grid-cols-[340px_1fr] gap-5 items-center bg-surface/35 p-5 md:p-6 rounded-2xl border border-main-border/70">
        <div className="relative flex justify-center items-center h-44">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={gaugeData}
                cx="50%"
                cy="85%"
                startAngle={210}
                endAngle={-30}
                innerRadius={62}
                outerRadius={78}
                paddingAngle={0}
                dataKey="value"
                stroke="none"
                animationDuration={900}
                animationBegin={100}
              >
                <Cell fill={getScoreColor(total_score)} />
                <Cell fill="rgba(var(--bg-overlay), 0.14)" />
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex flex-col items-center justify-end pb-5">
            <span className="text-5xl font-black tracking-tight text-text-primary">
              {total_score}
            </span>
            <span className="text-[10px] font-bold uppercase tracking-[0.16em] text-text-muted mt-0.5">
              ATS Score
            </span>
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-xl bg-accent-primary/10 border border-accent-primary/20">
              <TrendingUp className="w-5 h-5 text-accent-primary" />
            </div>
            <div>
              <h3 className="text-lg font-black text-text-primary">Analysis Summary</h3>
              <p className="text-sm text-text-secondary leading-relaxed mt-1">
                Your CV is <span className="font-bold text-text-primary">{total_score > benchmark_avg ? 'above' : 'below'}</span> the industry average of <span className="font-bold">{benchmark_avg}</span>.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="p-4 rounded-xl bg-surface/45 border border-main-border/70">
              <p className="text-[10px] font-bold text-text-muted uppercase tracking-[0.16em] mb-1">Critical</p>
              <div className="flex items-center gap-2 text-red-500">
                <p className="text-2xl font-black">{criticalCount}</p>
                <AlertCircle className="w-4 h-4 opacity-70" />
              </div>
            </div>
            <div className="p-4 rounded-xl bg-surface/45 border border-main-border/70">
              <p className="text-[10px] font-bold text-text-muted uppercase tracking-[0.16em] mb-1">Potential</p>
              <div className="flex items-center gap-2 text-emerald-500">
                <p className="text-2xl font-black">+{100 - total_score}</p>
                <Zap className="w-4 h-4 opacity-70" />
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs text-text-secondary">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-red-500/10 text-red-400 border border-red-500/20">
              High {criticalCount}
            </span>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
              Medium {mediumCount}
            </span>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
              Low {lowCount}
            </span>
          </div>
        </div>
      </div>

      {/* Breakdown Chart */}
      <div className="p-5 md:p-6 rounded-2xl bg-surface/35 border border-main-border/70">
        <h3 className="text-xs font-bold text-text-muted uppercase tracking-[0.16em] mb-4">
          Score Breakdown
        </h3>
        <div className="space-y-4">
          {barData.map((item) => (
            <div key={item.name}>
              <div className="flex items-center justify-between mb-1.5">
                <p className="text-sm text-text-secondary font-medium">{item.name}</p>
                <p className="text-sm text-text-primary font-bold">{item.score}</p>
              </div>
              <div className="h-2.5 rounded-full bg-surface-hover/60 overflow-hidden">
                <div
                  className="h-full rounded-full bg-linear-to-r from-indigo-500 via-violet-500 to-fuchsia-500 transition-all duration-700"
                  style={{ width: `${Math.max(0, Math.min(100, item.score))}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Priority Issues */}
      <div className="space-y-3">
        <h3 className="text-xs font-bold text-text-muted uppercase tracking-[0.16em] flex items-center gap-2">
          <Target className="w-4 h-4" /> Optimization Roadmap
        </h3>

        <div className="grid grid-cols-1 gap-3">
          {issues.map((issue, idx) => (
            <div 
              key={idx}
              className="p-4 rounded-xl bg-surface/35 border border-main-border/70 hover:border-accent-primary/35 transition-colors"
            >
              <div className="flex items-start gap-3">
                <div className="mt-0.5 p-2 rounded-lg bg-surface/80 border border-main-border/60">
                  {getSeverityIcon(issue.severity)}
                </div>
                <div className="flex-1 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-text-primary text-sm md:text-base pr-3">{issue.message}</h4>
                    <span className={`text-[10px] uppercase font-bold px-2 py-1 rounded-md border shrink-0 ${
                      issue.severity === 'high' ? 'bg-red-500/10 text-red-500 border-red-500/20' :
                      issue.severity === 'medium' ? 'bg-amber-500/10 text-amber-500 border-amber-500/20' :
                      'bg-blue-500/10 text-accent-primary border-accent-primary/20'
                    }`}>
                      {issue.severity}
                    </span>
                  </div>
                  <p className="text-sm text-text-secondary leading-relaxed">
                    <span className="text-accent-primary font-semibold mr-1.5">Tip:</span>
                    {issue.suggestion}
                  </p>
                </div>
                <div className="mt-0.5">
                  <ArrowUpRight className="w-4 h-4 text-text-muted" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>

  );
};

export default ATSScoreDashboard;
