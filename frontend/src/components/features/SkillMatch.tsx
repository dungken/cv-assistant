import React, { useState } from 'react';
import { 
  Target, Activity, Zap, Layers, 
  FileText, Search, Plus, Trash2, 
  ArrowRight, Sparkles, Brain, Cpu,
  Briefcase
} from 'lucide-react';
import { skillApi, SkillMatchResponse } from '../../services/api';
import SkillGapDashboard from './SkillGapDashboard';

export default function SkillMatch() {
  const [cvSkills, setCvSkills] = useState('React, TypeScript, Tailwind CSS, Node.js, Express, PostgreSQL, Docker, Git');
  const [jdTexts, setJdTexts] = useState<string[]>(['We are looking for a Senior Frontend Developer with expertise in React, TypeScript, and AWS. Experience with Next.js and CI/CD pipelines is a plus. Minimum 5 years of experience. Master degree related to Computer Science preferred.']);
  const [results, setResults] = useState<SkillMatchResponse | null>(null);
  const [multiResults, setMultiResults] = useState<SkillMatchResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [mode, setMode] = useState<'single' | 'multi'>('single');

  const handleMatch = async () => {
    setIsLoading(true);
    setResults(null);
    setMultiResults([]);
    
    try {
      const skillsArray = cvSkills.split(',').map(s => s.trim()).filter(s => s);
      const cvDetails = {
        skills: skillsArray,
        experience_years: 3.5, // Dummy for now, would be parsed from CV
        education_level: 'Bachelor'
      };

      if (mode === 'single') {
        const res = await skillApi.match(skillsArray, jdTexts[0], cvDetails);
        setResults(res.data);
      } else {
        const res = await skillApi.matchMulti(cvDetails, jdTexts);
        setMultiResults(res.data.results);
      }
    } catch (e) {
      console.error(e);
    }
    setIsLoading(false);
  };

  const addJD = () => {
    if (jdTexts.length < 5) {
      setJdTexts([...jdTexts, '']);
    }
  };

  const updateJD = (index: number, text: string) => {
    const newJds = [...jdTexts];
    newJds[index] = text;
    setJdTexts(newJds);
  };

  const removeJD = (index: number) => {
    if (jdTexts.length > 1) {
      setJdTexts(jdTexts.filter((_, i) => i !== index));
    }
  };

  return (
    <div className="p-8 w-full max-w-7xl mx-auto space-y-16 animate-in fade-in duration-700">
      
      {/* Refined Compact Header */}
      <div className="flex flex-col items-center text-center space-y-4 max-w-2xl mx-auto">
        <div className="relative">
           <div className="absolute -inset-4 bg-accent-primary/20 blur-[30px] rounded-full opacity-50" />
           <div className="relative p-4 rounded-3xl bg-surface border border-white/10 shadow-2xl">
              <Brain className="w-10 h-10 text-accent-primary" />
           </div>
        </div>
        <h2 className="text-5xl font-black tracking-tight leading-tight">
          Neural <span className="text-accent-primary">Gap</span> Analysis
        </h2>
        <p className="text-text-secondary text-lg font-medium opacity-80 leading-relaxed">
          Unlock your competitive edge with advanced semantic correlation between your professional arsenal and target role requirements.
        </p>
        
        {/* Sleek Switcher */}
        <div className="flex bg-surface/50 p-1 rounded-2xl border border-white/5 shadow-inner mt-8">
          <button 
            onClick={() => setMode('single')}
            className={`px-8 py-2.5 rounded-xl text-xs font-black uppercase tracking-widest transition-all flex items-center gap-2 ${mode === 'single' ? 'bg-accent-primary text-white shadow-[0_10px_30px_rgba(37,99,235,0.4)]' : 'text-text-muted hover:text-text-primary'}`}
          >
            <FileText className="w-4 h-4" />
            Precision Match
          </button>
          <button 
            onClick={() => setMode('multi')}
            className={`px-8 py-2.5 rounded-xl text-xs font-black uppercase tracking-widest transition-all flex items-center gap-2 ${mode === 'multi' ? 'bg-accent-primary text-white shadow-[0_10px_30px_rgba(37,99,235,0.4)]' : 'text-text-muted hover:text-text-primary'}`}
          >
            <Layers className="w-4 h-4" />
            Multi-JD Rank
          </button>
        </div>
      </div>
      
      {/* Integrated Entry Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch pt-4">
        {/* Sidebar: Global Context (CV Skills) */}
        <div className="lg:col-span-4 h-full">
          <div className="bg-surface/30 backdrop-blur-md border border-white/5 rounded-[2.5rem] p-8 h-full flex flex-col group hover:border-white/10 transition-all">
            <h3 className="text-[10px] font-black text-text-muted uppercase tracking-[0.2em] mb-6 flex items-center gap-2">
               <Search className="w-4 h-4 text-accent-primary" />
               Your Expertise Matrix
            </h3>
            <textarea 
              value={cvSkills}
              onChange={e => setCvSkills(e.target.value)}
              className="w-full flex-grow bg-white/[0.03] rounded-3xl p-6 text-text-primary focus:outline-none focus:ring-1 ring-accent-primary/40 transition-all resize-none font-medium leading-relaxed text-sm shadow-inner"
              placeholder="React, TypeScript, Node.js..."
            />
            <div className="mt-4 flex items-center gap-3 opacity-40 group-hover:opacity-100 transition-opacity">
               <Cpu className="w-4 h-4 text-accent-primary" />
               <span className="text-[10px] font-black text-text-muted uppercase">Ready for Vectorization</span>
            </div>
          </div>
        </div>

        {/* Main: Job Targets */}
        <div className="lg:col-span-8">
          <div className="bg-surface/30 backdrop-blur-md border border-white/5 rounded-[3rem] p-10 min-h-[450px] relative overflow-hidden flex flex-col">
             <div className="flex items-center justify-between mb-8">
                <h3 className="text-[10px] font-black text-text-muted uppercase tracking-[0.2em] flex items-center gap-2">
                  <Target className="w-4 h-4 text-rose-500" />
                  Target Specifications
                </h3>
                {mode === 'multi' && jdTexts.length < 5 && (
                  <button 
                    onClick={addJD}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-accent-primary/10 text-accent-primary hover:bg-accent-primary/20 transition-all text-[10px] font-black uppercase tracking-widest"
                  >
                    <Plus className="w-4 h-4" />
                    Expand Pool
                  </button>
                )}
             </div>

             <div className="space-y-6 flex-grow">
               {jdTexts.map((text, idx) => (
                 <div key={idx} className="relative group/jd animate-in zoom-in-95 duration-500">
                    <textarea 
                      value={text}
                      onChange={e => updateJD(idx, e.target.value)}
                      className="w-full h-40 bg-white/[0.03] rounded-[2rem] p-8 text-text-primary focus:outline-none focus:ring-1 ring-accent-primary/40 transition-all resize-none font-medium text-sm leading-relaxed shadow-inner"
                      placeholder={`Paste Job Description ${mode === 'multi' ? idx + 1 : ''} here...`}
                    />
                    {mode === 'multi' && jdTexts.length > 1 && (
                      <button 
                        onClick={() => removeJD(idx)}
                        className="absolute top-6 right-6 p-2 rounded-xl bg-rose-500/10 text-rose-500 opacity-0 group-hover/jd:opacity-100 transition-all hover:bg-rose-500/20"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                 </div>
               ))}
             </div>
          </div>
        </div>
      </div>

      {/* Action Sphere */}
      <div className="flex justify-center relative">
        <div className="absolute inset-0 flex items-center justify-center -z-10 pointer-events-none">
           <div className={`w-32 h-32 bg-accent-primary/30 blur-[60px] rounded-full transition-all duration-1000 ${isLoading ? 'scale-[3] opacity-100' : 'scale-100 opacity-20'}`} />
        </div>
        
        <button 
          onClick={handleMatch}
          disabled={isLoading || !cvSkills || jdTexts.some(t => !t)}
          className="group px-16 py-6 rounded-[3rem] bg-accent-primary text-white font-black text-lg tracking-[0.05em] hover:shadow-[0_40px_80px_rgba(37,99,235,0.4)] hover:-translate-y-2 active:translate-y-0 transition-all flex items-center gap-6 disabled:opacity-30 disabled:cursor-not-allowed uppercase"
        >
          {isLoading ? (
            <>
              <Activity className="w-6 h-6 animate-spin" />
              Slicing Neurons...
            </>
          ) : (
            <>
              Execute Assessment
              <div className="p-1 px-2 rounded-lg bg-white/20 text-white group-hover:bg-white text-accent-primary transition-all">
                 <Zap className="w-5 h-5 fill-current" />
              </div>
            </>
          )}
        </button>
      </div>

      {/* Results Portal */}
      {(results || multiResults.length > 0) ? (
        <div className="pt-20 scroll-mt-20 border-t border-white/5 animate-in slide-in-from-bottom-20 duration-1000">
           {results && <SkillGapDashboard data={results} />}
           
           {multiResults.length > 0 && (
             <div className="space-y-12">
                <div className="flex items-center justify-between">
                   <div>
                      <h3 className="text-4xl font-black tracking-tight">Comparative <span className="text-accent-primary">Nexus</span></h3>
                      <p className="text-text-muted font-bold text-sm mt-1 uppercase tracking-widest">{multiResults.length} Dimensions Analyzed</p>
                   </div>
                </div>
                
                <div className="grid grid-cols-1 gap-6">
                   {multiResults.map((res, i) => (
                     <div key={i} className="bg-surface/50 backdrop-blur-xl border border-white/5 rounded-[3rem] p-10 flex flex-col md:flex-row items-center justify-between gap-10 group hover:bg-surface hover:border-accent-primary/20 transition-all cursor-pointer relative overflow-hidden">
                        <div className="absolute inset-y-0 left-0 w-2 bg-accent-primary opacity-0 group-hover:opacity-100 transition-opacity" />
                        
                        <div className="flex items-center gap-8">
                           <div className="w-20 h-20 rounded-[2rem] bg-white/[0.03] border border-white/5 flex flex-col items-center justify-center font-black transition-all group-hover:bg-accent-primary/10 group-hover:border-accent-primary/20">
                              <span className="text-[10px] text-text-muted group-hover:text-accent-primary">RANK</span>
                              <span className="text-3xl text-text-primary">#{i+1}</span>
                           </div>
                           <div>
                              <h4 className="text-2xl font-black group-hover:text-accent-primary transition-colors">{res.jd_title}</h4>
                              <div className="flex items-center gap-2 mt-1">
                                 <Briefcase className="w-3 h-3 text-text-muted" />
                                 <p className="text-text-secondary font-bold uppercase text-[10px] tracking-widest">{res.jd_company}</p>
                              </div>
                           </div>
                        </div>

                        <div className="flex items-center gap-16 text-center">
                           <div className="space-y-1">
                              <p className="text-[10px] font-black text-text-muted uppercase tracking-widest">Match Index</p>
                              <p className="text-4xl font-black text-emerald-500">{res.overall_score}%</p>
                           </div>
                           <div className="hidden md:block space-y-1">
                              <p className="text-[10px] font-black text-text-muted uppercase tracking-widest">Skill Affinity</p>
                              <p className="text-2xl font-black text-text-primary/70">{Math.round(res.breakdown.skills)}%</p>
                           </div>
                           <button 
                             onClick={() => {
                               setResults(res);
                               window.scrollTo({ top: document.getElementById('results-view')?.offsetTop || 1000, behavior: 'smooth' });
                             }}
                             className="p-6 rounded-[2rem] bg-white/[0.03] border border-white/5 text-text-muted hover:bg-accent-primary hover:text-white hover:shadow-2xl transition-all translate-x-4 group-hover:translate-x-0"
                           >
                              <ArrowRight className="w-8 h-8" />
                           </button>
                        </div>
                     </div>
                   ))}
                </div>
                
                {/* Detail view anchor */}
                <div id="results-view" />
                {results && (
                  <div className="mt-32 pt-32 border-t-2 border-dashed border-white/5">
                     <div className="flex items-center justify-center mb-12">
                        <div className="px-6 py-2 rounded-full bg-surface border border-white/10 text-[10px] font-black uppercase tracking-[0.4em] text-text-muted">
                           Comprehensive Dimension Drill-down
                        </div>
                     </div>
                    <SkillGapDashboard data={results} />
                  </div>
                )}
             </div>
           )}
        </div>
      ) : (
        /* Empty State */
        <div className="pt-20 flex flex-col items-center space-y-8 animate-in fade-in slide-in-from-top-10 duration-1000">
           <div className="relative">
              <div className="absolute inset-0 bg-accent-primary/20 blur-[100px] rounded-full scale-150" />
              <div className="w-32 h-32 rounded-[3rem] bg-surface/50 border border-white/5 flex items-center justify-center relative">
                 <Cpu className="w-12 h-12 text-accent-primary/40 animate-pulse" />
              </div>
           </div>
           <div className="text-center space-y-2">
              <h4 className="text-xl font-black tracking-tight text-text-secondary">Neural Engine Idle</h4>
              <p className="text-sm text-text-muted font-medium">Inject professional data to begin multidimensional correlation.</p>
           </div>
        </div>
      )}
    </div>
  );
}
