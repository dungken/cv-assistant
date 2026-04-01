import React, { useState, useRef } from 'react';
import { UploadCloud, CheckCircle, Loader2, Brain, FileText, Hash, Eye } from 'lucide-react';
import { nerApi, ParseResult, Entity, ExperienceItem } from '../../services/api';

// Color map for entity labels
const LABEL_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  SKILL:     { bg: 'bg-sky-500/10',    text: 'text-sky-400',    border: 'border-sky-500/30' },
  ORG:       { bg: 'bg-violet-500/10', text: 'text-violet-400', border: 'border-violet-500/30' },
  JOB_TITLE: { bg: 'bg-amber-500/10',  text: 'text-amber-400',  border: 'border-amber-500/30' },
  DATE:      { bg: 'bg-slate-500/10',  text: 'text-slate-400',  border: 'border-slate-500/30' },
  DEGREE:    { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/30' },
  MAJOR:     { bg: 'bg-teal-500/10',   text: 'text-teal-400',   border: 'border-teal-500/30' },
  CERT:      { bg: 'bg-lime-500/10',   text: 'text-lime-400',   border: 'border-lime-500/30' },
  PROJECT:   { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/30' },
  LOC:       { bg: 'bg-rose-500/10',   text: 'text-rose-400',   border: 'border-rose-500/30' },
  PER:       { bg: 'bg-pink-500/10',   text: 'text-pink-400',   border: 'border-pink-500/30' },
};

const DEFAULT_COLOR = { bg: 'bg-gray-500/10', text: 'text-gray-400', border: 'border-gray-500/30' };

type Status = 'idle' | 'parsing' | 'done' | 'error';

function ExperienceCard({ item, title }: { item: ExperienceItem; title: string }) {
  return (
    <div className="bg-surface/40 border border-border-main/5 rounded-2xl p-6 hover:border-border-main/20 transition-all group">
      <div className="flex justify-between items-start mb-4">
        <h4 className="text-lg font-bold text-text-primary group-hover:text-accent-primary transition-colors">{item.anchor}</h4>
        <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded bg-accent-primary/10 text-accent-primary border border-accent-primary/20">
          {title}
        </span>
      </div>
      
      {item.description && (
        <p className="text-sm text-text-secondary leading-relaxed mb-5 border-l-2 border-border-main/10 pl-4">
          {item.description}
        </p>
      )}

      <div className="flex flex-wrap gap-2">
        {(item.entities ?? []).map((ent, idx) => {
          const color = LABEL_COLORS[ent.type] || DEFAULT_COLOR;
          return (
            <span key={idx} title={ent.type} className={`px-2.5 py-1 rounded-md border text-[11px] font-bold ${color.bg} ${color.text} ${color.border} flex items-center gap-1.5`}>
              <span className="w-1.5 h-1.5 rounded-full bg-current opacity-40"></span>
              {ent.text}
            </span>
          );
        })}
      </div>
    </div>
  );
}

export default function CVUpload() {
  const [isHovering, setIsHovering] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<Status>('idle');
  const [result, setResult] = useState<ParseResult | null>(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [showSummary, setShowSummary] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const acceptFile = (f: File) => {
    setFile(f);
    setStatus('idle');
    setResult(null);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsHovering(false);
    if (e.dataTransfer.files?.[0]) acceptFile(e.dataTransfer.files[0]);
  };

  const handleParse = async () => {
    if (!file) return;
    setStatus('parsing');
    setErrorMsg('');
    try {
      const res = await nerApi.parseCv(file);
      setResult(res.data);
      setStatus('done');
    } catch (e: any) {
      setErrorMsg(e?.response?.data?.detail || 'An error occurred. Is the NER service running?');
      setStatus('error');
    }
  };

  const handleReset = () => {
    setFile(null);
    setStatus('idle');
    setResult(null);
  };

  const totalExperience = (result?.experience?.length || 0) + (result?.projects?.length || 0);

  return (
    <div className="p-8 max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h2 className="text-4xl font-black tracking-tighter mb-2">Structural Ingestion</h2>
          <p className="text-text-secondary">Visual-aware parsing with hierarchical block grouping.</p>
        </div>
        {status === 'done' && (
          <button onClick={handleReset} className="px-6 py-2 rounded-full border border-border-main text-sm font-bold hover:bg-surface transition-all">
            Upload New
          </button>
        )}
      </div>

      {/* Upload Zone */}
      {status !== 'done' && (
        <div
          onDragOver={(e) => { e.preventDefault(); setIsHovering(true); }}
          onDragLeave={() => setIsHovering(false)}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-3xl p-16 flex flex-col items-center justify-center transition-all duration-300 mb-6 ${
            isHovering ? 'border-accent-primary bg-accent-primary/5 scale-[1.01]' : 'border-border-main/20 bg-surface/50'
          }`}
        >
          {/* Always-mounted hidden input for stability */}
          <input
            ref={inputRef}
            type="file"
            className="hidden"
            onChange={(e) => {
              if (e.target.files?.[0]) {
                acceptFile(e.target.files[0]);
                e.target.value = ''; // Clear value to allow re-selection of the same file
              }
            }}
            accept=".pdf"
          />

          {file ? (
            <div className="flex flex-col items-center gap-4 text-center">
              <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                <CheckCircle className="w-7 h-7 text-emerald-500" />
              </div>
              <div>
                <p className="font-bold text-text-primary text-lg">{file.name}</p>
                <p className="text-sm text-text-muted mt-1">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
              <div className="flex gap-3 mt-2">
                <button onClick={() => setFile(null)} className="px-5 py-2 rounded-full border border-border-main text-text-secondary text-sm hover:bg-overlay transition-all">
                  Change
                </button>
                <button
                  onClick={handleParse}
                  disabled={status === 'parsing'}
                  className="px-8 py-2 rounded-full bg-accent-primary text-white font-bold text-sm hover:shadow-[0_0_20px_rgba(37,99,235,0.4)] transition-all flex items-center gap-2 disabled:opacity-60"
                >
                  {status === 'parsing' ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> Structuring…</>
                  ) : (
                    <><Brain className="w-4 h-4" /> Start Parsing</>
                  )}
                </button>
              </div>
            </div>
          ) : (
            <>
              <div className="w-20 h-20 rounded-full bg-overlay flex items-center justify-center mb-5">
                <UploadCloud className="w-9 h-9 text-text-secondary" />
              </div>
              <h3 className="text-xl font-bold mb-2">Drop your CV here</h3>
              <p className="text-text-muted text-sm text-center max-w-xs mb-6">
                AI will decompose your CV into logical sections and associate entities with their context.
              </p>
              <button 
                onClick={() => inputRef.current?.click()}
                className="px-8 py-3 rounded-full bg-text-primary text-canvas font-bold hover:bg-text-secondary transition-colors"
              >
                Select PDF
              </button>
            </>
          )}
        </div>
      )}

      {/* Error State */}
      {status === 'error' && (
        <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 mb-6 flex gap-4 items-start">
          <span className="text-2xl mt-0.5">⚠️</span>
          <div>
            <p className="font-bold">Parsing Failed</p>
            <p className="text-sm mt-1 opacity-80">{errorMsg}</p>
          </div>
        </div>
      )}

      {/* Results Panel */}
      {status === 'done' && result && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-in zoom-in-95 duration-500">
          
          {/* Main Feed: Experience & Projects */}
          <div className="lg:col-span-2 space-y-6">
            <h3 className="text-xl font-bold flex items-center gap-3">
              <FileText className="w-5 h-5 text-accent-primary" /> 
              Professional Background
              <span className="bg-surface border border-border-main/20 text-[10px] px-2 py-0.5 rounded-lg text-text-muted">
                {totalExperience} Blocks
              </span>
            </h3>

            {result.summary && (
              <div className="bg-accent-primary/5 border border-accent-primary/10 rounded-2xl p-6 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                  <Brain className="w-12 h-12" />
                </div>
                <p className="text-xs font-black uppercase tracking-widest text-accent-primary mb-3">Professional Summary</p>
                <p className="text-sm text-text-primary leading-relaxed">{result.summary}</p>
              </div>
            )}

            <div className="space-y-4">
              {(result.experience ?? []).map((item, i) => (
                <ExperienceCard key={`exp-${i}`} item={item} title="Experience" />
              ))}
              {(result.projects ?? []).map((item, i) => (
                <ExperienceCard key={`proj-${i}`} item={item} title="Project" />
              ))}
              {(result.education ?? []).map((item, i) => (
                <ExperienceCard key={`edu-${i}`} item={item} title="Education" />
              ))}
              {(result.certifications as ExperienceItem[] ?? []).map((item, i) => (
                <ExperienceCard key={`cert-${i}`} item={item} title="Certification" />
              ))}
              {totalExperience === 0 && (result.education ?? []).length === 0 && (result.certifications ?? []).length === 0 && (
                <div className="p-12 text-center border border-dashed border-border-main/20 rounded-3xl text-text-muted">
                  No structured items found. Try another CV with a standard layout.
                </div>
              )}
            </div>
          </div>

          {/* Sidebar: Skills & Metadata */}
          <div className="space-y-8">
            {/* Categorized Skills */}
            <div className="bg-surface/50 border border-border-main/10 rounded-3xl p-6">
              <h3 className="text-lg font-bold mb-6 flex items-center gap-2">
                <Brain className="w-4 h-4 text-violet-400" />
                Skill Intelligence
              </h3>
              
              <div className="space-y-6">
                {(Object.entries(result.skills ?? {}) as [string, string[]][]).map(([category, items]) => (
                  <div key={category}>
                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-text-muted mb-3 flex justify-between items-center">
                      {category}
                      <span className="font-normal opacity-50">{(items ?? []).length}</span>
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {(items ?? []).map((skill, i) => (
                        <span key={i} className="px-2.5 py-1 rounded-lg bg-surface border border-border-main/10 text-xs font-medium text-text-secondary">
                          {skill}
                        </span>
                      ))}
                      {(items ?? []).length === 0 && <span className="text-[10px] italic text-text-muted/50">No identified skills</span>}
                    </div>
                  </div>
                ))}
                {Object.keys(result.skills ?? {}).length === 0 && (
                  <p className="text-sm text-text-muted italic">No skill categories extracted.</p>
                )}
              </div>
            </div>

            {/* Parsing Stats */}
            <div className="p-6 rounded-3xl bg-overlay/30 border border-border-main/10">
              <p className="text-xs font-bold text-text-muted uppercase mb-4 tracking-widest">Parsing Metadata</p>
              <div className="space-y-4">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-text-secondary">Status</span>
                  <span className="text-emerald-500 font-bold flex items-center gap-1.5">
                    <CheckCircle className="w-3.5 h-3.5" /> {result.status || 'Success'}
                  </span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-text-secondary">Source File</span>
                  <span className="text-text-primary font-medium truncate max-w-[120px]" title={result.filename}>{result.filename}</span>
                </div>
              </div>
            </div>
          </div>

        </div>
      )}
    </div>
  );
}
