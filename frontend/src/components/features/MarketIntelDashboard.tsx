import { useEffect, useMemo, useState } from 'react';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, Legend,
} from 'recharts';
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


export default function MarketIntelDashboard() {
    const [data, setData] = useState<MarketIntelDashboard | null>(null);
    const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;
        setLoading(true);
        setError(null);
        skillApi
            .getMarketIntelDashboard({
                source: filters.source || undefined,
                role_group: filters.role_group || undefined,
                seniority: filters.seniority || undefined,
            })
            .then((res) => { if (!cancelled) setData(res.data); })
            .catch((e) => { if (!cancelled) setError(e?.message ?? 'Lỗi tải dữ liệu'); })
            .finally(() => { if (!cancelled) setLoading(false); });
        return () => { cancelled = true; };
    }, [filters]);

    if (loading && !data) return <div className="p-8 text-center text-text-secondary">Đang tải dữ liệu thị trường…</div>;
    if (error) return <div className="p-8 text-center text-red-500">{error}</div>;
    if (!data) return null;

    return (
        <div className="space-y-6 max-w-7xl mx-auto p-6">
            <header>
                <h1 className="text-3xl font-black font-outfit">Market Intelligence — Thị trường tuyển dụng IT</h1>
                <p className="text-text-secondary mt-1">
                    Dữ liệu tổng hợp từ {data.kpis.total_jds.toLocaleString()} JD ·
                    {' '}{data.kpis.total_companies.toLocaleString()} công ty ·
                    {' '}{data.kpis.unique_skills.toLocaleString()} kỹ năng độc lập
                    {data.kpis.earliest_post && data.kpis.latest_post && (
                        <> · giai đoạn {data.kpis.earliest_post} → {data.kpis.latest_post}</>
                    )}
                </p>
            </header>

            <FiltersBar
                filters={filters}
                options={data.options}
                onChange={setFilters}
                onReset={() => setFilters(EMPTY_FILTERS)}
            />

            <KpiCards data={data} />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <ChartCard title="Top 20 kỹ năng được tuyển nhiều nhất" subtitle="Theo số JD đề cập">
                    <TopSkillsChart rows={data.top_skills} />
                </ChartCard>

                <ChartCard title="Phân bố nhóm vai trò" subtitle="Web/Data/Mobile/DevOps/...">
                    <RoleDistributionChart rows={data.role_distribution} />
                </ChartCard>

                <ChartCard title="Phân bố cấp độ kinh nghiệm" subtitle="Junior / Mid / Senior / Lead">
                    <SeniorityChart rows={data.seniority_distribution} />
                </ChartCard>

                <ChartCard title="Hình thức làm việc" subtitle="Onsite / Hybrid / Remote">
                    <WorkModeChart rows={data.work_mode_distribution} />
                </ChartCard>

                <ChartCard
                    title="Mức lương theo cấp độ"
                    subtitle="Median min/max — đơn vị giữ nguyên theo nguồn (USD/VND)"
                >
                    <SalaryChart rows={data.salary_by_seniority} />
                </ChartCard>

                <ChartCard title="Top 10 địa điểm tuyển dụng" subtitle="Theo số JD">
                    <LocationChart rows={data.top_locations} />
                </ChartCard>
            </div>

            <ChartCard
                title="Heatmap kỹ năng × nhóm vai trò"
                subtitle="Top 10 skill × Top 6 role · ô đậm = nhu cầu cao"
            >
                <Heatmap rows={data.heatmap} />
            </ChartCard>

            <SourceBreakdownBar rows={data.source_breakdown} />
        </div>
    );
}


// ── filters bar ─────────────────────────────────────────────────

function FiltersBar({
    filters, options, onChange, onReset,
}: {
    filters: Filters;
    options: MarketIntelDashboard['options'];
    onChange: (f: Filters) => void;
    onReset: () => void;
}) {
    const inputCls = "rounded-xl border border-border bg-surface/50 px-3 py-2 text-sm";
    return (
        <div className="flex flex-wrap items-end gap-3 p-4 rounded-2xl bg-surface/30 backdrop-blur">
            <div>
                <label className="block text-xs text-text-secondary mb-1">Nguồn</label>
                <select className={inputCls} value={filters.source}
                    onChange={(e) => onChange({ ...filters, source: e.target.value })}>
                    <option value="all">Tất cả</option>
                    {options.sources.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
            </div>
            <div>
                <label className="block text-xs text-text-secondary mb-1">Nhóm vai trò</label>
                <select className={inputCls} value={filters.role_group}
                    onChange={(e) => onChange({ ...filters, role_group: e.target.value })}>
                    <option value="">Tất cả</option>
                    {options.role_groups.map((r) => <option key={r} value={r}>{r}</option>)}
                </select>
            </div>
            <div>
                <label className="block text-xs text-text-secondary mb-1">Cấp độ</label>
                <select className={inputCls} value={filters.seniority}
                    onChange={(e) => onChange({ ...filters, seniority: e.target.value })}>
                    <option value="">Tất cả</option>
                    {options.seniorities.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
            </div>
            <button
                onClick={onReset}
                className="ml-auto rounded-xl px-4 py-2 text-sm bg-surface-hover/50 hover:bg-surface-hover">
                Reset filter
            </button>
        </div>
    );
}


// ── KPI cards ───────────────────────────────────────────────────

function KpiCards({ data }: { data: MarketIntelDashboard }) {
    const items = [
        { label: 'Tổng JD', value: data.kpis.total_jds.toLocaleString() },
        { label: 'Công ty', value: data.kpis.total_companies.toLocaleString() },
        { label: 'Kỹ năng độc lập', value: data.kpis.unique_skills.toLocaleString() },
        { label: 'Nguồn dữ liệu', value: String(data.kpis.total_sources) },
    ];
    return (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {items.map((it) => (
                <Card key={it.label}>
                    <CardContent className="pt-6">
                        <div className="text-text-secondary text-sm">{it.label}</div>
                        <div className="text-3xl font-black mt-1">{it.value}</div>
                    </CardContent>
                </Card>
            ))}
        </div>
    );
}


// ── shared chart card wrapper ───────────────────────────────────

function ChartCard({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
    return (
        <Card>
            <CardHeader>
                <CardTitle className="text-xl">{title}</CardTitle>
                {subtitle && <CardDescription>{subtitle}</CardDescription>}
            </CardHeader>
            <CardContent>{children}</CardContent>
        </Card>
    );
}


// ── individual charts ──────────────────────────────────────────

function TopSkillsChart({ rows }: { rows: { skill: string; cnt: number }[] }) {
    if (!rows.length) return <Empty />;
    return (
        <ResponsiveContainer width="100%" height={Math.max(300, rows.length * 22)}>
            <BarChart data={rows} layout="vertical" margin={{ left: 80 }}>
                <XAxis type="number" />
                <YAxis dataKey="skill" type="category" width={120} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="cnt" fill="#6366f1" radius={[0, 6, 6, 0]} />
            </BarChart>
        </ResponsiveContainer>
    );
}

function RoleDistributionChart({ rows }: { rows: { role_group: string; cnt: number }[] }) {
    if (!rows.length) return <Empty />;
    const data = rows.map((r) => ({ name: prettify(r.role_group), value: r.cnt }));
    return (
        <ResponsiveContainer width="100%" height={340}>
            <PieChart>
                <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={120} label={(e) => e.name}>
                    {data.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
                </Pie>
                <Tooltip />
            </PieChart>
        </ResponsiveContainer>
    );
}

function SeniorityChart({ rows }: { rows: { seniority: string; cnt: number }[] }) {
    if (!rows.length) return <EmptyNote msg="Cấp độ chưa được trích xuất cho nguồn này." />;
    return (
        <ResponsiveContainer width="100%" height={300}>
            <BarChart data={rows}>
                <XAxis dataKey="seniority" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="cnt" fill="#10b981" radius={[6, 6, 0, 0]} />
            </BarChart>
        </ResponsiveContainer>
    );
}

function WorkModeChart({ rows }: { rows: { work_mode: string; cnt: number }[] }) {
    if (!rows.length) return <EmptyNote msg="Hình thức làm việc chưa được trích xuất cho nguồn này." />;
    const data = rows.map((r) => ({ name: r.work_mode, value: r.cnt }));
    return (
        <ResponsiveContainer width="100%" height={300}>
            <PieChart>
                <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={60} outerRadius={100} label>
                    {data.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
                </Pie>
                <Tooltip />
                <Legend />
            </PieChart>
        </ResponsiveContainer>
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
        <ResponsiveContainer width="100%" height={320}>
            <BarChart data={data}>
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis />
                <Tooltip formatter={(v) => Number(v).toLocaleString()} />
                <Legend />
                <Bar dataKey="median_min" name="Median min" fill="#06b6d4" radius={[6, 6, 0, 0]} />
                <Bar dataKey="median_max" name="Median max" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
            </BarChart>
        </ResponsiveContainer>
    );
}

function LocationChart({ rows }: { rows: { location: string; cnt: number }[] }) {
    if (!rows.length) return <Empty />;
    return (
        <ResponsiveContainer width="100%" height={Math.max(280, rows.length * 30)}>
            <BarChart data={rows} layout="vertical" margin={{ left: 80 }}>
                <XAxis type="number" />
                <YAxis dataKey="location" type="category" width={130} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="cnt" fill="#f97316" radius={[0, 6, 6, 0]} />
            </BarChart>
        </ResponsiveContainer>
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

    return (
        <div className="overflow-x-auto">
            <table className="border-collapse text-xs">
                <thead>
                    <tr>
                        <th className="p-2"></th>
                        {roles.map((r) => (
                            <th key={r} className="p-2 text-left whitespace-nowrap font-medium text-text-secondary">
                                {prettify(r)}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {skills.map((s) => (
                        <tr key={s}>
                            <td className="p-2 font-medium pr-4 whitespace-nowrap">{s}</td>
                            {roles.map((r) => {
                                const v = matrix[s]?.[r] ?? 0;
                                const intensity = max > 0 ? v / max : 0;
                                return (
                                    <td key={r} className="p-1">
                                        <div
                                            className="w-16 h-9 rounded flex items-center justify-center text-white font-semibold"
                                            style={{ backgroundColor: `rgba(99, 102, 241, ${0.1 + intensity * 0.9})` }}
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
                <CardTitle className="text-xl">Phân bố theo nguồn dữ liệu</CardTitle>
                <CardDescription>Tổng {total.toLocaleString()} JD</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="flex w-full h-10 rounded-xl overflow-hidden">
                    {rows.map((r, i) => (
                        <div
                            key={r.source}
                            className="flex items-center justify-center text-white text-xs font-semibold"
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


// ── small helpers ────────────────────────────────────────────────

function Empty() { return <div className="text-text-secondary text-sm py-8 text-center">Không có dữ liệu</div>; }
function EmptyNote({ msg }: { msg: string }) { return <div className="text-text-secondary text-sm py-6 text-center">{msg}</div>; }

function prettify(slug: string): string {
    return slug.replace(/_/g, ' ').replace(/\band\b/gi, '&').replace(/\b\w/g, (c) => c.toUpperCase());
}
