import * as React from 'react';
import { 
  Shield, 
  Activity, 
  Files, 
  MessageSquare, 
  Users, 
  Search, 
  Plus, 
  RefreshCw, 
  Trash2, 
  Eye, 
  FileEdit,
  ArrowUpRight,
  ChevronRight,
  Layout
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { cn } from '../../lib/utils';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { monitoringApi, templateApi, feedbackApi, adminApi } from '../../services/api';

type AdminTab = 'stats' | 'templates' | 'feedback' | 'users';

export default function AdminPortal({ userName }: { userName: string }) {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = React.useState<AdminTab>('stats');
  const [stats, setStats] = React.useState<any>(null);
  const [templates, setTemplates] = React.useState<any[]>([]);
  const [feedback, setFeedback] = React.useState<any[]>([]);
  const [users, setUsers] = React.useState<any[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      if (activeTab === 'stats') {
        const res = await monitoringApi.getStats();
        setStats(res.data);
      } else if (activeTab === 'templates') {
        const res = await templateApi.getAll(true);
        setTemplates(res.data);
      } else if (activeTab === 'feedback') {
        const res = await feedbackApi.getAll();
        setFeedback(res.data);
      } else if (activeTab === 'users') {
        const res = await adminApi.getUsers();
        setUsers(res.data);
      }
    } catch (error) {
      console.error('Failed to load admin data', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-canvas animate-in fade-in duration-500">
      {/* Header */}
      <div className="px-8 py-6 border-b border-white/5 flex items-center justify-between bg-canvas/40 backdrop-blur-md sticky top-0 z-10">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20 shadow-lg shadow-emerald-500/5">
            <Shield className="w-6 h-6 text-emerald-500" />
          </div>
          <div>
            <h1 className="text-2xl font-black font-outfit tracking-tight text-text-primary uppercase italic">{t('sidebar.admin')}</h1>
            <p className="text-xs font-bold text-text-secondary uppercase tracking-[0.2em] opacity-60">{t('admin.dashboard')}</p>
          </div>
        </div>
        
        <div className="flex bg-surface/50 p-1 rounded-2xl border border-white/5">
          <TabButton 
            active={activeTab === 'stats'} 
            onClick={() => setActiveTab('stats')} 
            icon={<Activity size={16} />} 
            label={t('admin.monitoring')} 
          />
          <TabButton 
            active={activeTab === 'templates'} 
            onClick={() => setActiveTab('templates')} 
            icon={<Files size={16} />} 
            label={t('admin.templates')} 
          />
          <TabButton 
            active={activeTab === 'feedback'} 
            onClick={() => setActiveTab('feedback')} 
            icon={<MessageSquare size={16} />} 
            label={t('admin.feedback')} 
          />
          <TabButton 
            active={activeTab === 'users'} 
            onClick={() => setActiveTab('users')} 
            icon={<Users size={16} />} 
            label={t('admin.users')} 
          />
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-full opacity-20 gap-4">
            <RefreshCw className="w-12 h-12 animate-spin text-emerald-500" />
            <p className="font-black uppercase tracking-[0.3em] text-xs">{t('chat.thinking')}</p>
          </div>
        ) : (
          <div className="max-w-6xl mx-auto space-y-8 animate-in slide-in-from-bottom-4 duration-700">
            {activeTab === 'stats' && <MonitoringView stats={stats} />}
            {activeTab === 'templates' && <TemplateManagementView templates={templates} onRefresh={loadData} />}
            {activeTab === 'feedback' && <FeedbackView feedback={feedback} />}
            {activeTab === 'users' && <UserManagementView users={users} onRefresh={loadData} currentUserName={userName} />}
          </div>
        )}
      </div>
    </div>
  );
}

function TabButton({ active, onClick, icon, label }: { active: boolean, onClick: () => void, icon: React.ReactNode, label: string }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider transition-all",
        active 
          ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/20" 
          : "text-text-secondary hover:text-text-primary hover:bg-white/5"
      )}
    >
      {icon}
      {label}
    </button>
  );
}

function MonitoringView({ stats }: { stats: any }) {
  const { t } = useTranslation();
  if (!stats) return null;

  const cards = [
    { label: t('admin.users'), value: stats.totalUsers, icon: <Users size={20} />, color: 'blue' },
    { label: t('sidebar.my_cvs'), value: stats.totalCvs, icon: <Files size={20} />, color: 'purple' },
    { label: t('admin.stats'), value: stats.totalAnalyses, icon: <Layout size={20} />, color: 'emerald' },
    { label: t('feedback.title'), value: `${stats.averageRating?.toFixed(1) || 'N/A'}/5.0`, icon: <Star size={20} />, color: 'amber' },
  ];

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {cards.map((card, i) => (
          <div key={i} className="bg-surface/40 border border-white/5 p-6 rounded-[2rem] hover:border-white/15 transition-all group">
            <div className={`w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center mb-4 transition-transform group-hover:scale-110`}>
              {card.icon}
            </div>
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-text-secondary mb-1">{card.label}</p>
            <p className="text-3xl font-black font-outfit text-text-primary tracking-tight">{card.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-surface/40 border border-white/5 rounded-[2rem] p-8">
            <h3 className="text-sm font-black uppercase tracking-widest text-text-primary mb-6 flex items-center gap-2">
                <Activity size={16} className="text-emerald-500" />
                {t('admin.health')}
            </h3>
            <div className="space-y-6">
                <HealthItem label="API Gateway" status="Healthy" load={12} />
                <HealthItem label="NER Engine (Python)" status="Healthy" load={45} />
                <HealthItem label="Ollama (LLM)" status="Optimizing" load={88} />
                <HealthItem label="ChromaDB" status="Healthy" load={5} />
            </div>
        </div>
        
        <div className="bg-surface/40 border border-white/5 rounded-[2rem] p-8">
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-sm font-black uppercase tracking-widest text-text-primary flex items-center gap-2">
                    <Search size={16} className="text-blue-500" />
                    Global Logs
                </h3>
                <Badge variant="outline" className="text-[9px] uppercase font-black opacity-50 border-white/10">Tail -100</Badge>
            </div>
            <div className="bg-black/20 rounded-2xl p-4 font-mono text-[11px] h-[200px] overflow-y-auto custom-scrollbar border border-white/5">
                <div className="text-emerald-500/60 opacity-80 mb-1 flex justify-between">
                    <span>[2026-04-05 02:44:11] INFO: Application start sequence completed.</span>
                    <span className="opacity-40 italic">CV-GATE-01</span>
                </div>
                 <div className="text-blue-500/60 opacity-80 mb-1 flex justify-between">
                    <span>[2026-04-05 06:12:05] DEBUG: NER Parser language detected: VI.</span>
                    <span className="opacity-40 italic">NER-SVC-01</span>
                </div>
                <div className="text-text-secondary opacity-40 mb-1 flex justify-between">
                    <span>[2026-04-05 09:58:12] TRACE: Heartbeat sent to central node.</span>
                    <span className="opacity-40 italic">SYS-MON</span>
                </div>
                 <div className="text-rose-500/60 opacity-80 mb-1 flex justify-between">
                    <span>[2026-04-05 10:15:22] WARN: ChromaDB persistence flush delayed (200ms).</span>
                    <span className="opacity-40 italic">DB-VEC-01</span>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
}

function HealthItem({ label, status, load }: { label: string, status: string, load: number }) {
    const isWarn = load > 80;
    return (
        <div className="space-y-2">
            <div className="flex justify-between items-center text-[11px] font-bold uppercase tracking-wider">
                <span className="text-text-secondary">{label}</span>
                <span className={cn(isWarn ? "text-amber-500" : "text-emerald-500")}>{status} • {load}%</span>
            </div>
            <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                <div 
                  className={cn("h-full rounded-full transition-all duration-1000", isWarn ? "bg-amber-500" : "bg-emerald-500")}
                  style={{ width: `${load}%` }}
                />
            </div>
        </div>
    )
}

function TemplateManagementView({ templates, onRefresh }: { templates: any[], onRefresh: () => void }) {
  const { t } = useTranslation();
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-xl font-bold text-text-primary tracking-tight">CV Templates</h2>
          <p className="text-xs text-text-secondary font-medium lowercase tracking-normal">Manage visual engines for resume generation</p>
        </div>
        <Button className="h-10 rounded-xl bg-emerald-500 text-white gap-2 font-bold text-xs uppercase tracking-widest shadow-lg shadow-emerald-500/20">
          <Plus size={14} /> New Template
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {templates.map((tpl, i) => (
          <div key={i} className="bg-surface/40 border border-white/5 rounded-[2rem] overflow-hidden group hover:border-white/15 transition-all">
            <div className="aspect-[4/5] bg-secondary/30 relative flex items-center justify-center p-8">
              <div className="w-full h-full border border-white/10 rounded-lg bg-surface/50 shadow-2xl flex flex-col p-4 space-y-2 opacity-60 group-hover:opacity-100 transition-opacity">
                <div className="w-1/3 h-2 bg-text-primary/20 rounded-full" />
                <div className="w-full h-1 bg-text-primary/5 rounded-full" />
                <div className="w-full h-1 bg-text-primary/5 rounded-full" />
                <div className="w-2/3 h-1 bg-text-primary/5 rounded-full" />
              </div>
              <div className="absolute inset-0 bg-emerald-500/10 opacity-0 group-hover:opacity-100 transition-all flex items-center justify-center gap-3">
                 <Button size="icon" className="w-10 h-10 rounded-full bg-white text-black hover:scale-110"><FileEdit size={16}/></Button>
                 <Button size="icon" className="w-10 h-10 rounded-full bg-white text-rose-500 hover:scale-110"><Trash2 size={16}/></Button>
              </div>
            </div>
            <div className="p-6">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-bold text-text-primary text-sm uppercase tracking-tight">{tpl.name}</h4>
                <Badge variant={tpl.isPublished ? 'success' : 'secondary'} className="text-[9px] uppercase font-black">
                    {tpl.isPublished ? 'Active' : 'Draft'}
                </Badge>
              </div>
              <div className="flex items-center gap-4 mt-4 pt-4 border-t border-white/5">
                <div className="flex flex-col">
                  <span className="text-[10px] font-black uppercase tracking-widest text-text-muted/60">Layout</span>
                  <span className="text-xs font-bold text-text-secondary">{tpl.layoutType || 'Standard'}</span>
                </div>
                 <div className="flex flex-col">
                  <span className="text-[10px] font-black uppercase tracking-widest text-text-muted/60">Usage</span>
                  <span className="text-xs font-bold text-text-secondary">420 times</span>
                </div>
              </div>
            </div>
          </div>
        ))}
        {/* Placeholder for "Add" */}
         <button className="border-2 border-dashed border-white/5 rounded-[2rem] aspect-[4/5] flex flex-col items-center justify-center gap-4 text-text-secondary/40 hover:text-emerald-500 hover:border-emerald-500/20 hover:bg-emerald-500/5 transition-all group">
            <div className="w-16 h-16 rounded-full border-2 border-dashed border-current flex items-center justify-center group-hover:scale-110 transition-transform">
                <Plus size={32} />
            </div>
            <span className="text-xs font-black uppercase tracking-[0.2em]">Deploy Engine</span>
         </button>
      </div>
    </div>
  );
}

function FeedbackView({ feedback }: { feedback: any[] }) {
  const { t } = useTranslation();
  return (
    <div className="space-y-6">
      <div className="mb-2">
        <h2 className="text-xl font-bold text-text-primary tracking-tight italic">Quality Feedback</h2>
        <p className="text-xs text-text-secondary font-medium lowercase tracking-normal">Direct user feedback on AI-generated content</p>
      </div>

      <div className="bg-surface/40 border border-white/5 rounded-[2rem] overflow-hidden">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-white/5 bg-white/2">
              <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-text-muted">Type</th>
              <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-text-muted">Rating</th>
              <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-text-muted">Comment</th>
              <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-text-muted text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {feedback.map((f, i) => (
              <tr key={i} className="hover:bg-white/2 transition-colors">
                <td className="px-6 py-5">
                  <Badge variant="outline" className="text-[9px] uppercase font-black border-white/10 opacity-60">
                    {f.type}
                  </Badge>
                </td>
                <td className="px-6 py-5">
                  <div className="flex gap-1">
                    {[1,2,3,4,5].map(s => (
                        <Star key={s} size={10} className={s <= f.rating ? 'fill-amber-400 text-amber-400' : 'text-white/10'} />
                    ))}
                  </div>
                </td>
                <td className="px-6 py-5">
                  <p className="text-sm text-text-secondary truncate max-w-md font-medium tracking-tight">
                    {f.comment || <span className="opacity-20 italic">No comment provided</span>}
                  </p>
                </td>
                <td className="px-6 py-5 text-right">
                   <button className="p-2 text-text-secondary hover:text-text-primary hover:bg-white/5 rounded-xl transition-all">
                      <ChevronRight size={16} />
                   </button>
                </td>
              </tr>
            ))}
            {feedback.length === 0 && (
                <tr>
                    <td colSpan={4} className="px-6 py-20 text-center text-text-secondary opacity-30 text-sm font-bold uppercase tracking-widest">
                        Zero Feedback Records Syncing
                    </td>
                </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function UserManagementView({ users, onRefresh, currentUserName }: { users: any[], onRefresh: () => void, currentUserName: string }) {
  const { t } = useTranslation();
  const handleToggleRole = async (user: any) => {
    // Only block if the current user is trying to DEMOTE themselves
    if (user.name === currentUserName && user.role === 'Admin') {
      alert("You cannot demote yourself. Please use another admin account for this action.");
      return;
    }
    
    try {
      const newRole = user.role === 'Admin' ? 'User' : 'Admin';
      await adminApi.updateUserRole(user.id, newRole);
      onRefresh();
    } catch (error) {
      console.error('Failed to update role', error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="mb-2">
        <h2 className="text-xl font-bold text-text-primary tracking-tight">User Management</h2>
        <p className="text-xs text-text-secondary font-medium lowercase tracking-normal">Control access levels and roles</p>
      </div>

      <div className="bg-surface/40 border border-white/5 rounded-[2rem] overflow-hidden">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-white/5 bg-white/2">
              <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-text-muted">User</th>
              <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-text-muted">Role</th>
              <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-text-muted">Joined</th>
              <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-text-muted text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {users.map((user, i) => (
              <tr key={i} className="hover:bg-white/2 transition-colors">
                <td className="px-6 py-5">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20 text-[10px] font-bold text-indigo-400">
                      {user.name.charAt(0)}
                    </div>
                    <div>
                      <div className="text-sm font-bold text-text-primary">{user.name}</div>
                      <div className="text-[10px] text-text-secondary opacity-60">{user.email}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-5">
                  <Badge variant={user.role === 'Admin' ? 'success' : 'secondary'} className="text-[9px] uppercase font-black">
                    {user.role}
                  </Badge>
                </td>
                <td className="px-6 py-5">
                  <span className="text-[11px] text-text-secondary font-medium italic">
                    {new Date(user.createdAt).toLocaleDateString()}
                  </span>
                </td>
                <td className="px-6 py-5 text-right">
                  <Button 
                    size="sm" 
                    variant="ghost" 
                    onClick={() => handleToggleRole(user)}
                    className={cn(
                        "h-8 px-3 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all",
                        user.role === 'Admin' 
                            ? "text-rose-400 hover:text-rose-300 hover:bg-rose-900/20" 
                            : "text-emerald-400 hover:text-emerald-300 hover:bg-emerald-900/20",
                        (user.name === currentUserName && user.role === 'Admin') && "opacity-50 cursor-not-allowed"
                    )}
                  >
                    {user.role === 'Admin' ? 'Demote' : 'Promote'}
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Star({ size=16, className="" }) {
    return <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" /></svg>;
}
