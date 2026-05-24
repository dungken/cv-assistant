import { useEffect, useMemo, useRef, useState } from 'react';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, Legend, LineChart, Line, AreaChart, Area, CartesianGrid,
} from 'recharts';
import { Search, RefreshCw, TrendingUp, TrendingDown, Database, Briefcase, GraduationCap, MapPin, Building2, DollarSign, Sparkles, Layers, Compass, Zap, Wifi, Gem, LineChart as LineIcon, Target, Flame, Award, Languages, CalendarDays, AlertTriangle, Crown, Network } from 'lucide-react';
import { skillApi, type MarketIntelDashboard } from '../../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/Card';

const PALETTE = [
    '#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f97316',
    '#eab308', '#84cc16', '#10b981', '#06b6d4', '#3b82f6',
    '#a855f7', '#d946ef',
];

interface Filters {
    source: string;
    role_group: string;
    seniority: string;
}

const EMPTY_FILTERS: Filters = { source: 'all', role_group: '', seniority: '' };


export default function MarketIntelDashboardView() {
    const [data, setData] = useState<MarketIntelDashboard | null>(null);
    const [compareData, setCompareData] = useState<MarketIntelDashboard | null>(null);
    const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
    const [compareRole, setCompareRole] = useState<string>('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [skillSearch, setSkillSearch] = useState('');

    const fetchData = (f: Filters, _signal?: AbortSignal) =>
        skillApi.getMarketIntelDashboard({
            source: f.source || undefined,
            role_group: f.role_group || undefined,
            seniority: f.seniority || undefined,
        }).then((r: any) => r.data);

    useEffect(() => {
        const ctrl = new AbortController();
        setLoading(true);
        setError(null);
        fetchData(filters, ctrl.signal)
            .then(setData)
            .catch((e) => { if (e?.name !== 'CanceledError') setError(e?.message ?? 'Lỗi tải dữ liệu'); })
            .finally(() => setLoading(false));
        return () => ctrl.abort();
    }, [filters]);

    useEffect(() => {
        if (!compareRole) { setCompareData(null); return; }
        const ctrl = new AbortController();
        fetchData({ ...filters, role_group: compareRole }, ctrl.signal)
            .then(setCompareData)
            .catch(() => { /* compare is best-effort */ });
        return () => ctrl.abort();
    }, [compareRole, filters.source, filters.seniority]);

    if (loading && !data) return <SkeletonDashboard />;
    if (error) return <div className="p-8 text-center text-red-400">{error}</div>;
    if (!data) return null;

    const filteredTopSkills = skillSearch
        ? data.top_skills.filter((s) => s.skill.toLowerCase().includes(skillSearch.toLowerCase()))
        : data.top_skills;

    return (
        <div className="relative min-h-full">
            {/* Ambient gradient background — bỏ blur-[160px] để tránh repaint nặng khi scroll */}

            <div className="max-w-7xl mx-auto p-6 space-y-6">
                <header className="pt-2">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
                            <TrendingUp className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-black font-outfit tracking-tight">Market Intelligence</h1>
                            <p className="text-text-secondary text-sm">Phân tích thị trường tuyển dụng IT Việt Nam</p>
                        </div>
                    </div>
                    <p className="text-text-secondary text-sm pl-15">
                        Dữ liệu tổng hợp từ <b className="text-text-primary">{data.kpis.total_jds.toLocaleString()}</b> JD ·
                        {' '}<b className="text-text-primary">{data.kpis.total_companies.toLocaleString()}</b> công ty
                        {data.kpis.earliest_post && data.kpis.latest_post && (
                            <> · giai đoạn <b className="text-text-primary">{data.kpis.earliest_post}</b> → <b className="text-text-primary">{data.kpis.latest_post}</b></>
                        )}
                    </p>
                </header>

                {/* Sticky filter bar */}
                <div className="sticky top-0 z-20 -mx-6 px-6 py-3 bg-canvas border-b border-white/5">
                    <FiltersBar
                        filters={filters}
                        options={data.options}
                        onChange={setFilters}
                        onReset={() => { setFilters(EMPTY_FILTERS); setCompareRole(''); setSkillSearch(''); }}
                        compareRole={compareRole}
                        onCompareChange={setCompareRole}
                        loading={loading}
                    />
                </div>

                <KpiCards data={data} compareData={compareData} />

                {/* Daily trend (full width line chart) */}
                <ChartCard
                    title="Xu hướng đăng JD 30 ngày gần nhất"
                    subtitle="Theo dõi nhịp tuyển dụng của thị trường"
                    icon={<TrendingUp className="w-4 h-4" />}
                >
                    <DailyTrendChart rows={data.daily_trend} compareRows={compareData?.daily_trend} compareLabel={compareRole} />
                </ChartCard>

                {/* Velocity (full width — trending up vs down) */}
                <ChartCard
                    title="Kỹ năng đang nóng / nguội"
                    subtitle="So sánh 14 ngày gần nhất với 14 ngày trước đó · skills bùng nổ tuyển dụng"
                    icon={<Zap className="w-4 h-4" />}
                >
                    <VelocityChart data={data.skill_velocity} />
                </ChartCard>

                {/* Premium index (full width) */}
                <ChartCard
                    title="Skill Premium Index — Skill nào trả lương cao?"
                    subtitle="So với median salary toàn thị trường (USD) · cần ≥5 JD/skill để tính"
                    icon={<DollarSign className="w-4 h-4" />}
                >
                    <PremiumChart data={data.skill_premium} />
                </ChartCard>

                {/* Skill clusters (full width insight cards) */}
                <ChartCard
                    title="Stack thực tế thị trường tuyển dụng"
                    subtitle={`${data.skill_clusters.length} cluster · skills hay đi cùng nhau với Jaccard ≥ 0.15`}
                    icon={<Layers className="w-4 h-4" />}
                >
                    <ClusterChart clusters={data.skill_clusters} />
                </ChartCard>

                {/* English Premium — single hero KPI */}
                {data.english_premium && (
                    <ChartCard
                        title="English Premium — Tiếng Anh đáng giá bao nhiêu?"
                        subtitle="So sánh median lương JD yêu cầu English vs không"
                        icon={<Languages className="w-4 h-4" />}
                    >
                        <EnglishPremiumHero data={data.english_premium} />
                    </ChartCard>
                )}

                {/* Hidden Gems Quadrant (full width scatter) */}
                <ChartCard
                    title="💎 Hidden Gem Skills — Ít cạnh tranh, lương cao"
                    subtitle="Scatter: trục X = số JD (demand) · trục Y = median lương · ô trên-trái = HIDDEN GEM"
                    icon={<Gem className="w-4 h-4" />}
                >
                    <QuadrantChart quadrants={data.skill_quadrants} gems={data.hidden_gems} />
                </ChartCard>

                {/* Salary curve by experience */}
                <ChartCard
                    title="📈 Career ROI — Lương tăng theo kinh nghiệm"
                    subtitle="Median salary qua từng cấp · các đường role khác nhau"
                    icon={<LineIcon className="w-4 h-4" />}
                >
                    <SalaryCurveChart curve={data.salary_curve} />
                </ChartCard>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <ChartCard
                        title="Top kỹ năng được tuyển nhiều nhất"
                        subtitle={`${data.top_skills.length} skills · gõ để lọc`}
                        icon={<Search className="w-4 h-4" />}
                        action={
                            <input
                                value={skillSearch}
                                onChange={(e) => setSkillSearch(e.target.value)}
                                placeholder="Tìm skill..."
                                className="text-xs rounded-lg border border-white/10 bg-surface/40 px-2 py-1 w-32"
                            />
                        }
                    >
                        <TopSkillsChart rows={filteredTopSkills} />
                    </ChartCard>

                    <ChartCard title="Phân bố nhóm vai trò" subtitle="Web · Data · Mobile · DevOps · ..." icon={<Briefcase className="w-4 h-4" />}>
                        <RoleDistributionChart rows={data.role_distribution} />
                    </ChartCard>

                    <ChartCard title="Top 15 công ty tuyển nhiều nhất" subtitle="Theo số JD đang mở" icon={<Building2 className="w-4 h-4" />}>
                        <TopCompaniesChart rows={data.top_companies} />
                    </ChartCard>

                    <ChartCard title="Số năm kinh nghiệm yêu cầu" subtitle="JD nào nhận fresher?" icon={<Database className="w-4 h-4" />}>
                        <ExpHistogramChart rows={data.exp_histogram} />
                    </ChartCard>

                    <ChartCard title="Cấp độ kinh nghiệm" subtitle="Junior / Mid / Senior / Lead">
                        <SeniorityChart rows={data.seniority_distribution} />
                    </ChartCard>

                    <ChartCard title="Hình thức làm việc" subtitle="Onsite / Hybrid / Remote">
                        <WorkModeChart rows={data.work_mode_distribution} />
                    </ChartCard>

                    <ChartCard title="Yêu cầu bằng cấp" subtitle="Cử nhân / Cao đẳng / Master / ..." icon={<GraduationCap className="w-4 h-4" />}>
                        <DegreeChart rows={data.degree_distribution} />
                    </ChartCard>

                    <ChartCard title="Top 10 địa điểm tuyển dụng" subtitle="Theo số JD" icon={<MapPin className="w-4 h-4" />}>
                        <LocationChart rows={data.top_locations} />
                    </ChartCard>

                    <ChartCard title="Mức lương theo cấp độ" subtitle="Median min/max · giữ nguyên đơn vị nguồn (USD/VND)">
                        <SalaryChart rows={data.salary_by_seniority} />
                    </ChartCard>

                    <ChartCard title="Cặp kỹ năng đi cùng nhau" subtitle="Skills hay xuất hiện song song trong JD">
                        <SkillPairsChart rows={data.skill_pairs} />
                    </ChartCard>

                    <ChartCard
                        title="Lương theo nhóm vai trò"
                        subtitle="Median ± P25-P75 (USD) · vai trò nào trả cao nhất"
                        icon={<Briefcase className="w-4 h-4" />}
                    >
                        <RoleSalaryChart rows={data.role_salary} />
                    </ChartCard>

                    <ChartCard
                        title="Lương theo bằng cấp"
                        subtitle="Median salary theo trình độ học vấn yêu cầu"
                        icon={<GraduationCap className="w-4 h-4" />}
                    >
                        <EduSalaryChart rows={data.edu_salary} />
                    </ChartCard>

                    <ChartCard
                        title="Lương theo địa điểm"
                        subtitle="3 thành phố lớn · Median + dải P25-P75 (USD)"
                        icon={<Compass className="w-4 h-4" />}
                    >
                        <GeoSalaryChart rows={data.geo_salary} />
                    </ChartCard>

                    <ChartCard
                        title="Skill nào dễ remote nhất?"
                        subtitle="% JD remote hoặc hybrid · trên top 15 skills"
                        icon={<Wifi className="w-4 h-4" />}
                    >
                        <RemoteSkillChart rows={data.remote_by_skill} />
                    </ChartCard>

                    <ChartCard
                        title="Skills theo từng cấp kinh nghiệm"
                        subtitle="Fresher cần gì, Senior cần gì"
                        icon={<Sparkles className="w-4 h-4" />}
                    >
                        <SkillsByExpChart data={data.skills_by_exp} />
                    </ChartCard>

                    <ChartCard
                        title="Công ty hàng đầu theo Skill"
                        subtitle="Click skill để xem 3 công ty tuyển nhiều nhất"
                        icon={<Building2 className="w-4 h-4" />}
                    >
                        <CompaniesBySkillChart data={data.companies_by_skill} />
                    </ChartCard>

                    <ChartCard
                        title="🎯 Skill Specificity Tier"
                        subtitle="Core (>30% JD) · Common (10-30%) · Specialized (<10%)"
                        icon={<Target className="w-4 h-4" />}
                    >
                        <SpecificityChart rows={data.skill_specificity} />
                    </ChartCard>

                    <ChartCard
                        title="🔥 Hot Companies tháng này"
                        subtitle="Velocity 14d cuối so với 14d trước · cty đang scale"
                        icon={<Flame className="w-4 h-4" />}
                    >
                        <HotCompaniesChart rows={data.hot_companies} />
                    </ChartCard>

                    <ChartCard
                        title="🏆 Combo Skill Premium"
                        subtitle="Lương khi có cả 2 skill vs trung bình từng skill riêng"
                        icon={<Award className="w-4 h-4" />}
                    >
                        <ComboSalaryChart rows={data.combo_salary} />
                    </ChartCard>

                    <ChartCard
                        title="📅 Thứ mấy đăng JD nhiều nhất?"
                        subtitle="60 ngày gần nhất · biết khi nào nên check job board"
                        icon={<CalendarDays className="w-4 h-4" />}
                    >
                        <DayOfWeekChart rows={data.day_of_week} />
                    </ChartCard>

                    <ChartCard
                        title="⚠️ Skill đang nguội"
                        subtitle="Skills giảm post tuyển dụng trong 2 tuần gần nhất"
                        icon={<AlertTriangle className="w-4 h-4" />}
                    >
                        <OutdatedSkillsChart rows={data.outdated_skills} />
                    </ChartCard>

                    <ChartCard
                        title="👑 Niche Champions"
                        subtitle="Công ty tuyển nhiều skill hiếm (3-25 JD/skill)"
                        icon={<Crown className="w-4 h-4" />}
                    >
                        <NicheChampionsChart rows={data.niche_champions} />
                    </ChartCard>
                </div>

                {/* Skill Network full-width visualization */}
                <ChartCard
                    title="🕸️ Mạng lưới kết nối Skills"
                    subtitle={`Force-style network · ${data.skill_network.nodes.length} skills, ${data.skill_network.edges.length} edges`}
                    icon={<Network className="w-4 h-4" />}
                >
                    <SkillNetworkChart network={data.skill_network} />
                </ChartCard>

                <ChartCard
                    title="Heatmap kỹ năng × nhóm vai trò"
                    subtitle="Top 10 skill × Top 6 role · ô đậm = nhu cầu cao"
                >
                    <Heatmap rows={data.heatmap} />
                </ChartCard>

                <SourceBreakdownBar rows={data.source_breakdown} />

                <footer className="text-center text-text-secondary text-xs py-4">
                    Dữ liệu cập nhật mỗi lần crawl · cache 5 phút server-side
                </footer>
            </div>
        </div>
    );
}


// ── filters bar with compare ────────────────────────────────────

function FiltersBar({
    filters, options, onChange, onReset, compareRole, onCompareChange, loading,
}: {
    filters: Filters;
    options: MarketIntelDashboard['options'];
    onChange: (f: Filters) => void;
    onReset: () => void;
    compareRole: string;
    onCompareChange: (s: string) => void;
    loading: boolean;
}) {
    const inputCls = "rounded-xl border border-white/10 bg-surface/40 px-3 py-2 text-sm focus:border-accent-primary/50 focus:outline-none transition";
    return (
        <div className="flex flex-wrap items-end gap-3">
            <FilterSelect label="Nguồn" value={filters.source} cls={inputCls}
                onChange={(v) => onChange({ ...filters, source: v })}
                options={[{ v: 'all', label: 'Tất cả' }, ...options.sources.map((s) => ({ v: s, label: s }))]} />
            <FilterSelect label="Nhóm vai trò" value={filters.role_group} cls={inputCls}
                onChange={(v) => onChange({ ...filters, role_group: v })}
                options={[{ v: '', label: 'Tất cả' }, ...options.role_groups.map((s) => ({ v: s, label: prettify(s) }))]} />
            <FilterSelect label="Cấp độ" value={filters.seniority} cls={inputCls}
                onChange={(v) => onChange({ ...filters, seniority: v })}
                options={[{ v: '', label: 'Tất cả' }, ...options.seniorities.map((s) => ({ v: s, label: s }))]} />

            <div className="h-9 w-px bg-white/10 mx-2" />

            <FilterSelect label="So sánh với role" value={compareRole} cls={inputCls}
                onChange={onCompareChange}
                options={[{ v: '', label: 'Không' }, ...options.role_groups.map((s) => ({ v: s, label: prettify(s) }))]} />

            <button
                onClick={onReset}
                className="ml-auto inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm bg-surface-hover/50 hover:bg-surface-hover transition">
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                Reset
            </button>
        </div>
    );
}

function FilterSelect({ label, value, onChange, options, cls }: {
    label: string; value: string; onChange: (v: string) => void;
    options: { v: string; label: string }[]; cls: string;
}) {
    return (
        <div>
            <label className="block text-[10px] uppercase tracking-wider text-text-secondary mb-1 font-semibold">{label}</label>
            <select className={cls} value={value} onChange={(e) => onChange(e.target.value)}>
                {options.map((o) => <option key={o.v} value={o.v}>{o.label}</option>)}
            </select>
        </div>
    );
}


// ── KPI cards w/ animated counter + sparkline ──────────────────

function KpiCards({ data, compareData }: { data: MarketIntelDashboard; compareData: MarketIntelDashboard | null }) {
    const trendSeries = data.daily_trend.map((d) => d.cnt);

    const items: { label: string; value: number; sub?: string; spark?: number[] }[] = [
        { label: 'Tổng JD', value: data.kpis.total_jds, sub: '30 ngày qua', spark: trendSeries },
        { label: 'Công ty', value: data.kpis.total_companies },
        { label: 'Kỹ năng độc lập', value: data.kpis.unique_skills },
        { label: 'Nguồn dữ liệu', value: data.kpis.total_sources, sub: data.source_breakdown.map((s) => s.source).join(' · ') },
    ];

    return (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {items.map((it, i) => {
                const compareValue = compareData ? [compareData.kpis.total_jds, compareData.kpis.total_companies, compareData.kpis.unique_skills, compareData.kpis.total_sources][i] : null;
                return (
                    <Card key={it.label} className="overflow-hidden relative">
                        <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-transparent via-accent-primary/40 to-transparent" />
                        <CardContent className="pt-6 pb-5">
                            <div className="text-text-secondary text-xs uppercase tracking-wider font-semibold">{it.label}</div>
                            <div className="text-3xl font-black mt-1 font-outfit">
                                <AnimatedNumber to={it.value} />
                            </div>
                            {it.sub && <div className="text-[10px] text-text-secondary mt-0.5">{it.sub}</div>}
                            {compareValue !== null && (
                                <div className="text-[11px] mt-1 flex items-center gap-1">
                                    <span className="text-text-secondary">So với role chọn:</span>
                                    <CompareDelta from={it.value} to={compareValue} />
                                </div>
                            )}
                            {it.spark && it.spark.length > 1 && (
                                <div className="mt-3 -mx-2">
                                    <Sparkline data={it.spark} />
                                </div>
                            )}
                        </CardContent>
                    </Card>
                );
            })}
        </div>
    );
}

function AnimatedNumber({ to, durationMs = 800 }: { to: number; durationMs?: number }) {
    const [v, setV] = useState(0);
    const fromRef = useRef(0);
    useEffect(() => {
        const start = performance.now();
        const from = fromRef.current;
        let raf = 0;
        const step = (now: number) => {
            const t = Math.min(1, (now - start) / durationMs);
            const eased = 1 - Math.pow(1 - t, 3);
            setV(Math.round(from + (to - from) * eased));
            if (t < 1) raf = requestAnimationFrame(step);
            else fromRef.current = to;
        };
        raf = requestAnimationFrame(step);
        return () => cancelAnimationFrame(raf);
    }, [to, durationMs]);
    return <span>{v.toLocaleString()}</span>;
}

function CompareDelta({ from, to }: { from: number; to: number }) {
    if (!from) return <span className="text-text-secondary">—</span>;
    const pct = ((to - from) / from) * 100;
    const Icon = pct >= 0 ? TrendingUp : TrendingDown;
    return (
        <span className={pct >= 0 ? 'text-emerald-400 inline-flex items-center gap-0.5' : 'text-rose-400 inline-flex items-center gap-0.5'}>
            <Icon className="w-3 h-3" />
            {pct >= 0 ? '+' : ''}{pct.toFixed(0)}%
        </span>
    );
}

function Sparkline({ data }: { data: number[] }) {
    if (data.length < 2) return null;
    const pts = data.map((v, i) => ({ x: i, y: v }));
    return (
        <ResponsiveContainer width="100%" height={32}>
            <AreaChart data={pts}>
                <defs>
                    <linearGradient id="spark" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#6366f1" stopOpacity={0.6} />
                        <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                    </linearGradient>
                </defs>
                <Area type="monotone" dataKey="y" stroke="#6366f1" fill="url(#spark)" strokeWidth={1.5} dot={false} />
            </AreaChart>
        </ResponsiveContainer>
    );
}


// ── chart card wrapper ──────────────────────────────────────────

function ChartCard({ title, subtitle, children, icon, action }: {
    title: string; subtitle?: string; children: React.ReactNode;
    icon?: React.ReactNode; action?: React.ReactNode;
}) {
    return (
        <Card>
            <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-2 min-w-0">
                        {icon && <span className="mt-1 text-accent-primary opacity-80">{icon}</span>}
                        <div className="min-w-0">
                            <CardTitle className="text-lg truncate">{title}</CardTitle>
                            {subtitle && <CardDescription className="text-xs">{subtitle}</CardDescription>}
                        </div>
                    </div>
                    {action}
                </div>
            </CardHeader>
            <CardContent className="pt-0">{children}</CardContent>
        </Card>
    );
}


// ── individual charts ──────────────────────────────────────────

function DailyTrendChart({ rows, compareRows, compareLabel }: {
    rows: { day: string; cnt: number }[];
    compareRows?: { day: string; cnt: number }[];
    compareLabel?: string;
}) {
    if (!rows.length) return <Empty />;
    const map = new Map(rows.map((r) => [r.day, r.cnt]));
    const cmpMap = new Map((compareRows || []).map((r) => [r.day, r.cnt]));
    const merged = rows.map((r) => ({
        day: r.day.slice(5),
        current: map.get(r.day) ?? 0,
        compare: cmpMap.get(r.day) ?? null,
    }));
    return (
        <ResponsiveContainer width="100%" height={260}>
            <LineChart data={merged} margin={{ left: -10, right: 10, top: 10 }}>
                <defs>
                    <linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#6366f1" stopOpacity={0.3} />
                        <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                    </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="day" tick={{ fontSize: 11, fill: '#999' }} />
                <YAxis tick={{ fontSize: 11, fill: '#999' }} />
                <Tooltip content={<DarkTooltip />} />
                <Line type="monotone" dataKey="current" stroke="#6366f1" strokeWidth={2.5} dot={{ r: 3 }} activeDot={{ r: 5 }} name="JD đăng" />
                {compareRows && compareRows.length > 0 && (
                    <Line type="monotone" dataKey="compare" stroke="#ec4899" strokeWidth={2} strokeDasharray="5 5" dot={false} name={prettify(compareLabel || 'so sánh')} />
                )}
            </LineChart>
        </ResponsiveContainer>
    );
}

function TopSkillsChart({ rows }: { rows: { skill: string; cnt: number }[] }) {
    if (!rows.length) return <Empty />;
    const max = Math.max(...rows.map((r) => r.cnt));
    return (
        <div className="space-y-1.5">
            {rows.map((r, i) => (
                <div key={r.skill} className="group">
                    <div className="flex items-center justify-between text-xs mb-0.5">
                        <span className="font-medium truncate">{r.skill}</span>
                        <span className="text-text-secondary tabular-nums">{r.cnt}</span>
                    </div>
                    <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                        <div
                            className="h-full rounded-full transition-all duration-500 group-hover:brightness-125"
                            style={{
                                width: `${(r.cnt / max) * 100}%`,
                                background: `linear-gradient(90deg, ${PALETTE[i % PALETTE.length]}, ${PALETTE[(i + 3) % PALETTE.length]})`,
                            }}
                        />
                    </div>
                </div>
            ))}
        </div>
    );
}

function RoleDistributionChart({ rows }: { rows: { role_group: string; cnt: number }[] }) {
    if (!rows.length) return <Empty />;
    const total = rows.reduce((s, r) => s + r.cnt, 0) || 1;
    const data = rows.map((r) => ({ name: prettify(r.role_group), value: r.cnt }));
    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 items-center">
            <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                    <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%"
                        outerRadius={100} innerRadius={55} paddingAngle={2}>
                        {data.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
                    </Pie>
                    <Tooltip content={<DarkTooltip />} />
                </PieChart>
            </ResponsiveContainer>
            <div className="space-y-1.5 max-h-[260px] overflow-y-auto pr-1">
                {data.map((d, i) => {
                    const pct = (d.value / total) * 100;
                    return (
                        <div key={d.name} className="flex items-center gap-2 text-xs">
                            <span className="w-2.5 h-2.5 rounded-sm shrink-0" style={{ backgroundColor: PALETTE[i % PALETTE.length] }} />
                            <span className="flex-1 truncate font-medium" title={d.name}>{d.name}</span>
                            <span className="text-text-secondary tabular-nums">{d.value}</span>
                            <span className="text-text-secondary tabular-nums w-10 text-right">{pct.toFixed(1)}%</span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

function TopCompaniesChart({ rows }: { rows: { company: string; cnt: number }[] }) {
    if (!rows.length) return <Empty />;
    // Trim aggressively + render as horizontal progress bars (not Recharts
    // BarChart) so each row gets a generous fixed height regardless of how
    // recharts decides to layout its categorical Y axis.
    const max = Math.max(...rows.map((r) => r.cnt));
    return (
        <div className="space-y-2.5">
            {rows.map((r, i) => {
                const label = r.company.length > 38 ? r.company.slice(0, 38) + '…' : r.company;
                return (
                    <div key={r.company} className="group flex items-center gap-3">
                        <span className="text-xs font-medium truncate w-44 shrink-0" title={r.company}>{label}</span>
                        <div className="flex-1 h-2.5 rounded-full bg-white/5 overflow-hidden">
                            <div
                                className="h-full rounded-full transition-all duration-500 group-hover:brightness-125"
                                style={{
                                    width: `${(r.cnt / max) * 100}%`,
                                    background: `linear-gradient(90deg, ${PALETTE[i % PALETTE.length]}, ${PALETTE[(i + 3) % PALETTE.length]})`,
                                }}
                            />
                        </div>
                        <span className="text-xs text-text-secondary tabular-nums w-8 text-right shrink-0">{r.cnt}</span>
                    </div>
                );
            })}
        </div>
    );
}

function ExpHistogramChart({ rows }: { rows: { bucket: string; cnt: number }[] }) {
    if (!rows.length) return <EmptyNote msg="Chưa trích xuất kinh nghiệm cho nguồn này." />;
    return (
        <ResponsiveContainer width="100%" height={280}>
            <BarChart data={rows}>
                <CartesianGrid stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="bucket" tick={{ fontSize: 11, fill: '#999' }} />
                <YAxis tick={{ fontSize: 11, fill: '#999' }} />
                <Tooltip content={<DarkTooltip />} />
                <Bar dataKey="cnt" fill="#f97316" radius={[8, 8, 0, 0]} />
            </BarChart>
        </ResponsiveContainer>
    );
}

function SeniorityChart({ rows }: { rows: { seniority: string; cnt: number }[] }) {
    if (!rows.length) return <EmptyNote msg="Cấp độ chưa trích xuất cho nguồn này." />;
    return (
        <ResponsiveContainer width="100%" height={280}>
            <BarChart data={rows}>
                <CartesianGrid stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="seniority" tick={{ fontSize: 11, fill: '#999' }} />
                <YAxis tick={{ fontSize: 11, fill: '#999' }} />
                <Tooltip content={<DarkTooltip />} />
                <Bar dataKey="cnt" fill="#10b981" radius={[8, 8, 0, 0]} />
            </BarChart>
        </ResponsiveContainer>
    );
}

function WorkModeChart({ rows }: { rows: { work_mode: string; cnt: number }[] }) {
    if (!rows.length) return <EmptyNote msg="Hình thức làm việc chưa trích xuất cho nguồn này." />;
    const data = rows.map((r) => ({ name: r.work_mode, value: r.cnt }));
    return <DonutWithLegend data={data} colorOffset={0} />;
}

function DegreeChart({ rows }: { rows: { degree_norm: string; cnt: number }[] }) {
    if (!rows.length) return <EmptyNote msg="Bằng cấp chưa trích xuất cho nguồn này." />;
    const data = rows.map((r) => ({ name: r.degree_norm, value: r.cnt }));
    return <DonutWithLegend data={data} colorOffset={4} />;
}

function DonutWithLegend({ data, colorOffset = 0 }: { data: { name: string; value: number }[]; colorOffset?: number }) {
    const total = data.reduce((s, r) => s + r.value, 0) || 1;
    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 items-center">
            <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                    <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%"
                        innerRadius={55} outerRadius={95} paddingAngle={3}>
                        {data.map((_, i) => <Cell key={i} fill={PALETTE[(i + colorOffset) % PALETTE.length]} />)}
                    </Pie>
                    <Tooltip content={<DarkTooltip />} />
                </PieChart>
            </ResponsiveContainer>
            <div className="space-y-1.5">
                {data.map((d, i) => {
                    const pct = (d.value / total) * 100;
                    return (
                        <div key={d.name} className="flex items-center gap-2 text-xs">
                            <span className="w-2.5 h-2.5 rounded-sm shrink-0" style={{ backgroundColor: PALETTE[(i + colorOffset) % PALETTE.length] }} />
                            <span className="flex-1 truncate font-medium" title={d.name}>{d.name}</span>
                            <span className="text-text-secondary tabular-nums">{d.value}</span>
                            <span className="text-text-secondary tabular-nums w-10 text-right">{pct.toFixed(1)}%</span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

function SalaryChart({ rows }: { rows: MarketIntelDashboard['salary_by_seniority'] }) {
    if (!rows.length) return <EmptyNote msg="Chưa đủ dữ liệu lương để tổng hợp." />;
    const data = rows.map((r) => ({
        name: `${r.seniority} (${r.currency ?? '?'})`,
        median_min: r.median_min ?? 0,
        median_max: r.median_max ?? 0,
        cnt: r.cnt,
    }));
    return (
        <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data}>
                <CartesianGrid stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#999' }} />
                <YAxis tick={{ fontSize: 11, fill: '#999' }} />
                <Tooltip content={<DarkTooltip />} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="median_min" name="Median min" fill="#06b6d4" radius={[6, 6, 0, 0]} />
                <Bar dataKey="median_max" name="Median max" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
            </BarChart>
        </ResponsiveContainer>
    );
}

function LocationChart({ rows }: { rows: { location: string; cnt: number }[] }) {
    if (!rows.length) return <Empty />;
    return (
        <ResponsiveContainer width="100%" height={Math.max(280, rows.length * 28)}>
            <BarChart data={rows} layout="vertical" margin={{ left: 80 }}>
                <CartesianGrid stroke="rgba(255,255,255,0.04)" />
                <XAxis type="number" tick={{ fontSize: 11, fill: '#999' }} />
                <YAxis dataKey="location" type="category" width={130} tick={{ fontSize: 11, fill: '#bbb' }} />
                <Tooltip content={<DarkTooltip />} />
                <Bar dataKey="cnt" fill="#f97316" radius={[0, 6, 6, 0]} />
            </BarChart>
        </ResponsiveContainer>
    );
}

function SkillPairsChart({ rows }: { rows: { skill_a: string; skill_b: string; cnt: number }[] }) {
    if (!rows.length) return <Empty />;
    const max = Math.max(...rows.map((r) => r.cnt));
    return (
        <div className="space-y-2">
            {rows.map((r, i) => (
                <div key={`${r.skill_a}-${r.skill_b}`} className="flex items-center gap-2 text-xs p-2 rounded-lg bg-white/[0.02] hover:bg-white/5 transition">
                    <span className="px-2 py-0.5 rounded-md font-medium" style={{ backgroundColor: PALETTE[i % PALETTE.length] + '33', color: PALETTE[i % PALETTE.length] }}>
                        {r.skill_a}
                    </span>
                    <span className="text-text-secondary">+</span>
                    <span className="px-2 py-0.5 rounded-md font-medium" style={{ backgroundColor: PALETTE[(i + 4) % PALETTE.length] + '33', color: PALETTE[(i + 4) % PALETTE.length] }}>
                        {r.skill_b}
                    </span>
                    <div className="flex-1 ml-2 h-1.5 rounded-full bg-white/5 overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-indigo-500 to-purple-500" style={{ width: `${(r.cnt / max) * 100}%` }} />
                    </div>
                    <span className="text-text-secondary tabular-nums w-10 text-right">{r.cnt}</span>
                </div>
            ))}
        </div>
    );
}

function Heatmap({ rows }: { rows: { skill: string; role_group: string; cnt: number }[] }) {
    const { skills, roles, matrix, max } = useMemo(() => {
        const skillSet = Array.from(new Set(rows.map((r) => r.skill)));
        const roleSet = Array.from(new Set(rows.map((r) => r.role_group)));
        const m: Record<string, Record<string, number>> = {};
        let mx = 0;
        for (const r of rows) {
            m[r.skill] = m[r.skill] || {};
            m[r.skill][r.role_group] = r.cnt;
            mx = Math.max(mx, r.cnt);
        }
        return { skills: skillSet, roles: roleSet, matrix: m, max: mx };
    }, [rows]);

    if (!rows.length) return <Empty />;

    // Fixed-width label column; remaining width is split evenly among role cols
    // so the whole heatmap fits inside the card without horizontal scrolling.
    const labelColPct = 14;
    const roleColPct = roles.length ? (100 - labelColPct) / roles.length : 0;

    return (
        <div className="w-full">
            <table className="w-full border-collapse text-xs table-fixed">
                <colgroup>
                    <col style={{ width: `${labelColPct}%` }} />
                    {roles.map((r) => <col key={r} style={{ width: `${roleColPct}%` }} />)}
                </colgroup>
                <thead>
                    <tr>
                        <th className="p-2"></th>
                        {roles.map((r) => (
                            <th key={r} className="p-2 text-left font-medium text-text-secondary align-bottom">
                                <span className="block text-[10px] leading-tight break-words">{prettify(r)}</span>
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {skills.map((s) => (
                        <tr key={s}>
                            <td className="p-2 font-medium pr-2 truncate" title={s}>{s}</td>
                            {roles.map((r) => {
                                const v = matrix[s]?.[r] ?? 0;
                                const intensity = max > 0 ? v / max : 0;
                                return (
                                    <td key={r} className="p-1">
                                        <div
                                            className="w-full h-9 rounded flex items-center justify-center text-white font-semibold transition hover:scale-105"
                                            style={{ backgroundColor: `rgba(99, 102, 241, ${0.08 + intensity * 0.85})` }}
                                            title={`${s} × ${r}: ${v}`}
                                        >
                                            {v > 0 ? v : ''}
                                        </div>
                                    </td>
                                );
                            })}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

function SourceBreakdownBar({ rows }: { rows: { source: string; cnt: number }[] }) {
    const total = rows.reduce((s, r) => s + r.cnt, 0) || 1;
    return (
        <Card>
            <CardHeader>
                <CardTitle className="text-lg">Phân bố theo nguồn dữ liệu</CardTitle>
                <CardDescription>Tổng {total.toLocaleString()} JD</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="flex w-full h-10 rounded-xl overflow-hidden">
                    {rows.map((r, i) => (
                        <div
                            key={r.source}
                            className="flex items-center justify-center text-white text-xs font-semibold transition hover:brightness-110"
                            style={{
                                width: `${(r.cnt / total) * 100}%`,
                                backgroundColor: PALETTE[i % PALETTE.length],
                            }}
                            title={`${r.source}: ${r.cnt}`}
                        >
                            {r.source} ({r.cnt})
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}


// ── premium + velocity ─────────────────────────────────────────

function PremiumChart({ data }: { data: MarketIntelDashboard['skill_premium'] }) {
    if (!data.top_premium.length) return <EmptyNote msg="Chưa đủ JD có lương USD để tính premium." />;
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
                <div className="text-xs uppercase tracking-wider text-emerald-400 mb-2 font-semibold flex items-center gap-1.5">
                    <TrendingUp className="w-3.5 h-3.5" /> Top trả lương cao
                </div>
                <PremiumBars rows={data.top_premium} positive />
            </div>
            <div>
                <div className="text-xs uppercase tracking-wider text-rose-400 mb-2 font-semibold flex items-center gap-1.5">
                    <TrendingDown className="w-3.5 h-3.5" /> Lương thấp nhất
                </div>
                <PremiumBars rows={data.lowest_paid} />
            </div>
        </div>
    );
}

function PremiumBars({ rows, positive = false }: { rows: MarketIntelDashboard['skill_premium']['top_premium']; positive?: boolean }) {
    const maxAbs = Math.max(...rows.map((r) => Math.abs(r.premium_pct)), 1);
    return (
        <div className="space-y-2">
            {rows.map((r) => {
                const pct = r.premium_pct;
                const fillPct = (Math.abs(pct) / maxAbs) * 100;
                return (
                    <div key={r.skill} className="text-xs">
                        <div className="flex items-center justify-between mb-0.5">
                            <span className="font-medium truncate" title={r.skill}>{r.skill}</span>
                            <span className={`tabular-nums font-semibold ${pct >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                {pct >= 0 ? '+' : ''}{pct.toFixed(0)}%
                            </span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
                                <div
                                    className="h-full rounded-full"
                                    style={{
                                        width: `${fillPct}%`,
                                        background: positive
                                            ? 'linear-gradient(90deg, #10b981, #06b6d4)'
                                            : 'linear-gradient(90deg, #f43f5e, #f97316)',
                                    }}
                                />
                            </div>
                            <span className="text-text-secondary w-20 text-right tabular-nums">
                                ${Math.round(r.median_salary).toLocaleString()} · {r.cnt} JD
                            </span>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

function VelocityChart({ data }: { data: MarketIntelDashboard['skill_velocity'] }) {
    if (!data.trending_up.length && !data.trending_down.length)
        return <EmptyNote msg="Chưa đủ data 14+14 ngày để so sánh velocity." />;
    const renderRow = (r: MarketIntelDashboard['skill_velocity']['trending_up'][number], up: boolean) => {
        const Icon = up ? TrendingUp : TrendingDown;
        const color = up ? 'text-emerald-400' : 'text-rose-400';
        const bg = up ? 'from-emerald-500/15 to-emerald-500/0' : 'from-rose-500/15 to-rose-500/0';
        return (
            <div key={r.skill} className={`p-2.5 rounded-xl bg-gradient-to-r ${bg} flex items-center gap-2 text-xs`}>
                <Icon className={`w-3.5 h-3.5 ${color} shrink-0`} />
                <span className="font-semibold flex-1 truncate" title={r.skill}>{r.skill}</span>
                <span className={`${color} font-bold tabular-nums`}>
                    {r.delta_abs > 0 ? '+' : ''}{r.delta_abs}
                </span>
                <span className="text-text-secondary tabular-nums w-12 text-right">
                    {r.delta_pct !== null ? `${r.delta_pct > 0 ? '+' : ''}${r.delta_pct.toFixed(0)}%` : '—'}
                </span>
                <span className="text-text-secondary text-[10px] w-20 text-right">
                    {r.prev_cnt} → {r.recent_cnt}
                </span>
            </div>
        );
    };
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
                <div className="text-xs uppercase tracking-wider text-emerald-400 mb-2 font-semibold flex items-center gap-1.5">
                    <TrendingUp className="w-3.5 h-3.5" /> Trending UP
                </div>
                <div className="space-y-1.5">{data.trending_up.map((r) => renderRow(r, true))}</div>
            </div>
            <div>
                <div className="text-xs uppercase tracking-wider text-rose-400 mb-2 font-semibold flex items-center gap-1.5">
                    <TrendingDown className="w-3.5 h-3.5" /> Trending DOWN
                </div>
                <div className="space-y-1.5">{data.trending_down.map((r) => renderRow(r, false))}</div>
            </div>
        </div>
    );
}


// ── clusters ───────────────────────────────────────────────────

function ClusterChart({ clusters }: { clusters: MarketIntelDashboard['skill_clusters'] }) {
    if (!clusters.length) return <EmptyNote msg="Chưa phát hiện cluster nào với threshold hiện tại." />;
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {clusters.map((c, i) => {
                const color = PALETTE[i % PALETTE.length];
                return (
                    <div key={c.label}
                        className="rounded-2xl p-4 border border-white/5 relative overflow-hidden hover:border-white/20 transition"
                        style={{ background: `linear-gradient(135deg, ${color}18, transparent)` }}>
                        <div className="text-[10px] uppercase tracking-wider text-text-secondary mb-1">Stack #{i + 1} · {c.size} skills</div>
                        <div className="font-bold mb-2 text-sm truncate" title={c.label}>{c.label}</div>
                        <div className="flex flex-wrap gap-1">
                            {c.skills.map((s) => (
                                <span key={s} className="px-2 py-0.5 rounded-md text-[10px] font-medium"
                                    style={{ backgroundColor: color + '33', color }}>{s}</span>
                            ))}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}


// ── salary insights ────────────────────────────────────────────

function RoleSalaryChart({ rows }: { rows: MarketIntelDashboard['role_salary'] }) {
    if (!rows.length) return <EmptyNote msg="Cần JD có lương USD + role_group." />;
    const max = Math.max(...rows.map((r) => r.p75 ?? 0));
    return (
        <div className="space-y-2.5">
            {rows.map((r, i) => (
                <div key={r.role_group} className="text-xs">
                    <div className="flex items-center justify-between mb-1">
                        <span className="font-medium truncate" title={prettify(r.role_group)}>{prettify(r.role_group)}</span>
                        <span className="text-text-secondary tabular-nums">${Math.round(r.median_mid ?? 0).toLocaleString()} · {r.cnt} JD</span>
                    </div>
                    <div className="relative h-2 rounded-full bg-white/5">
                        <div
                            className="absolute h-full rounded-full opacity-50"
                            style={{
                                left: `${((r.p25 ?? 0) / max) * 100}%`,
                                width: `${(((r.p75 ?? 0) - (r.p25 ?? 0)) / max) * 100}%`,
                                background: PALETTE[i % PALETTE.length],
                            }}
                        />
                        <div
                            className="absolute h-3 w-0.5 -top-0.5 bg-white"
                            style={{ left: `${((r.median_mid ?? 0) / max) * 100}%` }}
                        />
                    </div>
                </div>
            ))}
            <div className="text-[10px] text-text-secondary mt-2">Thanh = dải P25–P75 · vạch trắng = median</div>
        </div>
    );
}

function EduSalaryChart({ rows }: { rows: MarketIntelDashboard['edu_salary'] }) {
    if (!rows.length) return <EmptyNote msg="Cần JD có bằng cấp + lương USD." />;
    return (
        <ResponsiveContainer width="100%" height={260}>
            <BarChart data={rows} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid stroke="rgba(255,255,255,0.04)" />
                <XAxis type="number" tick={{ fontSize: 11, fill: '#999' }} tickFormatter={(v) => `$${v}`} />
                <YAxis dataKey="degree_norm" type="category" width={100} tick={{ fontSize: 11, fill: '#bbb' }} />
                <Tooltip content={<DarkTooltip />} />
                <Bar dataKey="median_salary" name="Median (USD)" fill="#8b5cf6" radius={[0, 6, 6, 0]} />
            </BarChart>
        </ResponsiveContainer>
    );
}

function GeoSalaryChart({ rows }: { rows: MarketIntelDashboard['geo_salary'] }) {
    if (!rows.length) return <EmptyNote msg="Cần JD có location + lương USD." />;
    const max = Math.max(...rows.map((r) => r.p75 ?? 0));
    return (
        <div className="space-y-3 mt-2">
            {rows.map((r, i) => (
                <div key={r.city} className="text-xs">
                    <div className="flex items-center justify-between mb-1.5">
                        <span className="font-bold text-sm flex items-center gap-1.5">
                            <MapPin className="w-3.5 h-3.5" style={{ color: PALETTE[i % PALETTE.length] }} />
                            {r.city}
                        </span>
                        <span className="text-text-secondary tabular-nums">${Math.round(r.median_salary ?? 0).toLocaleString()} · {r.cnt} JD</span>
                    </div>
                    <div className="relative h-3 rounded-full bg-white/5">
                        <div
                            className="absolute h-full rounded-full opacity-60"
                            style={{
                                left: `${((r.p25 ?? 0) / max) * 100}%`,
                                width: `${(((r.p75 ?? 0) - (r.p25 ?? 0)) / max) * 100}%`,
                                background: `linear-gradient(90deg, ${PALETTE[i % PALETTE.length]}, ${PALETTE[(i + 3) % PALETTE.length]})`,
                            }}
                        />
                        <div
                            className="absolute h-4 w-1 -top-0.5 bg-white rounded"
                            style={{ left: `${((r.median_salary ?? 0) / max) * 100}%` }}
                        />
                    </div>
                    <div className="flex justify-between text-[10px] text-text-secondary mt-0.5">
                        <span>${Math.round(r.p25 ?? 0).toLocaleString()}</span>
                        <span>${Math.round(r.p75 ?? 0).toLocaleString()}</span>
                    </div>
                </div>
            ))}
        </div>
    );
}


// ── remote + skills-by-exp + companies-by-skill ────────────────

function RemoteSkillChart({ rows }: { rows: MarketIntelDashboard['remote_by_skill'] }) {
    if (!rows.length) return <EmptyNote msg="Cần JD có work_mode." />;
    return (
        <div className="space-y-1.5">
            {rows.map((r, i) => (
                <div key={r.skill} className="flex items-center gap-2 text-xs">
                    <span className="w-24 truncate font-medium shrink-0" title={r.skill}>{r.skill}</span>
                    <div className="flex-1 h-2.5 rounded-full bg-white/5 overflow-hidden">
                        <div
                            className="h-full rounded-full"
                            style={{
                                width: `${r.pct}%`,
                                background: `linear-gradient(90deg, ${PALETTE[i % PALETTE.length]}, ${PALETTE[(i + 5) % PALETTE.length]})`,
                            }}
                        />
                    </div>
                    <span className="text-text-secondary tabular-nums w-16 text-right">{r.pct.toFixed(1)}%</span>
                </div>
            ))}
        </div>
    );
}

function SkillsByExpChart({ data }: { data: MarketIntelDashboard['skills_by_exp'] }) {
    const buckets = Object.keys(data).sort();
    if (!buckets.length) return <EmptyNote msg="Chưa đủ JD có min_exp." />;
    return (
        <div className="space-y-3">
            {buckets.map((b, bi) => (
                <div key={b}>
                    <div className="text-xs uppercase tracking-wider font-semibold mb-1.5" style={{ color: PALETTE[bi % PALETTE.length] }}>
                        {b}
                    </div>
                    <div className="flex flex-wrap gap-1">
                        {data[b].map((s) => (
                            <span key={s.skill} className="px-2 py-1 rounded-md text-[11px] font-medium bg-white/[0.04] hover:bg-white/10 transition"
                                title={`${s.cnt} JD`}>
                                {s.skill} <span className="text-text-secondary">·{s.cnt}</span>
                            </span>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
}

function CompaniesBySkillChart({ data }: { data: MarketIntelDashboard['companies_by_skill'] }) {
    const skills = Object.keys(data);
    const [selected, setSelected] = useState<string>(skills[0] ?? '');
    if (!skills.length) return <Empty />;
    const companies = data[selected] || [];
    return (
        <div className="space-y-3">
            <div className="flex flex-wrap gap-1.5">
                {skills.map((s) => (
                    <button
                        key={s}
                        onClick={() => setSelected(s)}
                        className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition ${
                            s === selected
                                ? 'bg-accent-primary text-white shadow-md shadow-accent-primary/30'
                                : 'bg-white/[0.04] hover:bg-white/10'
                        }`}>
                        {s}
                    </button>
                ))}
            </div>
            <div className="space-y-1.5 pt-2 border-t border-white/5">
                <div className="text-[10px] uppercase tracking-wider text-text-secondary">Top tuyển <b className="text-text-primary">{selected}</b></div>
                {companies.map((c, i) => (
                    <div key={c.company} className="flex items-center gap-3 text-xs p-2 rounded-lg bg-white/[0.02]">
                        <span className="w-5 h-5 rounded-full flex items-center justify-center font-bold text-[10px]"
                            style={{ backgroundColor: PALETTE[i % PALETTE.length] + '33', color: PALETTE[i % PALETTE.length] }}>
                            {i + 1}
                        </span>
                        <span className="flex-1 font-medium truncate" title={c.company}>{c.company}</span>
                        <span className="text-text-secondary tabular-nums">{c.cnt} JD</span>
                    </div>
                ))}
            </div>
        </div>
    );
}


// ── English Premium hero ───────────────────────────────────────

function EnglishPremiumHero({ data }: { data: NonNullable<MarketIntelDashboard['english_premium']> }) {
    const positive = data.premium_pct >= 0;
    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-stretch">
            <div className="md:col-span-1 rounded-2xl p-6 bg-gradient-to-br from-emerald-500/20 to-emerald-600/5 border border-emerald-500/20 flex flex-col items-center justify-center">
                <div className="text-text-secondary text-xs uppercase tracking-wider mb-1">Premium</div>
                <div className={`text-6xl font-black ${positive ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {positive ? '+' : ''}{data.premium_pct.toFixed(1)}%
                </div>
                <div className="text-xs text-text-secondary mt-2 text-center">Tăng lương khi yêu cầu English</div>
            </div>
            <div className="rounded-2xl p-6 bg-white/[0.03] border border-white/5 flex flex-col">
                <div className="text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-1">Có yêu cầu English</div>
                <div className="text-3xl font-black">${data.with_english.median_salary.toLocaleString()}</div>
                <div className="text-xs text-text-secondary mt-auto pt-3">{data.with_english.cnt} JD · median USD</div>
            </div>
            <div className="rounded-2xl p-6 bg-white/[0.03] border border-white/5 flex flex-col">
                <div className="text-rose-400 text-xs font-semibold uppercase tracking-wider mb-1">Không yêu cầu</div>
                <div className="text-3xl font-black">${data.without_english.median_salary.toLocaleString()}</div>
                <div className="text-xs text-text-secondary mt-auto pt-3">{data.without_english.cnt} JD · median USD</div>
            </div>
        </div>
    );
}


// ── Quadrant Hidden Gems ───────────────────────────────────────

function QuadrantChart({ quadrants, gems }: {
    quadrants: MarketIntelDashboard['skill_quadrants'];
    gems: MarketIntelDashboard['hidden_gems'];
}) {
    const [hovered, setHovered] = useState<string | null>(null);
    if (!quadrants.length) return <EmptyNote msg="Cần ≥3 JD USD/skill để vẽ quadrant." />;
    const maxCnt = Math.max(...quadrants.map((q) => q.cnt));
    const maxSal = Math.max(...quadrants.map((q) => q.median_salary));
    const overallMed = quadrants[0] ? quadrants.reduce((s, q) => s + q.median_salary, 0) / quadrants.length : 0;
    const medCutX = 30 / maxCnt * 100;
    const medCutY = overallMed / maxSal * 100;

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2 relative h-[360px] rounded-2xl bg-white/[0.02] border border-white/5">
                <div className="absolute inset-0 p-4">
                    <div className="absolute" style={{ left: `${medCutX}%`, top: 0, bottom: 0, width: 1, background: 'rgba(255,255,255,0.1)' }} />
                    <div className="absolute" style={{ top: `${100 - medCutY}%`, left: 0, right: 0, height: 1, background: 'rgba(255,255,255,0.1)' }} />
                    <div className="absolute top-2 left-2 text-[10px] text-emerald-400/60 uppercase tracking-wider font-bold">💎 Hidden Gem</div>
                    <div className="absolute top-2 right-2 text-[10px] text-cyan-400/60 uppercase tracking-wider font-bold">High demand · High salary</div>
                    <div className="absolute bottom-2 left-2 text-[10px] text-text-secondary uppercase tracking-wider">Low everything</div>
                    <div className="absolute bottom-2 right-2 text-[10px] text-orange-400/60 uppercase tracking-wider">Saturated</div>
                    {quadrants.map((q) => {
                        const x = (q.cnt / maxCnt) * 100;
                        const y = (q.median_salary / maxSal) * 100;
                        const r = Math.max(4, Math.min(14, Math.log2(q.cnt + 1) * 2.5));
                        const color = q.is_gem ? '#10b981' : '#6366f1';
                        return (
                            <div key={q.skill}
                                className="absolute rounded-full transition cursor-pointer hover:scale-150 hover:z-10"
                                style={{
                                    left: `${x}%`, bottom: `${y}%`,
                                    width: r * 2, height: r * 2,
                                    transform: 'translate(-50%, 50%)',
                                    backgroundColor: color,
                                    opacity: hovered && hovered !== q.skill ? 0.2 : 0.8,
                                    boxShadow: hovered === q.skill ? `0 0 16px ${color}` : 'none',
                                }}
                                onMouseEnter={() => setHovered(q.skill)}
                                onMouseLeave={() => setHovered(null)}
                                title={`${q.skill}: ${q.cnt} JD · $${Math.round(q.median_salary)}`}
                            />
                        );
                    })}
                </div>
                <div className="absolute bottom-1 right-2 text-[10px] text-text-secondary">→ Số JD</div>
                <div className="absolute top-2 left-2 text-[10px] text-text-secondary rotate-[-90deg] origin-left translate-y-16">↑ Lương USD</div>
            </div>
            <div className="space-y-1.5">
                <div className="text-xs uppercase tracking-wider text-emerald-400 mb-2 font-semibold flex items-center gap-1.5">
                    <Gem className="w-3.5 h-3.5" /> Top 10 Hidden Gems
                </div>
                {gems.length === 0 && <EmptyNote msg="Chưa phát hiện gem." />}
                {gems.map((g, i) => (
                    <div key={g.skill}
                        className={`flex items-center gap-2 text-xs p-2 rounded-lg cursor-pointer transition ${
                            hovered === g.skill ? 'bg-emerald-500/20' : 'bg-white/[0.03] hover:bg-white/[0.06]'
                        }`}
                        onMouseEnter={() => setHovered(g.skill)}
                        onMouseLeave={() => setHovered(null)}
                    >
                        <span className="w-5 text-text-secondary text-[10px] tabular-nums">#{i + 1}</span>
                        <span className="flex-1 font-medium truncate" title={g.skill}>{g.skill}</span>
                        <span className="text-emerald-400 font-bold tabular-nums">${Math.round(g.median_salary).toLocaleString()}</span>
                        <span className="text-text-secondary tabular-nums w-12 text-right">{g.cnt} JD</span>
                    </div>
                ))}
            </div>
        </div>
    );
}


// ── Salary Curve ───────────────────────────────────────────────

function SalaryCurveChart({ curve }: { curve: MarketIntelDashboard['salary_curve'] }) {
    if (!curve.length) return <EmptyNote msg="Cần JD có min_exp + lương USD." />;
    const roleKeys = curve.length > 0
        ? Object.keys(curve[0]).filter((k) => k !== 'exp' && k !== 'overall_median')
        : [];
    return (
        <ResponsiveContainer width="100%" height={320}>
            <LineChart data={curve}>
                <CartesianGrid stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="exp" tick={{ fontSize: 11, fill: '#999' }} />
                <YAxis tick={{ fontSize: 11, fill: '#999' }} tickFormatter={(v) => `$${v}`} />
                <Tooltip content={<DarkTooltip />} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Line type="monotone" dataKey="overall_median" name="Overall median" stroke="#fff" strokeWidth={3} dot={{ r: 5 }} />
                {roleKeys.map((k, i) => (
                    <Line key={k} type="monotone" dataKey={k} name={prettify(k).slice(0, 24)}
                        stroke={PALETTE[i % PALETTE.length]} strokeWidth={2} strokeDasharray="4 4" dot={{ r: 3 }} connectNulls />
                ))}
            </LineChart>
        </ResponsiveContainer>
    );
}


// ── Specificity tiers ──────────────────────────────────────────

function SpecificityChart({ rows }: { rows: MarketIntelDashboard['skill_specificity'] }) {
    if (!rows.length) return <Empty />;
    const tierMeta: Record<string, { label: string; color: string }> = {
        core: { label: 'Core (>30% JD)', color: '#ef4444' },
        common: { label: 'Common (10-30%)', color: '#f97316' },
        specialized: { label: 'Specialized (<10%)', color: '#10b981' },
    };
    const grouped: Record<string, typeof rows> = { core: [], common: [], specialized: [] };
    rows.forEach((r) => grouped[r.tier]?.push(r));
    return (
        <div className="space-y-3">
            {(['core', 'common', 'specialized'] as const).map((tier) => (
                grouped[tier].length > 0 && (
                    <div key={tier}>
                        <div className="text-[10px] uppercase tracking-wider font-bold mb-1.5" style={{ color: tierMeta[tier].color }}>
                            {tierMeta[tier].label}
                        </div>
                        <div className="flex flex-wrap gap-1">
                            {grouped[tier].map((s) => (
                                <span key={s.skill} className="px-2 py-1 rounded-md text-[11px] font-medium"
                                    style={{ backgroundColor: tierMeta[tier].color + '22', color: tierMeta[tier].color }}
                                    title={`${s.cnt} JD · ${s.pct}%`}>
                                    {s.skill} <span className="opacity-60">·{s.pct}%</span>
                                </span>
                            ))}
                        </div>
                    </div>
                )
            ))}
        </div>
    );
}


// ── Hot companies / niche / outdated ───────────────────────────

function HotCompaniesChart({ rows }: { rows: MarketIntelDashboard['hot_companies'] }) {
    if (!rows.length) return <EmptyNote msg="Chưa đủ velocity data cho công ty." />;
    return (
        <div className="space-y-1.5">
            {rows.map((r) => {
                const up = r.delta_abs > 0;
                const color = up ? 'text-emerald-400' : 'text-rose-400';
                const bg = up ? 'from-emerald-500/15 to-emerald-500/0' : 'from-rose-500/15 to-rose-500/0';
                const Icon = up ? TrendingUp : TrendingDown;
                return (
                    <div key={r.company} className={`p-2.5 rounded-lg bg-gradient-to-r ${bg} flex items-center gap-2 text-xs`}>
                        <Icon className={`w-3.5 h-3.5 ${color} shrink-0`} />
                        <span className="font-semibold flex-1 truncate" title={r.company}>{r.company}</span>
                        <span className={`${color} font-bold tabular-nums`}>{up ? '+' : ''}{r.delta_abs}</span>
                        <span className="text-text-secondary text-[10px] tabular-nums w-16 text-right">{r.prev_cnt}→{r.recent_cnt}</span>
                    </div>
                );
            })}
        </div>
    );
}

function NicheChampionsChart({ rows }: { rows: MarketIntelDashboard['niche_champions'] }) {
    if (!rows.length) return <Empty />;
    const max = Math.max(...rows.map((r) => r.niche_skill_jds));
    return (
        <div className="space-y-2">
            {rows.map((r, i) => (
                <div key={r.company} className="flex items-center gap-2 text-xs">
                    <Crown className="w-3 h-3 shrink-0" style={{ color: PALETTE[i % PALETTE.length] }} />
                    <span className="flex-1 truncate font-medium" title={r.company}>{r.company}</span>
                    <div className="w-24 h-2 rounded-full bg-white/5 overflow-hidden">
                        <div className="h-full rounded-full"
                            style={{
                                width: `${(r.niche_skill_jds / max) * 100}%`,
                                background: `linear-gradient(90deg, ${PALETTE[i % PALETTE.length]}, ${PALETTE[(i + 4) % PALETTE.length]})`,
                            }}
                        />
                    </div>
                    <span className="text-text-secondary tabular-nums w-8 text-right">{r.niche_skill_jds}</span>
                </div>
            ))}
        </div>
    );
}

function OutdatedSkillsChart({ rows }: { rows: MarketIntelDashboard['outdated_skills'] }) {
    if (!rows.length) return <EmptyNote msg="🎉 Không có skill nào đang nguội. Thị trường ổn định." />;
    return (
        <div className="space-y-2">
            {rows.map((r) => {
                const oldSum = r.w3 + r.w4;
                const newSum = r.w1 + r.w2;
                return (
                    <div key={r.skill} className="text-xs p-2 rounded-lg bg-rose-500/5 border border-rose-500/15">
                        <div className="flex items-center justify-between mb-1">
                            <span className="font-bold">{r.skill}</span>
                            <span className="text-rose-400 font-bold">{oldSum} → {newSum}</span>
                        </div>
                        <div className="flex items-center gap-1">
                            {[r.w4, r.w3, r.w2, r.w1].map((v, i) => (
                                <div key={i} className="flex-1 text-center">
                                    <div className="h-6 rounded flex items-end justify-center"
                                        style={{ backgroundColor: 'rgba(244, 63, 94, 0.15)' }}>
                                        <div className="w-full rounded"
                                            style={{
                                                height: `${(v / Math.max(r.w1, r.w2, r.w3, r.w4, 1)) * 100}%`,
                                                backgroundColor: i >= 2 ? '#f43f5e' : '#fb7185',
                                            }} />
                                    </div>
                                    <div className="text-[9px] text-text-secondary mt-0.5">w-{4 - i}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}


// ── Combo Salary ───────────────────────────────────────────────

function ComboSalaryChart({ rows }: { rows: MarketIntelDashboard['combo_salary'] }) {
    if (!rows.length) return <EmptyNote msg="Chưa đủ JD chứa combo skill có lương USD." />;
    return (
        <div className="space-y-2.5">
            {rows.map((r, i) => {
                const positive = r.combo_premium_pct >= 0;
                return (
                    <div key={`${r.skill_a}-${r.skill_b}`} className="p-2.5 rounded-xl bg-white/[0.02] border border-white/5">
                        <div className="flex items-center gap-2 mb-1.5">
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold"
                                style={{ backgroundColor: PALETTE[i % PALETTE.length] + '33', color: PALETTE[i % PALETTE.length] }}>
                                {r.skill_a}
                            </span>
                            <span className="text-text-secondary text-xs">+</span>
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold"
                                style={{ backgroundColor: PALETTE[(i + 4) % PALETTE.length] + '33', color: PALETTE[(i + 4) % PALETTE.length] }}>
                                {r.skill_b}
                            </span>
                            <span className={`ml-auto text-xs font-bold ${positive ? 'text-emerald-400' : 'text-rose-400'}`}>
                                {positive ? '+' : ''}{r.combo_premium_pct.toFixed(0)}%
                            </span>
                        </div>
                        <div className="text-[10px] text-text-secondary flex justify-between">
                            <span>Combo: <b className="text-text-primary">${Math.round(r.both_median)}</b> ({r.both_cnt} JD)</span>
                            <span>Solo avg: ${Math.round(((r.a_median ?? 0) + (r.b_median ?? 0)) / 2)}</span>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}


// ── Day-of-Week ────────────────────────────────────────────────

function DayOfWeekChart({ rows }: { rows: MarketIntelDashboard['day_of_week'] }) {
    if (!rows.length) return <Empty />;
    // Reorder Mon-first
    const ordered = [...rows].sort((a, b) => ((a.dow + 6) % 7) - ((b.dow + 6) % 7));
    return (
        <ResponsiveContainer width="100%" height={240}>
            <BarChart data={ordered}>
                <CartesianGrid stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="day" tick={{ fontSize: 11, fill: '#999' }} />
                <YAxis tick={{ fontSize: 11, fill: '#999' }} />
                <Tooltip content={<DarkTooltip />} />
                <Bar dataKey="cnt" radius={[8, 8, 0, 0]}>
                    {ordered.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
                </Bar>
            </BarChart>
        </ResponsiveContainer>
    );
}


// ── Skill Network (force-style radial layout) ──────────────────

function SkillNetworkChart({ network }: { network: MarketIntelDashboard['skill_network'] }) {
    const { nodes, edges } = network;
    const [hovered, setHovered] = useState<string | null>(null);
    if (!nodes.length) return <EmptyNote msg="Không đủ data để build graph." />;

    // Simple radial layout — nodes around a circle, sized by cnt.
    const cx = 400, cy = 280, R = 220;
    const placed = nodes.map((n, i) => {
        const angle = (i / nodes.length) * Math.PI * 2 - Math.PI / 2;
        return {
            skill: n.skill, cnt: n.cnt,
            x: cx + Math.cos(angle) * R,
            y: cy + Math.sin(angle) * R,
        };
    });
    const posMap = new Map(placed.map((p) => [p.skill, p]));
    const maxCnt = Math.max(...nodes.map((n) => n.cnt));
    const maxEdge = Math.max(...edges.map((e) => e.cnt), 1);

    return (
        <div className="relative w-full overflow-x-auto">
            <svg viewBox="0 0 800 560" className="w-full" style={{ minWidth: 600 }}>
                {edges.map((e, i) => {
                    const a = posMap.get(e.skill_a); const b = posMap.get(e.skill_b);
                    if (!a || !b) return null;
                    const opacity = (e.cnt / maxEdge) * 0.45 + 0.05;
                    const active = hovered === e.skill_a || hovered === e.skill_b;
                    return (
                        <line key={i} x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                            stroke={active ? '#6366f1' : '#888'}
                            strokeWidth={active ? 2 : Math.max(0.4, (e.cnt / maxEdge) * 2.5)}
                            opacity={hovered && !active ? 0.05 : opacity} />
                    );
                })}
                {placed.map((p, i) => {
                    const r = Math.max(8, Math.min(28, Math.log2(p.cnt + 1) * 4));
                    const active = hovered === p.skill;
                    const color = PALETTE[i % PALETTE.length];
                    return (
                        <g key={p.skill}
                            style={{ cursor: 'pointer' }}
                            onMouseEnter={() => setHovered(p.skill)}
                            onMouseLeave={() => setHovered(null)}
                        >
                            <circle cx={p.x} cy={p.y} r={r}
                                fill={color}
                                opacity={hovered && !active ? 0.2 : 0.85}
                                style={{ filter: active ? `drop-shadow(0 0 12px ${color})` : 'none' }} />
                            <text x={p.x} y={p.y + r + 12}
                                textAnchor="middle"
                                fill={active ? '#fff' : '#bbb'}
                                fontSize={active ? 13 : 10}
                                fontWeight={active ? 700 : 500}
                                opacity={hovered && !active ? 0.3 : 1}>
                                {p.skill}
                            </text>
                        </g>
                    );
                })}
            </svg>
        </div>
    );
}


// ── shared dark tooltip ────────────────────────────────────────

function DarkTooltip({ active, payload, label }: any) {
    if (!active || !payload || !payload.length) return null;
    return (
        <div className="rounded-xl bg-black/90 border border-white/10 px-3 py-2 shadow-lg">
            {label && <div className="text-text-secondary text-xs mb-1">{label}</div>}
            {payload.map((p: any, i: number) => (
                <div key={i} className="text-xs flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: p.color || p.fill }} />
                    <span className="text-text-primary font-medium">{p.name}:</span>
                    <span className="text-white tabular-nums">{Number(p.value).toLocaleString()}</span>
                </div>
            ))}
        </div>
    );
}


// ── skeleton ───────────────────────────────────────────────────

function SkeletonDashboard() {
    return (
        <div className="max-w-7xl mx-auto p-6 space-y-6">
            <div className="h-12 w-72 rounded-2xl bg-surface/40 animate-pulse" />
            <div className="h-14 rounded-2xl bg-surface/30 animate-pulse" />
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="h-32 rounded-3xl bg-surface/40 animate-pulse" />
                ))}
            </div>
            <div className="h-72 rounded-3xl bg-surface/40 animate-pulse" />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {Array.from({ length: 6 }).map((_, i) => (
                    <div key={i} className="h-80 rounded-3xl bg-surface/40 animate-pulse" />
                ))}
            </div>
        </div>
    );
}


// ── helpers ────────────────────────────────────────────────────

function Empty() { return <div className="text-text-secondary text-sm py-8 text-center">Không có dữ liệu</div>; }
function EmptyNote({ msg }: { msg: string }) { return <div className="text-text-secondary text-sm py-6 text-center">{msg}</div>; }

function prettify(slug: string): string {
    if (!slug) return slug;
    return slug.replace(/_/g, ' ').replace(/\band\b/gi, '&').replace(/\b\w/g, (c) => c.toUpperCase());
}
