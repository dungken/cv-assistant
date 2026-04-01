import React, { useState } from 'react';
import { Target, Activity, Zap } from 'lucide-react';
import { skillApi } from '../../services/api';

export default function SkillMatch() {
  const [cvSkills, setCvSkills] = useState('Python, React, Node.js, SQL');
  const [jdText, setJdText] = useState('We are looking for a Fullstack Developer with experience in React, Python, and AWS.');
  const [results, setResults] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleMatch = async () => {
    setIsLoading(true);
    try {
      const skillsArray = cvSkills.split(',').map(s => s.trim()).filter(s => s);
      const res = await skillApi.match(skillsArray, jdText);
      setResults(res.data);
    } catch (e) {
      console.error(e);
    }
    setIsLoading(false);
  };

  return (
    <div className="p-8 max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex items-center gap-4 mb-2">
        <Target className="w-8 h-8 text-accent-primary" />
        <h2 className="text-3xl font-black tracking-tight">Skill Correlation Matrix</h2>
      </div>
      <p className="text-text-secondary mb-8">Compare your extracted skills against Job Descriptions to calculate semantic overlaps.</p>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <div className="space-y-4">
          <label className="block text-sm font-bold text-text-muted uppercase tracking-wider">Your Capabilities (Comma separated)</label>
          <textarea 
            value={cvSkills}
            onChange={e => setCvSkills(e.target.value)}
            className="w-full h-48 bg-surface border border-border-main/20 rounded-2xl p-6 text-text-primary focus:outline-none focus:border-accent-primary/50 transition-colors resize-none"
            placeholder="e.g. Python, Agile, Project Management"
          />
        </div>
        <div className="space-y-4">
          <label className="block text-sm font-bold text-text-muted uppercase tracking-wider">Target Job Description</label>
          <textarea 
            value={jdText}
            onChange={e => setJdText(e.target.value)}
            className="w-full h-48 bg-surface border border-border-main/20 rounded-2xl p-6 text-text-primary focus:outline-none focus:border-accent-primary/50 transition-colors resize-none"
            placeholder="Paste the job description here..."
          />
        </div>
      </div>

      <div className="flex justify-center mb-12">
        <button 
          onClick={handleMatch}
          disabled={isLoading}
          className="px-10 py-4 rounded-full bg-accent-primary text-white font-bold tracking-wide hover:shadow-[0_0_20px_rgba(37,99,235,0.4)] transition-all flex items-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Processing Neural Match...' : 'Initialize Analysis'}
          <Zap className={`w-5 h-5 ${isLoading ? 'animate-pulse' : ''}`} />
        </button>
      </div>

      {results && (
        <div className="bg-surface/50 border border-border-main/10 rounded-3xl p-8 animate-in zoom-in-95 duration-500">
          <div className="flex items-center justify-between mb-8">
             <h3 className="text-2xl font-bold">Analysis Results</h3>
             <div className="px-6 py-2 rounded-full bg-overlay border border-border-main flex items-center gap-2">
                <Activity className="w-4 h-4 text-emerald-500" />
                <span className="font-bold">Match Score: <span className="text-emerald-500">{results.overall_score}%</span></span>
             </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h4 className="font-bold text-text-muted uppercase text-sm mb-4 tracking-wider">Exact Matches</h4>
              <div className="flex flex-wrap gap-2">
                {results.exact_matches.length > 0 ? results.exact_matches.map((m: string, i: number) => (
                  <span key={i} className="px-4 py-2 rounded-xl bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 text-sm font-medium">
                    {m}
                  </span>
                )) : <span className="text-text-secondary text-sm">No exact matches found.</span>}
              </div>
            </div>
            <div>
              <h4 className="font-bold text-text-muted uppercase text-sm mb-4 tracking-wider">Semantic Equivalents</h4>
              <div className="space-y-3">
                {results.semantic_matches.length > 0 ? results.semantic_matches.map((m: any, i: number) => (
                  <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-overlay/50 border border-border-main/5 text-sm">
                    <span className="text-text-primary font-medium">{m.cv_skill}</span>
                    <span className="text-text-muted text-xs mx-2">→</span>
                    <span className="text-accent-secondary font-medium">{m.jd_skill}</span>
                    <span className="ml-auto text-xs font-mono text-text-secondary bg-surface px-2 py-1 rounded-md">
                      {(m.similarity * 100).toFixed(0)}%
                    </span>
                  </div>
                )) : <span className="text-text-secondary text-sm">No semantic matches found.</span>}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
