import React, { useEffect, useState, useRef } from 'react';
import { UploadCloud, CheckCircle, Loader2, Brain, FileText, Hash, Eye, Edit2, Trash2, Check, X, Plus } from 'lucide-react';
import { nerApi, cvDocumentApi, ParseResult, Entity, ExperienceItem, CVData, CvDocument } from '../../services/api';
import { cn } from '../../lib/utils';

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

const ENTITY_TYPES = Object.keys(LABEL_COLORS);

const DEFAULT_COLOR = { bg: 'bg-gray-500/10', text: 'text-gray-400', border: 'border-gray-500/30' };

type Status = 'idle' | 'parsing' | 'done' | 'error';

function ExperienceCard({ 
  item, 
  title, 
  onUpdateEntity, 
  onDeleteEntity,
  onAddEntity 
}: { 
  item: ExperienceItem; 
  title: string;
  onUpdateEntity: (entityIdx: number, newEntity: Entity) => void;
  onDeleteEntity: (entityIdx: number) => void;
  onAddEntity: () => void;
}) {
  const [editingIdx, setEditingIdx] = useState<number | null>(null);
  const [editValue, setEditValue] = useState<Entity | null>(null);

  const startEdit = (idx: number, ent: Entity) => {
    setEditingIdx(idx);
    setEditValue({ ...ent });
  };

  const cancelEdit = () => {
    setEditingIdx(null);
    setEditValue(null);
  };

  const saveEdit = () => {
    if (editingIdx !== null && editValue) {
      onUpdateEntity(editingIdx, editValue);
      cancelEdit();
    }
  };

  return (
    <div className="bg-surface/40  rounded-2xl p-6 hover: transition-all group relative">
      <div className="flex justify-between items-start mb-4">
        <h4 className="text-lg font-bold text-text-primary group-hover:text-accent-primary transition-colors">{item.anchor}</h4>
        <div className="flex items-center gap-2">
          <button 
            onClick={onAddEntity}
            className="p-1.5 rounded-lg bg-surface  text-text-muted hover:text-accent-primary hover:border-accent-primary/30 transition-all"
            title="Add Entity"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
          <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded bg-accent-primary/10 text-accent-primary border border-accent-primary/20">
            {title}
          </span>
        </div>
      </div>
      
      {item.description && (
        <div className="text-sm text-text-secondary leading-relaxed mb-5 border-l-2  pl-4 space-y-1">
          {item.description.split('\n').map((line, i) => {
            const cleanLine = line.trim().replace(/^[-•\*◦]\s*/, '');
            if (!cleanLine) return null;
            return (
              <div key={i} className="flex gap-2 text-[13px]">
                <span className="text-accent-primary opacity-40 mt-1">•</span>
                <span>{cleanLine}</span>
              </div>
            );
          })}
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        {(item.entities ?? []).map((ent, idx) => {
          const isEditing = editingIdx === idx;
          const color = LABEL_COLORS[ent.type] || DEFAULT_COLOR;

          if (isEditing && editValue) {
            return (
              <div key={idx} className="flex items-center gap-1 bg-surface border border-accent-primary/30 rounded-lg p-1 animate-in zoom-in-95 duration-200">
                <select 
                  value={editValue.type}
                  onChange={(e) => setEditValue({ ...editValue, type: e.target.value })}
                  className="bg-overlay text-[10px] font-bold text-text-primary border-none rounded px-1.5 py-0.5 focus:ring-0"
                >
                  {ENTITY_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
                <input 
                  type="text"
                  value={editValue.text}
                  onChange={(e) => setEditValue({ ...editValue, text: e.target.value })}
                  className="bg-overlay text-[11px] text-text-primary border-none rounded px-2 py-0.5 w-32 focus:ring-0"
                  autoFocus
                />
                <button onClick={saveEdit} className="p-1 hover:text-emerald-500 transition-colors"><Check className="w-3.5 h-3.5" /></button>
                <button onClick={cancelEdit} className="p-1 hover:text-rose-500 transition-colors"><X className="w-3.5 h-3.5" /></button>
              </div>
            );
          }

          return (
            <div key={idx} className="group/entity relative">
              <span 
                className={`px-2.5 py-1 rounded-md border text-[11px] font-bold ${color.bg} ${color.text} ${color.border} flex items-center gap-1.5 cursor-default transition-all`}
              >
                <span className="w-1.5 h-1.5 rounded-full bg-current opacity-40"></span>
                {ent.text}
                <span className="text-[9px] opacity-60 font-medium ml-0.5">
                  ({Math.round(ent.confidence * 100)}%)
                </span>
                
                <div className="flex items-center gap-1 ml-1 border-l border-current/20 pl-1.5 opacity-60 group-hover/entity:opacity-100 transition-opacity">
                  <button onClick={() => startEdit(idx, ent)} className="hover:scale-110 transition-transform"><Edit2 className="w-3 h-3" /></button>
                  <button onClick={() => onDeleteEntity(idx)} className="hover:scale-110 transition-transform"><Trash2 className="w-3 h-3 text-rose-500/80" /></button>
                </div>
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

interface CVUploadProps {
  onParsedCvData?: (data: CVData) => void;
}

interface SavedParsedCv {
  docId: number;
  name: string;
  updatedAt: string;
  latestVersionId: number;
}

const pickEntities = (items: ExperienceItem[] | undefined, type: string): string[] => {
  if (!items?.length) return [];
  const values = items.flatMap(i => (i.entities || []).filter(e => e.type === type).map(e => e.text.trim())).filter(Boolean);
  return Array.from(new Set(values));
};

const mapParseResultToCvData = (result: ParseResult): CVData => {
  const jobTitles = pickEntities([...(result.experience || []), ...(result.projects || [])], 'JOB_TITLE');
  const names = pickEntities([...(result.experience || []), ...(result.education || []), ...(result.projects || [])], 'PER');
  const orgs = pickEntities(result.experience || [], 'ORG');
  const locs = pickEntities([...(result.experience || []), ...(result.education || [])], 'LOC');

  const skills = Array.from(
    new Set(Object.values(result.skills || {}).flatMap(list => list || []).map(s => s.trim()).filter(Boolean))
  );

  return {
    personal_info: {
      full_name: names[0] || '',
      email: '',
      phone: '',
      location: locs[0] || '',
      title: jobTitles[0] || '',
    },
    education: (result.education || []).map((item) => ({
      degree: item.anchor || '',
      institution: pickEntities([item], 'ORG')[0] || '',
      graduation_year: '',
      gpa: ''
    })),
    experience: (result.experience || []).map((item) => ({
      company: pickEntities([item], 'ORG')[0] || orgs[0] || '',
      title: pickEntities([item], 'JOB_TITLE')[0] || item.anchor || '',
      duration: pickEntities([item], 'DATE').join(' - ') || '',
      achievements: item.description
        ? item.description.split('\n').map(line => line.trim().replace(/^[-•\*◦]\s*/, '')).filter(Boolean)
        : []
    })),
    skills,
    projects: (result.projects || []).map((item) => ({
      name: item.anchor || '',
      description: item.description || '',
      technologies: pickEntities([item], 'SKILL')
    })),
    certifications: (result.certifications || []).map((item) => ({
      name: item.anchor || '',
      issuer: pickEntities([item], 'ORG')[0] || '',
      year: pickEntities([item], 'DATE')[0] || ''
    }))
  };
};

export default function CVUpload({ onParsedCvData }: CVUploadProps) {
  const [isHovering, setIsHovering] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<Status>('idle');
  const [result, setResult] = useState<ParseResult | null>(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [showSummary, setShowSummary] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [savedParses, setSavedParses] = useState<SavedParsedCv[]>([]);
  const [isLoadingSaved, setIsLoadingSaved] = useState(false);
  const [loadingDocId, setLoadingDocId] = useState<number | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const loadSavedParses = async () => {
    setIsLoadingSaved(true);
    try {
      const res = await cvDocumentApi.list({ sortBy: 'updated' });
      const docs = (res.data || []) as CvDocument[];
      const parsed = docs
        .filter(d => d.versions?.length > 0 && d.name.toLowerCase().startsWith('parsed:'))
        .map(d => ({
          docId: d.id,
          name: d.name,
          updatedAt: d.updatedAt,
          latestVersionId: d.versions[0].id,
        }))
        .slice(0, 8);
      setSavedParses(parsed);
    } catch {
      // Keep silent; upload flow still works without history
    } finally {
      setIsLoadingSaved(false);
    }
  };

  useEffect(() => {
    loadSavedParses();
  }, []);

  const isParseResultLike = (data: any): data is ParseResult =>
    data && typeof data === 'object' && Array.isArray(data.experience) && Array.isArray(data.projects) && typeof data.skills === 'object';

  const buildParsedDocName = (fileName: string) =>
    `Parsed: ${fileName.replace(/\.(pdf|docx)$/i, '')}`;

  const autoSaveParsedResult = async (fileName: string, parsed: ParseResult) => {
    const docName = buildParsedDocName(fileName);
    const payload = JSON.stringify(parsed);

    // Upsert behavior: if a parsed doc with same name exists, append a new version.
    const listRes = await cvDocumentApi.list({ query: docName, sortBy: 'updated' });
    const existing = (listRes.data || []).find(d => d.name.trim().toLowerCase() === docName.trim().toLowerCase());

    if (existing) {
      await cvDocumentApi.createVersion(existing.id, {
        dataJson: payload,
        note: 'Auto-saved from Data Ingestion'
      });
      return;
    }

    await cvDocumentApi.create({
      name: docName,
      dataJson: payload,
      note: 'Auto-saved from Data Ingestion'
    });
  };

  const acceptFile = (f: File) => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(f);
    setPreviewUrl(URL.createObjectURL(f));
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
      onParsedCvData?.(mapParseResultToCvData(res.data));
      try {
        await autoSaveParsedResult(file.name, res.data);
        await loadSavedParses();
      } catch {
        // Non-blocking: parsing succeeded even if autosave failed
      }
      setStatus('done');
    } catch (e: any) {
      setErrorMsg(e?.response?.data?.detail || 'An error occurred. Is the NER service running?');
      setStatus('error');
    }
  };

  const handleReset = () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(null);
    setPreviewUrl(null);
    setStatus('idle');
    setResult(null);
    setSaveSuccess(false);
    setShowPreview(false);
    setShowSummary(false);
  };

  const handleSaveToMyCvs = async () => {
    if (!result || !file) return;
    setIsSaving(true);
    try {
      await cvDocumentApi.create({
        name: buildParsedDocName(file.name),
        dataJson: JSON.stringify(result),
        note: 'Imported from AI Parser'
      });
      await loadSavedParses();
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (e) {
      setErrorMsg('Failed to save document to My CVs');
    } finally {
      setIsSaving(false);
    }
  };

  // --- Entity Management (Task T10) ---
  const updateEntity = (section: keyof ParseResult, blockIdx: number, entityIdx: number, newEntity: Entity) => {
    if (!result) return;
    const newResult = { ...result };
    const items = newResult[section] as ExperienceItem[];
    if (items && items[blockIdx]) {
      items[blockIdx].entities[entityIdx] = newEntity;
      setResult(newResult);
    }
  };

  const deleteEntity = (section: keyof ParseResult, blockIdx: number, entityIdx: number) => {
    if (!result) return;
    const newResult = { ...result };
    const items = newResult[section] as ExperienceItem[];
    if (items && items[blockIdx]) {
      items[blockIdx].entities.splice(entityIdx, 1);
      setResult(newResult);
    }
  };

  const addEntity = (section: keyof ParseResult, blockIdx: number) => {
    if (!result) return;
    const newResult = { ...result };
    const items = newResult[section] as ExperienceItem[];
    if (items && items[blockIdx]) {
      const newEnt: Entity = {
        text: 'New Entity',
        type: 'SKILL',
        start: 0,
        end: 0,
        confidence: 1.0
      };
      items[blockIdx].entities.push(newEnt);
      setResult(newResult);
    }
  };

  const totalExperience = (result?.experience?.length || 0) + (result?.projects?.length || 0);

  const handleLoadSavedParse = async (doc: SavedParsedCv) => {
    setLoadingDocId(doc.docId);
    setErrorMsg('');
    try {
      const detail = await cvDocumentApi.getVersion(doc.docId, doc.latestVersionId);
      const parsed = JSON.parse(detail.data.dataJson);
      if (!isParseResultLike(parsed)) {
        throw new Error('Selected document is not a parsed CV result.');
      }
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setFile(null);
      setPreviewUrl(null);
      setShowPreview(false);
      setResult(parsed);
      onParsedCvData?.(mapParseResultToCvData(parsed));
      setStatus('done');
    } catch {
      setStatus('error');
      setErrorMsg('Không mở được dữ liệu parse từ lịch sử. Có thể đây không phải CV parse từ Upload.');
    } finally {
      setLoadingDocId(null);
    }
  };

  return (
    <div className="p-8 w-full animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h2 className="text-4xl font-black tracking-tighter mb-2">Structural Ingestion</h2>
          <p className="text-text-secondary">Visual-aware parsing with hierarchical block grouping.</p>
        </div>
        {status === 'done' && (
          <button onClick={handleReset} className="px-6 py-2 rounded-full  text-sm font-bold hover:bg-surface transition-all">
            Upload New
          </button>
        )}
      </div>

      {/* Saved Parse History */}
      <div className="mb-6 rounded-2xl border border-white/10 bg-surface/40 p-4">
        <p className="text-xs font-black uppercase tracking-[0.2em] text-text-muted mb-3">CV đã phân tích gần đây</p>
        {isLoadingSaved ? (
          <div className="text-sm text-text-secondary">Đang tải lịch sử...</div>
        ) : savedParses.length === 0 ? (
          <div className="text-sm text-text-secondary">Chưa có dữ liệu đã lưu.</div>
        ) : (
          <div className="space-y-2">
            {savedParses.map((doc) => (
              <button
                key={`${doc.docId}-${doc.latestVersionId}`}
                onClick={() => handleLoadSavedParse(doc)}
                disabled={loadingDocId === doc.docId}
                className="w-full flex items-center justify-between rounded-xl border border-white/10 bg-secondary/30 px-3 py-2 text-left hover:bg-secondary/50 transition-colors disabled:opacity-60"
              >
                <div className="min-w-0">
                  <p className="text-sm font-semibold truncate">{doc.name}</p>
                  <p className="text-[11px] text-text-secondary">
                    {new Date(doc.updatedAt).toLocaleString()}
                  </p>
                </div>
                {loadingDocId === doc.docId ? (
                  <Loader2 className="w-4 h-4 animate-spin text-accent-primary" />
                ) : (
                  <span className="text-xs text-accent-primary font-bold">Mở lại</span>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Upload Zone */}
      {status !== 'done' && (
        <div
          onDragOver={(e) => { e.preventDefault(); setIsHovering(true); }}
          onDragLeave={() => setIsHovering(false)}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-3xl p-16 flex flex-col items-center justify-center transition-all duration-300 mb-6 ${
            isHovering ? 'border-accent-primary bg-accent-primary/5 scale-[1.01]' : ' bg-surface/50'
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
                <button onClick={() => setFile(null)} className="px-5 py-2 rounded-full text-text-secondary text-sm hover:bg-accent-primary/10 hover:text-accent-primary transition-all">
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
              <span className="bg-surface  text-[10px] px-2 py-0.5 rounded-lg text-text-muted">
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
              {(result.experience ?? []).map((item: ExperienceItem, i: number) => (
                <ExperienceCard 
                  key={`exp-${i}`} 
                  item={item} 
                  title="Experience" 
                  onUpdateEntity={(entIdx, ent) => updateEntity('experience', i, entIdx, ent)}
                  onDeleteEntity={(entIdx) => deleteEntity('experience', i, entIdx)}
                  onAddEntity={() => addEntity('experience', i)}
                />
              ))}
              {(result.projects ?? []).map((item: ExperienceItem, i: number) => (
                <ExperienceCard 
                  key={`proj-${i}`} 
                  item={item} 
                  title="Project" 
                  onUpdateEntity={(entIdx, ent) => updateEntity('projects', i, entIdx, ent)}
                  onDeleteEntity={(entIdx) => deleteEntity('projects', i, entIdx)}
                  onAddEntity={() => addEntity('projects', i)}
                />
              ))}
              {(result.education ?? []).map((item: ExperienceItem, i: number) => (
                <ExperienceCard 
                  key={`edu-${i}`} 
                  item={item} 
                  title="Education" 
                  onUpdateEntity={(entIdx, ent) => updateEntity('education', i, entIdx, ent)}
                  onDeleteEntity={(entIdx) => deleteEntity('education', i, entIdx)}
                  onAddEntity={() => addEntity('education', i)}
                />
              ))}
              {(result.certifications as ExperienceItem[] ?? []).map((item: ExperienceItem, i: number) => (
                <ExperienceCard 
                  key={`cert-${i}`} 
                  item={item} 
                  title="Certification" 
                  onUpdateEntity={(entIdx, ent) => updateEntity('certifications', i, entIdx, ent)}
                  onDeleteEntity={(entIdx) => deleteEntity('certifications', i, entIdx)}
                  onAddEntity={() => addEntity('certifications', i)}
                />
              ))}
              {totalExperience === 0 && (result.education ?? []).length === 0 && (result.certifications ?? []).length === 0 && (
                <div className="p-12 text-center border border-dashed  rounded-3xl text-text-muted">
                  No structured items found. Try another CV with a standard layout.
                </div>
              )}
            </div>
          </div>

          {/* Sidebar: Skills & Metadata */}
          <div className="space-y-8">
            {/* Categorized Skills */}
            <div className="bg-surface/50  rounded-3xl p-6">
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
                        <span key={i} className="px-2.5 py-1 rounded-lg bg-surface  text-xs font-medium text-text-secondary">
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
            <div className="p-6 rounded-3xl bg-overlay/30  shadow-sm">
              <p className="text-[10px] font-black text-text-muted uppercase mb-4 tracking-[0.2em] opacity-80">Parsing Intelligence</p>
              <div className="space-y-4">
                <div className="flex justify-between items-center text-sm group">
                  <span className="text-text-secondary flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-emerald-500/50" /> Status
                  </span>
                  <span className="text-emerald-400 font-bold">
                    {result.status || 'Success'}
                  </span>
                </div>
                
                {result.metadata && (
                  <>
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-text-secondary flex items-center gap-2">
                        <Brain className="w-4 h-4 text-violet-400/50" /> Language
                      </span>
                      <span className="text-text-primary font-bold uppercase tracking-widest bg-surface/50 px-2 py-0.5 rounded ">
                        {result.metadata.language}
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-text-secondary flex items-center gap-2">
                        <FileText className="w-4 h-4 text-sky-400/50" /> Pages
                      </span>
                      <span className="text-text-primary font-medium">{result.metadata.pages}</span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-text-secondary flex items-center gap-2">
                        <Hash className="w-4 h-4 text-amber-400/50" /> Time
                      </span>
                      <span className="text-text-primary font-medium">{result.metadata.parse_time_ms}ms</span>
                    </div>
                  </>
                )}

                {result.languages && result.languages.length > 0 && (
                  <div className="pt-4 border-t ">
                    <p className="text-[10px] font-black text-text-muted uppercase mb-2 tracking-[0.2em] opacity-60">Human Languages</p>
                    <div className="flex flex-wrap gap-2">
                      {result.languages.map((lang: string, idx: number) => (
                        <span key={idx} className="px-2 py-1 bg-surface/80 rounded  text-[10px] font-bold text-text-secondary">
                          {lang}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                  <div className="pt-4 mt-2 flex flex-col gap-2">
                    <button 
                      onClick={handleSaveToMyCvs}
                      disabled={isSaving || saveSuccess}
                      className={cn(
                        "w-full flex items-center justify-center gap-2 py-3 rounded-xl font-bold transition-all shadow-lg",
                        saveSuccess 
                          ? "bg-emerald-500 text-white shadow-emerald-500/20" 
                          : "bg-accent-primary text-white hover:shadow-accent-primary/30 active:scale-95 disabled:opacity-50"
                      )}
                    >
                      {isSaving ? (
                        <><Loader2 className="w-4 h-4 animate-spin" /> Saving...</>
                      ) : saveSuccess ? (
                        <><Check className="w-4 h-4" /> Saved Successfully!</>
                      ) : (
                        <><Plus className="w-4 h-4" /> Save to My CVs</>
                      )}
                    </button>

                    <div className="grid grid-cols-2 gap-2">
                      <button 
                        onClick={() => setShowPreview(!showPreview)}
                        className={`flex items-center justify-center gap-2 py-2.5 rounded-xl border text-xs font-bold transition-all ${
                          showPreview ? 'bg-accent-primary border-accent-primary text-white' : 'bg-surface text-text-primary hover:bg-surface-hover hover:text-accent-primary'
                        }`}
                      >
                        <FileText className="w-4 h-4" /> {showPreview ? 'Hide PDF' : 'Show PDF'}
                      </button>
                      <button 
                        onClick={() => setShowSummary(!showSummary)}
                        className="flex items-center justify-center gap-2 py-2.5 rounded-xl bg-surface text-xs font-bold text-text-primary hover:bg-surface-hover hover:text-accent-primary transition-all"
                      >
                        <Eye className="w-4 h-4" /> {showSummary ? 'Raw Text' : 'View Text'}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* PDF Preview Modal/Panel */}
              {showPreview && previewUrl && (
                <div className="fixed inset-0 bg-canvas/80 backdrop-blur-md z-50 flex items-center justify-center p-8 animate-in fade-in duration-300">
                  <div className="bg-surface  rounded-3xl w-full max-w-5xl h-[90vh] flex flex-col shadow-2xl overflow-hidden">
                    <div className="p-4 border-b  flex justify-between items-center bg-overlay/5">
                      <div className="flex items-center gap-3">
                        <FileText className="w-5 h-5 text-accent-primary" />
                        <span className="font-bold text-sm">{file?.name}</span>
                      </div>
                      <button onClick={() => setShowPreview(false)} className="p-2 hover:bg-accent-primary/10 hover:text-accent-primary rounded-full transition-colors text-text-muted">
                        ✕
                      </button>
                    </div>
                    <iframe 
                      src={previewUrl} 
                      className="w-full h-full border-none"
                      title="CV Preview"
                    />
                  </div>
                </div>
              )}

              {/* Raw Text Preview Overlay */}
              {showSummary && (
                <div className="fixed inset-0 bg-canvas/80 backdrop-blur-md z-50 flex items-center justify-center p-8 animate-in fade-in duration-300">
                  <div className="bg-surface  rounded-3xl w-full max-w-4xl max-h-[80vh] flex flex-col shadow-2xl overflow-hidden">
                    <div className="p-6 border-b  flex justify-between items-center bg-overlay/5">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-accent-primary/10 flex items-center justify-center">
                          <FileText className="w-5 h-5 text-accent-primary" />
                        </div>
                        <h4 className="font-bold text-text-primary">Raw Extracted Content</h4>
                      </div>
                      <button onClick={() => setShowSummary(false)} className="p-2 hover:bg-accent-primary/10 hover:text-accent-primary rounded-full transition-colors text-text-muted">
                        ✕
                      </button>
                    </div>
                    <div className="p-8 overflow-y-auto font-mono text-[11px] leading-relaxed text-text-secondary whitespace-pre-wrap bg-canvas/50">
                      {result.raw_text}
                    </div>
                  </div>
                </div>
              )}
            </div>
        </div>
      )}
    </div>
  );
}
