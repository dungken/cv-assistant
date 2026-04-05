import React, { useState } from 'react';
import { Route, Search, Map, ChevronRight } from 'lucide-react';
import { careerApi } from '../../services/api';

export default function CareerPath() {
  const [currentRole, setCurrentRole] = useState('Data Analyst');
  const [targetRole, setTargetRole] = useState('Data Scientist');
  const [skills, setSkills] = useState('Python, SQL, Excel');
  const [path, setPath] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleGenerate = async () => {
    setIsLoading(true);
    try {
      const skillsArray = skills.split(',').map(s => s.trim()).filter(s => s);
      const res = await careerApi.recommend(currentRole, targetRole, skillsArray);
      setPath(res.data);
    } catch (e) {
      console.error(e);
    }
    setIsLoading(false);
  };

  return (
    <div className="p-8 w-full animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex items-center gap-4 mb-2">
        <Map className="w-8 h-8 text-accent-secondary" />
        <h2 className="text-3xl font-black tracking-tight">Career Trajectory Mapping</h2>
      </div>
      <p className="text-text-secondary mb-10">Generate optimized learning paths based on O*NET occupational data and your current capabilities.</p>
      
      <div className="bg-surface/30  rounded-3xl p-8 mb-10 flex flex-col md:flex-row gap-6">
         <div className="flex-1 space-y-2">
            <label className="text-xs font-bold text-text-muted uppercase tracking-wider">Origin Role</label>
            <input 
              value={currentRole}
              onChange={e => setCurrentRole(e.target.value)}
              className="w-full bg-overlay  rounded-xl px-5 py-3 text-text-primary focus:outline-none focus:border-accent-secondary/50 transition-colors"
              placeholder="E.g. Junior Developer"
            />
         </div>
         <div className="hidden md:flex items-center justify-center pt-6">
            <ChevronRight className="w-6 h-6 text-text-muted" />
         </div>
         <div className="flex-1 space-y-2">
            <label className="text-xs font-bold text-text-muted uppercase tracking-wider">Destination Role</label>
            <input 
              value={targetRole}
              onChange={e => setTargetRole(e.target.value)}
              className="w-full bg-overlay  rounded-xl px-5 py-3 text-text-primary focus:outline-none focus:border-accent-secondary/50 transition-colors"
              placeholder="E.g. Technical Lead"
            />
         </div>
         <div className="flex-1 space-y-2">
            <label className="text-xs font-bold text-text-muted uppercase tracking-wider">Current Arsenal</label>
            <input 
              value={skills}
              onChange={e => setSkills(e.target.value)}
              className="w-full bg-overlay  rounded-xl px-5 py-3 text-text-primary focus:outline-none focus:border-accent-secondary/50 transition-colors"
              placeholder="E.g. React, Node"
            />
         </div>
         <div className="pt-6">
            <button 
              onClick={handleGenerate}
              disabled={isLoading}
              className="h-full px-8 rounded-xl bg-text-primary text-canvas font-bold hover:bg-text-secondary transition-colors disabled:opacity-50"
            >
              {isLoading ? 'Computing...' : 'Calculate'}
            </button>
         </div>
      </div>

      {path && (
        <div className="space-y-8 animate-in zoom-in-95 duration-500">
           <div className="bg-surface/50  rounded-3xl p-8">
              <h3 className="text-xl font-bold mb-6 flex items-center gap-3">
                <Search className="w-5 h-5 text-accent-secondary" /> 
                Skill Gap Analysis
              </h3>
              <div className="flex flex-wrap gap-2">
                {path.skill_gap.missing.map((s: string, i: number) => (
                  <span key={i} className="px-4 py-2 rounded-xl bg-rose-500/10 text-rose-500 border border-rose-500/20 font-medium text-sm">
                    Missing: {s}
                  </span>
                ))}
              </div>
           </div>

           <div className="space-y-6">
              <h3 className="text-xl font-bold flex items-center gap-3 px-2">
                <Route className="w-5 h-5 text-accent-primary" /> 
                Suggested Trajectories
              </h3>
              {path.paths.map((p: any, i: number) => (
                <div key={i} className="bg-surface/50  rounded-3xl p-8 relative overflow-hidden group">
                   <div className="absolute top-0 left-0 w-2 h-full bg-gradient-to-b from-accent-primary to-accent-secondary opacity-50 group-hover:opacity-100 transition-opacity" />
                   <h4 className="text-lg font-bold mb-1 capitalize">{p.path_type} Path</h4>
                   <p className="text-sm text-text-muted mb-6">Estimated time: <span className="font-mono text-text-primary">{p.total_time}</span></p>
                   
                   <div className="space-y-4">
                     {p.steps.map((step: any, j: number) => (
                       <div key={j} className="flex gap-6">
                         <div className="flex flex-col items-center">
                           <div className="w-8 h-8 rounded-full bg-overlay  flex items-center justify-center font-bold text-xs text-text-secondary">
                             {step.step}
                           </div>
                           {j < p.steps.length - 1 && <div className="w-px h-full bg- my-2" />}
                         </div>
                         <div className="pb-6">
                           <h5 className="font-bold text-text-primary">{step.role}</h5>
                           <p className="text-sm text-text-secondary mt-1">{step.description}</p>
                           <div className="mt-3 flex flex-wrap gap-2">
                             {step.skills_to_learn.map((s: string, k: number) => (
                               <span key={k} className="text-xs px-2 py-1 bg-overlay rounded flex items-center gap-1 text-text-muted">
                                 + {s}
                               </span>
                             ))}
                           </div>
                         </div>
                       </div>
                     ))}
                   </div>
                </div>
              ))}
           </div>
        </div>
      )}
    </div>
  );
}
