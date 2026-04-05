import React, { useState, useEffect } from 'react';
import { 
  BarChart3, PieChart as PieChartIcon, 
  TrendingUp, DollarSign, MapPin, 
  Briefcase, Search, Filter, RefreshCw
} from 'lucide-react';
import { skillApi, MarketOverviewResponse } from '../../services/api';
import { 
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, 
  CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell,
  LineChart, Line, AreaChart, Area
} from 'recharts';

type MarketData = MarketOverviewResponse;

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

const MarketDashboard: React.FC = () => {
  const [data, setData] = useState<MarketData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterIndustry, setFilterIndustry] = useState<string>('All');

  useEffect(() => {
    fetchMarketData();
  }, [filterIndustry]);

  const fetchMarketData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const industry = filterIndustry === 'All' ? undefined : filterIndustry;
      const resp = await skillApi.getMarketOverview(industry);
      setData(resp.data);
    } catch (err) {
      console.error("Failed to fetch market data", err);
      setError('Không thể tải dữ liệu thị trường. Kiểm tra skill-service hoặc API Gateway.');
      setData(null);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading || !data) {
    if (error) {
      return (
        <div className="flex flex-col items-center justify-center p-24 space-y-4">
          <p className="text-red-400 font-semibold text-center">{error}</p>
          <button
            onClick={fetchMarketData}
            className="px-4 py-2 rounded-xl bg-surface-hover text-text-primary border border-white/10 hover:bg-surface transition-colors"
          >
            Thử lại
          </button>
        </div>
      );
    }
    return (
      <div className="flex flex-col items-center justify-center p-24 space-y-6">
        <RefreshCw className="w-12 h-12 text-indigo-500 animate-spin" />
        <p className="text-slate-400 font-medium animate-pulse">Aggregating market intelligence...</p>
      </div>
    );
  }

  const industryData = Object.entries(data.industry_distribution).map(([name, value]) => ({ name, value }));
  const locationData = Object.entries(data.location_distribution).map(([name, value]) => ({ name, value }));

  return (
    <div className="p-8 space-y-10 bg-slate-950 min-h-screen text-slate-200">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-1">
          <h1 className="text-4xl font-black tracking-tighter text-white bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-500">
            Market Insights
          </h1>
          <p className="text-slate-400 font-medium italic">
            Visualizing trends across {Object.values(data.industry_distribution).reduce((a, b) => a + b, 0)} job descriptions.
          </p>
        </div>

        <div className="flex items-center gap-3 bg-white/5 p-1.5 rounded-2xl border border-white/5">
          <Filter className="w-4 h-4 text-slate-500 ml-2" />
          {['All', 'Frontend Development', 'Backend Development', 'Machine Learning & AI'].map((ind) => (
            <button
              key={ind}
              onClick={() => setFilterIndustry(ind)}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                filterIndustry === ind 
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20' 
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              {ind === 'All' ? 'All Roles' : ind.split(' ')[0]}
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Top Skills Chart */}
        <div className="lg:col-span-2 p-8 rounded-3xl bg-slate-900/40 border border-white/5 backdrop-blur-xl">
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-sm font-black text-slate-500 uppercase tracking-widest flex items-center gap-2">
              <BarChart3 className="w-4 h-4" /> Most Demanded Skills
            </h3>
            <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/10">
              REAL-TIME DATA
            </span>
          </div>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.top_skills}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip 
                  cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                  contentStyle={{ backgroundColor: '#0f172a', border: 'none', borderRadius: '16px', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.5)' }}
                />
                <Bar dataKey="count" fill="#6366f1" radius={[6, 6, 0, 0]} barSize={24} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Industry Distribution */}
        <div className="p-8 rounded-3xl bg-slate-900/40 border border-white/5 backdrop-blur-xl">
          <h3 className="text-sm font-black text-slate-500 uppercase tracking-widest flex items-center gap-2 mb-8">
            <PieChartIcon className="w-4 h-4" /> Market Segments
          </h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={industryData}
                  cx="50%" cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {industryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} stroke="none" />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 space-y-2">
            {industryData.slice(0, 4).map((item, idx) => (
              <div key={idx} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[idx % COLORS.length] }} />
                  <span className="text-slate-400 font-medium truncate max-w-[120px]">{item.name}</span>
                </div>
                <span className="text-slate-200 font-bold">{item.value} JDs</span>
              </div>
            ))}
          </div>
        </div>

        {/* Salary Overview */}
        <div className="lg:col-span-3 grid grid-cols-1 md:grid-cols-4 gap-6">
          {data.salary_overview.slice(0, 4).map((sal, idx) => (
            <div key={idx} className="p-6 rounded-3xl bg-white/5 border border-white/5 hover:border-white/10 transition-all duration-300 group">
              <div className="flex items-center justify-between mb-4">
                <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 group-hover:bg-indigo-500 group-hover:text-white transition-all">
                  <DollarSign className="w-5 h-5" />
                </div>
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{sal.category.split(' ')[0]}</span>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-bold text-slate-500 uppercase">Median Salary</p>
                <h4 className="text-2xl font-black text-white">${sal.median_salary.toLocaleString()}</h4>
              </div>
              <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between text-[11px] font-bold text-slate-500">
                <span>MIN: ${sal.min_salary.toLocaleString()}</span>
                <span>MAX: ${sal.max_salary.toLocaleString()}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Skill Correlations (Matrix style) */}
        <div className="lg:col-span-3 p-8 rounded-3xl bg-slate-900/40 border border-white/5">
          <h3 className="text-sm font-black text-slate-500 uppercase tracking-widest flex items-center gap-2 mb-8">
            <TrendingUp className="w-4 h-4" /> Skill Synergy Correlations
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {data.correlations.slice(0, 8).map((corr, idx) => (
              <div key={idx} className="flex items-center gap-4 bg-white/5 p-4 rounded-2xl border border-white/5 group hover:bg-indigo-500/5 transition-all">
                <div className="flex flex-col items-center justify-center p-2 rounded-lg bg-slate-950 border border-white/5 text-[10px] font-bold text-slate-400 group-hover:text-indigo-400 transition-all">
                  <span>S-1</span>
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-white">{corr.skill_a}</span>
                    <span className="text-[10px] font-bold text-indigo-400">+{Math.round(corr.weight * 10)}%</span>
                  </div>
                  <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-indigo-500 rounded-full transition-all duration-1000" style={{ width: `${corr.weight * 10}%` }} />
                  </div>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-xs font-bold text-white">{corr.skill_b}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};

export default MarketDashboard;
