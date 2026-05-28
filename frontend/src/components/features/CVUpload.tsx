import React, { useEffect, useState, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { UploadCloud, CheckCircle, Loader2, Brain, FileText, Hash, Eye, Edit2, Trash2, Check, X, Plus, Building, Calendar, Briefcase, MapPin, GraduationCap, Link2, Globe, Mail, Phone, ChevronDown, ChevronRight, ScanLine, ArrowLeft } from 'lucide-react';
import { nerApi, cvDocumentApi, ParseResult, Entity, ExperienceItem, CVData, CvDocument } from '../../services/api';
import { cn } from '../../lib/utils';

import { ExperienceCard } from './cv-upload/ExperienceCard';
import { PersonalInfoSection } from './cv-upload/PersonalInfoSection';
import { SkillsSection } from './cv-upload/SkillsSection';
import { LanguagesSection } from './cv-upload/LanguagesSection';
type Status = 'idle' | 'parsing' | 'done' | 'error';
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

  const toBullets = (desc: string | string[] | undefined): string[] => {
    if (!desc) return [];
    if (Array.isArray(desc)) return desc.map(s => s.trim()).filter(Boolean);
    return desc.split('\n').map(line => line.trim().replace(/^[-•*◦]\s*/, '')).filter(Boolean);
  };

  const parseDates = (dates: string[]): { start_date: string; end_date: string } => {
    if (dates.length >= 2) return { start_date: dates[0], end_date: dates[1] };
    if (dates.length === 1) return { start_date: dates[0], end_date: '' };
    return { start_date: '', end_date: '' };
  };

  return {
    personal_info: {
      full_name: result.personal_info?.full_name || names[0] || '',
      email: result.personal_info?.email || '',
      phone: result.personal_info?.phone || '',
      location: result.personal_info?.location || locs[0] || '',
      title: result.personal_info?.title || jobTitles[0] || '',
      linkedin: result.personal_info?.linkedin || '',
      github: result.personal_info?.github || '',
      youtube: result.personal_info?.youtube || '',
    },
    education: (result.education || []).map((item) => {
      const dates = parseDates(pickEntities([item], 'DATE'));
      return {
        school: pickEntities([item], 'ORG')[0] || item.anchor || '',
        degree: pickEntities([item], 'DEGREE')[0] || '',
        major: pickEntities([item], 'MAJOR')[0] || '',
        start_date: dates.start_date,
        end_date: dates.end_date,
        gpa: null,
      };
    }),
    experience: (result.experience || []).map((item) => {
      const dates = parseDates(pickEntities([item], 'DATE'));
      return {
        company: pickEntities([item], 'ORG')[0] || orgs[0] || '',
        position: pickEntities([item], 'JOB_TITLE')[0] || item.anchor || '',
        location: pickEntities([item], 'LOC')[0] || '',
        start_date: dates.start_date,
        end_date: dates.end_date,
        description: toBullets(item.description),
      };
    }),
    skills,
    projects: (result.projects || []).map((item) => ({
      name: item.anchor || '',
      description: toBullets(item.description),
      technologies: pickEntities([item], 'SKILL'),
      link: null,
    })),
    certifications: (result.certifications || []).map((item) => ({
      name: item.anchor || '',
      organization: pickEntities([item], 'ORG')[0] || '',
      issue_date: pickEntities([item], 'DATE')[0] || '',
      expiry_date: null,
    })),
    languages: (result.languages || []).map((lang: any) => {
      if (typeof lang === 'string') {
        return { name: lang, description: '' };
      }
      return lang;
    }),
  };
};


// Helper to map parsing status and color entities
const getEntityColor = (type: string) => {
  switch (type) {
    case 'PER': return 'bg-rose-500/20 text-rose-400';
    case 'ORG': return 'bg-emerald-500/20 text-emerald-400';
    case 'SKILL': return 'bg-amber-500/20 text-amber-400';
    case 'ROLE': return 'bg-purple-500/20 text-purple-400';
    case 'LOC': return 'bg-cyan-500/20 text-cyan-400';
    default: return 'bg-accent-primary/20 text-accent-primary';
  }
};

const renderHighlightedRawText = (text: string, groupedEntities?: Record<string, string[]>) => {
  if (!groupedEntities) return text;
  
  const entityMap = new Map<string, string>();
  Object.entries(groupedEntities).forEach(([type, words]) => {
      words.forEach(w => {
          if (w.trim().length > 2) entityMap.set(w.trim().toLowerCase(), type);
      });
  });

  if (entityMap.size === 0) return text;

  const sortedWords = Array.from(entityMap.keys()).sort((a, b) => b.length - a.length);
  const escapedWords = sortedWords.map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  const regex = new RegExp(`(${escapedWords.join('|')})`, 'gi');

  const parts = text.split(regex);
  
  return parts.map((part, i) => {
      const type = entityMap.get(part.toLowerCase());
      if (!type) return <span key={i}>{part}</span>;
      const colorClass = getEntityColor(type);
      return (
          <mark key={i} className={`px-1 rounded ${colorClass} font-bold inline-block relative group`} style={{ backgroundColor: 'transparent' }}>
              <span className={colorClass + " px-1 py-0.5 rounded"}>{part}</span>
              <span className="absolute -top-4 left-0 text-[9px] bg-black/90 text-white px-1.5 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none whitespace-nowrap">
                  {type}
              </span>
          </mark>
      );
  });
};

type SectionKey = 'experience' | 'projects' | 'education' | 'certifications';

export default function CVUpload({ onParsedCvData }: CVUploadProps) {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const docIdParam = searchParams.get('docId');
  const [collapsedSections, setCollapsedSections] = useState<Record<SectionKey, boolean>>({
    experience: false,
    projects: false,
    education: false,
    certifications: false
  });
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
  const [isInitializingDoc, setIsInitializingDoc] = useState(!!docIdParam);
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
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
      return parsed;
    } catch {
      // Keep silent; upload flow still works without history
      return [];
    } finally {
      setIsLoadingSaved(false);
    }
  };

  useEffect(() => {
    if (!docIdParam) {
      loadSavedParses();
      return;
    }
    
    setIsInitializingDoc(true);
    loadSavedParses().then((savedList) => {
      const id = parseInt(docIdParam);
      const found = savedList.find(d => d.docId === id);
      if (found) {
        handleLoadSavedParse(found).finally(() => setIsInitializingDoc(false));
      } else {
        cvDocumentApi.getById(id).then(async docRes => {
          const latest = docRes.data.versions.slice().sort((a, b) => b.versionNumber - a.versionNumber)[0];
          if (latest) {
             await handleLoadSavedParse({ docId: docRes.data.id, name: docRes.data.name, updatedAt: docRes.data.updatedAt, latestVersionId: latest.id });
          }
        }).catch(e => {
            console.error(e);
            setStatus('error');
            setErrorMsg('Không tìm thấy CV này.');
        }).finally(() => setIsInitializingDoc(false));
      }
    });
  }, [docIdParam]);

  const handleDeleteCv = async () => {
    if (!docIdParam || !confirm('Bạn có chắc chắn muốn xóa CV này? Hành động này không thể hoàn tác.')) return;
    try {
        await cvDocumentApi.delete(parseInt(docIdParam));
        navigate('/cv-health');
    } catch (e) {
        alert('Lỗi khi xóa CV');
    }
  };

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
      const parsedData = res.data;
      if (!parsedData.personal_info) {
        parsedData.personal_info = mapParseResultToCvData(parsedData).personal_info;
      }
      setResult(parsedData);
      onParsedCvData?.(mapParseResultToCvData(parsedData));
      // Human-in-the-loop: Do NOT auto-save. Require user review.
      // try {
      //   await autoSaveParsedResult(file.name, res.data);
      //   await loadSavedParses();
      // } catch {
      //   // Non-blocking
      // }
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
    if (!result) return;
    setIsSaving(true);
    try {
      if (docIdParam) {
        // Edit mode: save a new version of the existing CV
        await cvDocumentApi.createVersion(parseInt(docIdParam), {
          dataJson: JSON.stringify(result),
          note: 'Updated from CV Reviewer'
        });
      } else {
        // Upload mode: create a new CV document
        if (!file) return;
        await cvDocumentApi.create({
          name: buildParsedDocName(file.name),
          dataJson: JSON.stringify(result),
          note: 'Imported from AI Parser'
        });
      }
      await loadSavedParses();
      setSaveSuccess(true);
    } catch (e) {
      setErrorMsg(docIdParam ? 'Không thể cập nhật phiên bản CV' : 'Failed to save document to My CVs');
    } finally {
      setIsSaving(false);
    }
  };

  const handleViewPdf = async () => {
    if (previewUrl) {
      setShowPreview(true);
      return;
    }
    if (!result) return;
    setIsGeneratingPdf(true);
    try {
      const pdfPayload = {
        name: result.personal_info?.full_name || "",
        email: result.personal_info?.email || "",
        phone: result.personal_info?.phone || "",
        location: result.personal_info?.location || "",
        linkedin: result.personal_info?.linkedin || "",
        linkedin_title: result.personal_info?.linkedin_title || "",
        github: result.personal_info?.github || "",
        github_title: result.personal_info?.github_title || "",
        youtube: result.personal_info?.youtube || "",
        youtube_title: result.personal_info?.youtube_title || "",
        summary: result.summary || "",
        experience: result.experience || [],
        projects: result.projects || [],
        education: result.education || [],
        skills: result.skills || {},
        certifications: result.certifications || [],
        languages: result.languages || []
      };
      const res = await nerApi.generatePdf(pdfPayload);
      const blob = new Blob([res.data], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      setPreviewUrl(url);
      setShowPreview(true);
    } catch (e) {
      alert("Không thể tạo bản xem trước PDF từ dữ liệu CV này. Vui lòng kiểm tra lại thông tin.");
    } finally {
      setIsGeneratingPdf(false);
    }
  };

  // --- Entity Management (Task T10) ---

  const handleUpdateItem = (section: SectionKey, blockIdx: number, newItem: ExperienceItem) => {
    if (!result || !result[section]) return;
    const newList = [...result[section]];
    newList[blockIdx] = newItem;
    const newResult = { ...result, [section]: newList };
    setResult(newResult);
    onParsedCvData?.(mapParseResultToCvData(newResult));
  };

  const [isEditingSummary, setIsEditingSummary] = useState(false);
  const [editSummary, setEditSummary] = useState('');
  const summaryRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (result) setEditSummary(result.summary || '');
  }, [result?.summary]);

  useEffect(() => {
    if (isEditingSummary && summaryRef.current) {
      summaryRef.current.style.height = 'auto';
      summaryRef.current.style.height = summaryRef.current.scrollHeight + 'px';
    }
  }, [isEditingSummary, editSummary]);

  const handleSaveSummary = () => {
    if (!result) return;
    setResult({ ...result, summary: editSummary });
    setIsEditingSummary(false);
  };

  const addBlock = (section: SectionKey) => {
    if (!result) return;
    const newResult = { ...result };
    if (!newResult[section]) {
      (newResult[section] as any) = [];
    }
    (newResult[section] as ExperienceItem[]).unshift({
      anchor: '',
      description: '',
      entities: []
    });
    setResult(newResult);
  };

  const deleteBlock = (section: SectionKey, blockIdx: number) => {
    if (!result) return;
    const newResult = { ...result };
    if (newResult[section]) {
      (newResult[section] as ExperienceItem[]).splice(blockIdx, 1);
      setResult(newResult);
    }
  };

  const handleUpdatePersonalInfo = (newInfo: any) => {
    if (!result) return;
    const newResult = { ...result, personal_info: newInfo };
    setResult(newResult);
    onParsedCvData?.(mapParseResultToCvData(newResult));
  };

  const handleUpdateSkills = (newSkills: Record<string, string[]>) => {
    if (!result) return;
    const newResult = { ...result, skills: newSkills };
    setResult(newResult);
    onParsedCvData?.(mapParseResultToCvData(newResult));
  };

  const handleUpdateLanguages = (newLanguages: any[]) => {
    if (!result) return;
    const newResult = { ...result, languages: newLanguages };
    setResult(newResult);
    onParsedCvData?.(mapParseResultToCvData(newResult));
  };

  const totalBlocks = (result?.experience?.length || 0) + (result?.projects?.length || 0) + (result?.education?.length || 0) + (result?.certifications?.length || 0);

  const handleLoadSavedParse = async (doc: SavedParsedCv) => {
    setLoadingDocId(doc.docId);
    setErrorMsg('');
    try {
      const detail = await cvDocumentApi.getVersion(doc.docId, doc.latestVersionId);
      const parsed = JSON.parse(detail.data.dataJson);
      if (!isParseResultLike(parsed)) {
        throw new Error('Selected document is not a parsed CV result.');
      }
      if (!parsed.personal_info) {
        parsed.personal_info = mapParseResultToCvData(parsed).personal_info;
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
    <div className="max-w-7xl mx-auto p-6 pt-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 gap-4">
        <div>
            <button onClick={() => navigate('/cv-health')} className="flex items-center gap-1.5 text-text-muted hover:text-text-primary transition-colors text-sm font-semibold mb-3">
                <ArrowLeft className="w-4 h-4" /> Quay lại Health Dashboard
            </button>
            <h1 className="text-3xl font-black font-outfit tracking-tight mb-1">
                {docIdParam ? 'Xem / Sửa CV' : 'Upload & Review CV'}
            </h1>
            <p className="text-text-secondary text-sm">
                {docIdParam ? 'Chỉnh sửa trực tiếp dữ liệu CV đã lưu của bạn.' : 'Review AI extracted entities before saving to My CVs.'}
            </p>
        </div>
        <div className="flex items-center gap-3">
            {docIdParam && (
                <button onClick={handleDeleteCv} className="px-5 py-2.5 rounded-full bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 text-sm font-bold transition-all shadow-sm flex items-center gap-2">
                    <Trash2 className="w-4 h-4" /> Xóa CV
                </button>
            )}
            {status === 'done' && !docIdParam && (
              <button onClick={handleReset} className="px-6 py-2.5 rounded-full bg-surface hover:bg-surface-hover border border-white/10 text-sm font-bold transition-all shadow-sm">
                Upload New
              </button>
            )}
        </div>
      </div>

      {isInitializingDoc ? (
        <div className="flex flex-col items-center justify-center min-h-[40vh] border border-white/5 bg-surface/30 rounded-3xl">
            <Loader2 className="w-10 h-10 text-accent-primary animate-spin mb-4" />
            <p className="text-text-secondary text-sm font-semibold">Đang tải dữ liệu CV...</p>
        </div>
      ) : (
        <>
          {/* Saved Parse History */}
      {status !== 'done' && (
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
      )}

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
                  className="px-8 py-2 rounded-full bg-accent-primary text-white font-bold text-sm hover:shadow-[0_0_20px_rgba(37,99,235,0.4)] transition-all flex items-center gap-2 disabled:opacity-60 overflow-hidden relative"
                >
                  {status === 'parsing' ? (
                    <>
                      <div className="absolute inset-0 bg-white/20 animate-pulse" />
                      <ScanLine className="w-4 h-4 animate-bounce relative z-10" /> 
                      <span className="relative z-10">Structuring...</span>
                    </>
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
        <div className="w-full animate-in zoom-in-95 duration-500 pb-12">
          
          {/* Header & Actions */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
            <h3 className="text-xl font-bold flex items-center gap-3">
              <FileText className="w-5 h-5 text-accent-primary" /> 
              Professional Background
              <span className="bg-surface text-[10px] px-2 py-0.5 rounded-lg text-text-muted">
                {totalBlocks} Blocks
              </span>
            </h3>

            <div className="flex items-center gap-3">
              <button 
                onClick={handleViewPdf} 
                disabled={isGeneratingPdf}
                className="px-4 py-2 rounded-xl text-sm font-bold bg-surface hover:bg-surface-hover text-text-primary transition-colors flex items-center gap-2 border border-white/5 disabled:opacity-50"
              >
                {isGeneratingPdf ? (
                  <><Loader2 className="w-4 h-4 animate-spin text-accent-primary" /> Generating...</>
                ) : (
                  <><Eye className="w-4 h-4" /> View PDF</>
                )}
              </button>
              <button 
                onClick={handleSaveToMyCvs}
                disabled={isSaving || saveSuccess}
                className={cn(
                  "px-6 py-2 rounded-xl text-sm font-bold transition-all duration-300 flex items-center gap-2",
                  saveSuccess 
                    ? "bg-emerald-500 text-white shadow-[0_0_20px_rgba(16,185,129,0.4)]" 
                    : "bg-gradient-to-r from-accent-primary to-accent-secondary text-white hover:shadow-[0_0_20px_rgba(37,99,235,0.4)] hover:scale-[1.02] active:scale-95 disabled:opacity-50 disabled:hover:scale-100 disabled:hover:shadow-none"
                )}
              >
                {isSaving ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> Saving...</>
                ) : saveSuccess ? (
                  <><Check className="w-4 h-4" /> Saved!</>
                ) : (
                  <>{docIdParam ? <><Check className="w-4 h-4" /> Cập nhật CV</> : <><Plus className="w-4 h-4" /> Save to My CVs</>}</>
                )}
              </button>
              {saveSuccess && (
                <button
                  onClick={() => navigate('/cv-health')}
                  className="px-6 py-2 rounded-xl text-sm font-bold bg-indigo-500 text-white shadow-[0_0_20px_rgba(99,102,241,0.4)] hover:scale-[1.02] active:scale-95 transition-all duration-300 flex items-center gap-2 animate-in slide-in-from-right-4"
                >
                  👉 Phân tích sức khỏe CV này ngay
                </button>
              )}
            </div>
          </div>

          <div className="space-y-6">

            <PersonalInfoSection 
              info={result.personal_info || mapParseResultToCvData(result).personal_info} 
              onChange={handleUpdatePersonalInfo} 
            />

            {result.summary !== undefined && (
              <div className="mb-8">
                <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2">
                  <h4 className="font-bold text-text-primary uppercase tracking-wider text-sm">Professional Summary</h4>
                  {!isEditingSummary && (
                    <button onClick={() => setIsEditingSummary(true)} className="text-xs font-bold bg-surface hover:bg-surface-hover px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1 text-accent-primary">
                      <Edit2 className="w-3 h-3" /> Edit
                    </button>
                  )}
                </div>
                <div className="bg-surface/60 border border-white/5 shadow-xl shadow-black/10 rounded-2xl p-6 hover:bg-surface/80 hover:border-accent-primary/20 transition-all duration-300 relative group overflow-hidden">
                  <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none group-hover:opacity-10 transition-opacity">
                    <Brain className="w-12 h-12 text-accent-primary" />
                  </div>
                  {isEditingSummary ? (
                    <div className="space-y-4">
                      <textarea
                        ref={summaryRef}
                        value={editSummary}
                        onChange={(e) => setEditSummary(e.target.value)}
                        autoFocus
                        className="w-full text-sm bg-black/20 border border-accent-primary/50 rounded-lg p-3 min-h-[100px] outline-none leading-relaxed text-text-secondary resize-none shadow-inner transition-colors focus:border-accent-primary focus:bg-black/40 overflow-hidden relative z-10"
                        placeholder="Tóm tắt bản thân..."
                      />
                      <div className="flex justify-end gap-2 relative z-10">
                        <button onClick={() => { setIsEditingSummary(false); setEditSummary(result.summary); }} className="px-4 py-1.5 rounded-lg text-sm bg-surface hover:bg-surface-hover text-text-primary transition-colors">Cancel</button>
                        <button onClick={handleSaveSummary} className="px-4 py-1.5 rounded-lg text-sm bg-accent-primary text-white font-bold hover:shadow-[0_0_15px_rgba(37,99,235,0.3)] transition-all">Save</button>
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-text-secondary leading-relaxed p-2 -ml-2 rounded-lg relative z-10">
                      {result.summary || <span className="italic opacity-50">No summary added. Click Edit to add.</span>}
                    </p>
                  )}
                </div>
              </div>
            )}

            <SkillsSection 
              skills={result.skills || {}} 
              onChange={handleUpdateSkills} 
            />

            <LanguagesSection 
              languages={result.languages || []} 
              onChange={handleUpdateLanguages} 
            />

            {/* Experience Section */}
            <div className="mb-8 bg-surface/30 rounded-2xl p-4 border border-white/5 transition-all duration-300">
              <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2 cursor-pointer group" onClick={() => setCollapsedSections(prev => ({ ...prev, experience: !prev.experience }))}>
                <div className="flex items-center gap-2">
                  {collapsedSections.experience ? <ChevronRight className="w-4 h-4 text-text-muted group-hover:text-text-primary" /> : <ChevronDown className="w-4 h-4 text-text-muted group-hover:text-text-primary" />}
                  <h4 className="font-bold text-text-primary uppercase tracking-wider text-sm flex items-center gap-2">Experience <span className="bg-white/10 px-2 py-0.5 rounded-full text-xs">{result.experience?.length || 0}</span></h4>
                </div>
                <button onClick={(e) => { e.stopPropagation(); addBlock('experience'); }} className="text-xs font-bold bg-surface hover:bg-surface-hover px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1 text-accent-primary">
                  <Plus className="w-3 h-3" /> Thêm Experience
                </button>
              </div>
              {!collapsedSections.experience && (
                <div className="space-y-4 animate-in slide-in-from-top-2 fade-in duration-300">
                  {(result.experience ?? []).length === 0 && <p className="text-text-muted text-sm italic py-4">No experience added.</p>}
                  {(result.experience ?? []).map((item: ExperienceItem, i: number) => (
                    <ExperienceCard 
                      key={`exp-${i}`} 
                      item={item} 
                      title="Experience" 
                      onUpdate={(newItem) => handleUpdateItem('experience', i, newItem)}
                      onDelete={() => deleteBlock('experience', i)}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Projects Section */}
            <div className="mb-8 bg-surface/30 rounded-2xl p-4 border border-white/5 transition-all duration-300">
              <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2 cursor-pointer group" onClick={() => setCollapsedSections(prev => ({ ...prev, projects: !prev.projects }))}>
                <div className="flex items-center gap-2">
                  {collapsedSections.projects ? <ChevronRight className="w-4 h-4 text-text-muted group-hover:text-text-primary" /> : <ChevronDown className="w-4 h-4 text-text-muted group-hover:text-text-primary" />}
                  <h4 className="font-bold text-text-primary uppercase tracking-wider text-sm flex items-center gap-2">Projects <span className="bg-white/10 px-2 py-0.5 rounded-full text-xs">{result.projects?.length || 0}</span></h4>
                </div>
                <button onClick={(e) => { e.stopPropagation(); addBlock('projects'); }} className="text-xs font-bold bg-surface hover:bg-surface-hover px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1 text-accent-primary">
                  <Plus className="w-3 h-3" /> Thêm Project
                </button>
              </div>
              {!collapsedSections.projects && (
                <div className="space-y-4 animate-in slide-in-from-top-2 fade-in duration-300">
                  {(result.projects ?? []).length === 0 && <p className="text-text-muted text-sm italic py-4">No projects added.</p>}
                  {(result.projects ?? []).map((item: ExperienceItem, i: number) => (
                    <ExperienceCard 
                      key={`proj-${i}`} 
                      item={item} 
                      title="Project" 
                      onUpdate={(newItem) => handleUpdateItem('projects', i, newItem)}
                      onDelete={() => deleteBlock('projects', i)}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Education Section */}
            <div className="mb-8 bg-surface/30 rounded-2xl p-4 border border-white/5 transition-all duration-300">
              <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2 cursor-pointer group" onClick={() => setCollapsedSections(prev => ({ ...prev, education: !prev.education }))}>
                <div className="flex items-center gap-2">
                  {collapsedSections.education ? <ChevronRight className="w-4 h-4 text-text-muted group-hover:text-text-primary" /> : <ChevronDown className="w-4 h-4 text-text-muted group-hover:text-text-primary" />}
                  <h4 className="font-bold text-text-primary uppercase tracking-wider text-sm flex items-center gap-2">Education <span className="bg-white/10 px-2 py-0.5 rounded-full text-xs">{result.education?.length || 0}</span></h4>
                </div>
                <button onClick={(e) => { e.stopPropagation(); addBlock('education'); }} className="text-xs font-bold bg-surface hover:bg-surface-hover px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1 text-accent-primary">
                  <Plus className="w-3 h-3" /> Thêm Education
                </button>
              </div>
              {!collapsedSections.education && (
                <div className="space-y-4 animate-in slide-in-from-top-2 fade-in duration-300">
                  {(result.education ?? []).length === 0 && <p className="text-text-muted text-sm italic py-4">No education added.</p>}
                  {(result.education ?? []).map((item: ExperienceItem, i: number) => (
                    <ExperienceCard 
                      key={`edu-${i}`} 
                      item={item} 
                      title="Education" 
                      onUpdate={(newItem) => handleUpdateItem('education', i, newItem)}
                      onDelete={() => deleteBlock('education', i)}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Certifications Section */}
            <div className="mb-8 bg-surface/30 rounded-2xl p-4 border border-white/5 transition-all duration-300">
              <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2 cursor-pointer group" onClick={() => setCollapsedSections(prev => ({ ...prev, certifications: !prev.certifications }))}>
                <div className="flex items-center gap-2">
                  {collapsedSections.certifications ? <ChevronRight className="w-4 h-4 text-text-muted group-hover:text-text-primary" /> : <ChevronDown className="w-4 h-4 text-text-muted group-hover:text-text-primary" />}
                  <h4 className="font-bold text-text-primary uppercase tracking-wider text-sm flex items-center gap-2">Certifications <span className="bg-white/10 px-2 py-0.5 rounded-full text-xs">{result.certifications?.length || 0}</span></h4>
                </div>
                <button onClick={(e) => { e.stopPropagation(); addBlock('certifications'); }} className="text-xs font-bold bg-surface hover:bg-surface-hover px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1 text-accent-primary">
                  <Plus className="w-3 h-3" /> Thêm Certification
                </button>
              </div>
              {!collapsedSections.certifications && (
                <div className="space-y-4 animate-in slide-in-from-top-2 fade-in duration-300">
                  {(result.certifications ?? []).length === 0 && <p className="text-text-muted text-sm italic py-4">No certifications added.</p>}
                  {(result.certifications as ExperienceItem[] ?? []).map((item: ExperienceItem, i: number) => (
                    <ExperienceCard 
                      key={`cert-${i}`} 
                      item={item} 
                      title="Certification" 
                      onUpdate={(newItem) => handleUpdateItem('certifications', i, newItem)}
                      onDelete={() => deleteBlock('certifications', i)}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>

              {/* PDF Preview Modal/Panel */}
              {showPreview && previewUrl && (
                <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-6 lg:p-12 animate-in fade-in duration-300">
                  <div className="bg-surface rounded-2xl w-full max-w-4xl h-[85vh] flex flex-col shadow-2xl overflow-hidden border border-white/10">
                    <div className="p-4 border-b  flex justify-between items-center bg-overlay/5">
                      <div className="flex items-center gap-3">
                        <FileText className="w-5 h-5 text-accent-primary" />
                        <span className="font-bold text-sm">{file?.name || result?.personal_info?.fullName || 'CV Preview'}</span>
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
                <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-6 lg:p-12 animate-in fade-in duration-300">
                  <div className="bg-surface rounded-2xl w-full max-w-4xl h-[85vh] flex flex-col shadow-2xl overflow-hidden border border-white/10">
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
                      {renderHighlightedRawText(result.raw_text, result.grouped_entities)}
                    </div>
                  </div>
                </div>
              )}

        </div>
      )}
      </>
      )}
    </div>
  );
}
