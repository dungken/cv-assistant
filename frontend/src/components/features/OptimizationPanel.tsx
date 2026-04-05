import React, { useState } from 'react';
import { 
  Sparkles, ChevronDown, ChevronUp, Bot, 
  Lightbulb, ShieldCheck, Target, Zap, 
  ArrowRight, CheckCircle2, Loader2, Info
} from 'lucide-react';

interface OptimizationSuggestion {
  id: string;
  category: string;
  priority: 'critical' | 'important' | 'nice_to_have';
  title: string;
  description: string;
  why: string;
  how: string;
  evidence: string;
  confidence: number;
  preview?: string;
}

interface OptimizationPanelProps {
  suggestions: OptimizationSuggestion[];
  onApply: (id: string, preview?: string) => Promise<void>;
  isLoading?: boolean;
}

const OptimizationPanel: React.FC<OptimizationPanelProps> = ({ suggestions, onApply, isLoading }) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [applyingId, setApplyingId] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-6 text-center">
        <div className="relative">
          <div className="w-16 h-16 rounded-full border-4 border-indigo-500/20 border-t-indigo-500 animate-spin" />
          <Bot className="absolute inset-0 m-auto w-6 h-6 text-indigo-400" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-white">AI is analyzing your CV...</h3>
          <p className="text-sm text-slate-400">Comparing your data against industry benchmarks and job requirements.</p>
        </div>
      </div>
    );
  }

  const handleApply = async (id: string, preview?: string) => {
    setApplyingId(id);
    try {
      await onApply(id, preview);
    } finally {
      setApplyingId(null);
    }
  };

  const getPriorityStyles = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-500/10 text-red-400 border-red-500/20';
      case 'important': return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'nice_to_have': return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      default: return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
      <div className="flex items-center justify-between px-2">
        <h3 className="text-sm font-black text-slate-500 uppercase tracking-widest flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-indigo-400" /> AI Optimization
        </h3>
        <span className="text-[10px] font-bold bg-indigo-500/10 text-indigo-400 px-2 py-0.5 rounded-full border border-indigo-500/20">
          POWERED BY GEMINI
        </span>
      </div>

      <div className="space-y-4">
        {suggestions.map((suggestion) => (
          <div 
            key={suggestion.id}
            className={`group rounded-2xl border transition-all duration-300 overflow-hidden shadow-sm hover:shadow-xl hover:shadow-indigo-500/5 ${
              expandedId === suggestion.id 
                ? 'bg-surface border-accent-primary/30 ring-1 ring-accent-primary/10' 
                : 'bg-surface/40 border-main-border hover:border-accent-primary/20 hover:bg-surface/60'
            }`}
          >
            {/* Header */}
            <div 
              className="p-5 cursor-pointer flex items-start gap-5"
              onClick={() => setExpandedId(expandedId === suggestion.id ? null : suggestion.id)}
            >
              <div className="mt-1">
                <div className={`p-2.5 rounded-xl transition-colors ${
                  expandedId === suggestion.id ? 'bg-accent-primary text-white' : 'bg-accent-primary/10 text-accent-primary'
                }`}>
                  <Lightbulb className="w-5 h-5" />
                </div>
              </div>
              <div className="flex-1 space-y-1.5 text-left">
                <div className="flex items-center gap-2.5 flex-wrap">
                  <span className={`text-[9px] uppercase font-black px-2 py-0.5 rounded-lg border shadow-sm ${getPriorityStyles(suggestion.priority)}`}>
                    {suggestion.priority.replace('_', ' ')}
                  </span>
                  <span className="text-[10px] font-black text-text-muted uppercase tracking-[0.15em]">
                    {suggestion.category}
                  </span>
                </div>
                <h4 className="font-extrabold text-text-primary leading-snug text-[15px] font-outfit">
                  {suggestion.title}
                </h4>
              </div>
              <div className="mt-1.5">
                {expandedId === suggestion.id ? 
                  <ChevronUp className="w-4 h-4 text-accent-primary" /> : 
                  <ChevronDown className="w-4 h-4 text-text-muted group-hover:text-accent-primary transition-colors" />
                }
              </div>
            </div>

            {/* Expanded Content */}
            {expandedId === suggestion.id && (
              <div className="px-6 pb-6 space-y-6 pt-3 animate-in fade-in slide-in-from-top-2 duration-300 border-t border-main-border/50">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <p className="text-[10px] font-black text-accent-primary uppercase tracking-widest flex items-center gap-1.5">
                      <Target className="w-3 h-3" /> The Rationale
                    </p>
                    <p className="text-[13px] text-text-secondary leading-relaxed bg-accent-primary/5 p-3 rounded-xl border border-accent-primary/10 italic">
                      "{suggestion.why}"
                    </p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-[10px] font-black text-emerald-500 uppercase tracking-widest flex items-center gap-1.5">
                      <ShieldCheck className="w-3 h-3" /> The Evidence
                    </p>
                    <p className="text-[13px] text-text-secondary leading-relaxed bg-emerald-500/5 p-3 rounded-xl border border-emerald-500/10">
                      {suggestion.evidence}
                    </p>
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-surface-hover border border-main-border space-y-3 shadow-inner">
                  <p className="text-[10px] font-black text-text-muted uppercase tracking-widest flex items-center gap-1.5">
                    <Target className="w-3 h-3 text-accent-primary" /> Plan
                  </p>
                  <p className="text-[14px] text-text-primary leading-relaxed font-medium">
                    {suggestion.how}
                  </p>
                </div>

                {suggestion.preview && (
                  <div className="p-5 rounded-2xl bg-accent-primary/5 border border-accent-primary/10 space-y-4 shadow-sm">
                    <div className="flex items-center justify-between">
                      <p className="text-[10px] font-black text-accent-primary uppercase tracking-widest flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5" /> AI Recommendation
                      </p>
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 rounded-full bg-accent-primary/10 overflow-hidden">
                          <div 
                            className="h-full bg-accent-primary" 
                            style={{ width: `${suggestion.confidence * 100}%` }} 
                          />
                        </div>
                        <span className="text-[9px] font-black text-accent-primary uppercase">
                          {Math.round(suggestion.confidence * 100)}% Match
                        </span>
                      </div>
                    </div>
                      <div className="text-sm text-slate-300 bg-slate-950/50 p-2.5 rounded-lg border border-indigo-500/10 font-mono text-[13px]">
                        {suggestion.preview}
                      </div>
                      <button 
                        onClick={() => handleApply(suggestion.id, suggestion.preview)}
                        disabled={applyingId === suggestion.id}
                        className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all shadow-lg shadow-indigo-500/20 flex items-center justify-center gap-2"
                      >
                        {applyingId === suggestion.id ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            UPDATING CV...
                          </>
                        ) : (
                          <>
                            <Sparkles className="w-3.5 h-3.5" />
                            MAGIC APPLY SUGGESTION
                          </>
                        )}
                      </button>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>


      <div className="p-4 rounded-2xl bg-indigo-500/5 border border-indigo-500/10 flex items-center gap-3">
        <ShieldCheck className="w-5 h-5 text-indigo-400" />
        <p className="text-[11px] text-indigo-400/80 font-medium leading-tight">
          Optimization suggestions are based on real-time analysis of your CV data and target JD requirements.
        </p>
      </div>
    </div>
  );
};

export default OptimizationPanel;
