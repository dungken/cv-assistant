import React, { useEffect, useState, useRef } from 'react';
import { UploadCloud, CheckCircle, Loader2, Brain, FileText, Hash, Eye, Edit2, Trash2, Check, X, Plus, Building, Calendar, Briefcase, MapPin, GraduationCap, Link2, Globe, Mail, Phone } from 'lucide-react';
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
  LINK:      { bg: 'bg-indigo-500/10', text: 'text-indigo-400', border: 'border-indigo-500/30' },
};

const ENTITY_TYPES = Object.keys(LABEL_COLORS);

const SECTION_ENTITY_MAP: Record<string, string[]> = {
  'Experience': ['DATE', 'JOB_TITLE', 'ORG', 'LOC', 'SKILL', 'LINK', 'PER'],
  'Project': ['DATE', 'JOB_TITLE', 'ORG', 'PROJECT', 'SKILL', 'LINK', 'PER'],
  'Education': ['DATE', 'DEGREE', 'MAJOR', 'ORG', 'LOC', 'SKILL', 'LINK'],
  'Certification': ['DATE', 'CERT', 'ORG', 'SKILL', 'LINK'],
};

const DEFAULT_COLOR = { bg: 'bg-gray-500/10', text: 'text-gray-400', border: 'border-gray-500/30' };

type Status = 'idle' | 'parsing' | 'done' | 'error';

function ExperienceCard({ 
  item, 
  title, 
  onUpdate,
  onDelete
}: { 
  item: ExperienceItem; 
  title: string;
  onUpdate: (updatedItem: ExperienceItem) => void;
  onDelete?: () => void;
}) {
  const [isEditing, setIsEditing] = useState(false);
  
  // Form states
  const [editAnchor, setEditAnchor] = useState(item.anchor || '');
  const [editDesc, setEditDesc] = useState(item.description || '');
  const [editSubtitle, setEditSubtitle] = useState('');
  const [editLocation, setEditLocation] = useState('');
  const [editDates, setEditDates] = useState('');
  const [editLinks, setEditLinks] = useState('');
  const [editStack, setEditStack] = useState('');

  useEffect(() => {
    if (isEditing) {
      setEditAnchor(item.anchor || '');
      setEditDesc(item.description || '');
      
      const entities = item.entities || [];
      const getTexts = (types: string[]) => entities.filter(e => types.includes(e.type)).map(e => e.text);
      
      setEditSubtitle(getTexts(['ORG', 'JOB_TITLE', 'DEGREE', 'MAJOR', 'CERT', 'PROJECT']).join(', '));
      setEditLocation(getTexts(['LOC']).join(', '));
      setEditDates(getTexts(['DATE']).join(' - '));
      setEditLinks(getTexts(['LINK']).join(', '));
      setEditStack(getTexts(['SKILL']).join(', '));
    }
  }, [isEditing, item]);

  const handleSave = () => {
    const newEntities: Entity[] = [];
    const addEnts = (textStr: string, type: string) => {
      if (!textStr) return;
      const parts = type === 'DATE' ? textStr.split('-') : textStr.split(',');
      parts.forEach(part => {
        const t = part.trim();
        if (t) newEntities.push({ text: t, type, start: 0, end: 0, confidence: 1 });
      });
    };

    const subtitleParts = editSubtitle.split(',').map(s => s.trim()).filter(Boolean);
    if (title === 'Experience' || title === 'Project') {
       if (subtitleParts.length > 0) newEntities.push({ text: subtitleParts[0], type: 'ORG', start: 0, end: 0, confidence: 1 });
       if (subtitleParts.length > 1) newEntities.push({ text: subtitleParts.slice(1).join(', '), type: 'JOB_TITLE', start: 0, end: 0, confidence: 1 });
    } else if (title === 'Education') {
       if (subtitleParts.length > 0) newEntities.push({ text: subtitleParts[0], type: 'ORG', start: 0, end: 0, confidence: 1 });
       if (subtitleParts.length > 1) newEntities.push({ text: subtitleParts.slice(1).join(', '), type: 'DEGREE', start: 0, end: 0, confidence: 1 });
    } else if (title === 'Certification') {
       if (subtitleParts.length > 0) newEntities.push({ text: subtitleParts[0], type: 'ORG', start: 0, end: 0, confidence: 1 });
       if (subtitleParts.length > 1) newEntities.push({ text: subtitleParts.slice(1).join(', '), type: 'CERT', start: 0, end: 0, confidence: 1 });
    } else {
       subtitleParts.forEach(p => newEntities.push({ text: p, type: 'ORG', start: 0, end: 0, confidence: 1 }));
    }

    addEnts(editLocation, 'LOC');
    addEnts(editDates, 'DATE');
    addEnts(editLinks, 'LINK');
    addEnts(editStack, 'SKILL');

    onUpdate({
      anchor: editAnchor,
      description: editDesc,
      entities: newEntities
    });
    setIsEditing(false);
  };

  if (isEditing) {
    return (
      <div className="bg-surface/60 border border-white/5 shadow-xl shadow-black/10 rounded-2xl p-6 relative mb-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Title / Anchor</label>
            <input type="text" value={editAnchor} onChange={e => setEditAnchor(e.target.value)} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" placeholder="e.g. Backend Developer" />
          </div>
          <div>
            <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Organization / Role</label>
            <input type="text" value={editSubtitle} onChange={e => setEditSubtitle(e.target.value)} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" placeholder="Comma separated..." />
          </div>
          <div>
            <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Dates</label>
            <input type="text" value={editDates} onChange={e => setEditDates(e.target.value)} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" placeholder="e.g. Jan 2026 - Jun 2026" />
          </div>
          <div>
            <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Location</label>
            <input type="text" value={editLocation} onChange={e => setEditLocation(e.target.value)} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" placeholder="e.g. Ho Chi Minh City" />
          </div>
          <div>
            <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Links</label>
            <input type="text" value={editLinks} onChange={e => setEditLinks(e.target.value)} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" placeholder="Comma separated URLs..." />
          </div>
          <div className="md:col-span-2">
            <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Stack / Skills</label>
            <input type="text" value={editStack} onChange={e => setEditStack(e.target.value)} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" placeholder="Comma separated skills..." />
          </div>
          <div className="md:col-span-2">
            <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Description</label>
            <textarea value={editDesc} onChange={e => setEditDesc(e.target.value)} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary resize-none min-h-[100px] font-mono text-[12px]" placeholder="Italic summary paragraph...&#10;- **Bullet Title:** Bullet details..." />
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-4">
          <button onClick={() => setIsEditing(false)} className="px-4 py-1.5 rounded-lg text-sm bg-surface hover:bg-surface-hover text-text-primary transition-colors">Cancel</button>
          <button onClick={handleSave} className="px-4 py-1.5 rounded-lg text-sm bg-accent-primary text-white font-bold hover:shadow-[0_0_15px_rgba(37,99,235,0.3)] transition-all">Save</button>
        </div>
      </div>
    );
  }

  // --- View Mode ---
  const entities = item.entities || [];
  const dateEntities = entities.filter(ent => ent.type === 'DATE');
  const linkEntities = entities.filter(ent => ent.type === 'LINK');
  const subtitleEntities = entities.filter(ent => ['ORG', 'JOB_TITLE', 'DEGREE', 'MAJOR', 'LOC', 'PER', 'CERT', 'PROJECT'].includes(ent.type));
  const tagEntities = entities.filter(ent => !['DATE', 'LINK', 'ORG', 'JOB_TITLE', 'DEGREE', 'MAJOR', 'LOC', 'PER', 'CERT', 'PROJECT'].includes(ent.type));

  const renderEntityText = (ent: any, isBold: boolean = false, customClasses?: string) => {
    const renderWithBold = (text: string) => {
      const parts = text.split(/(\*\*.*?\*\*)/g);
      return parts.map((part, idx) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={idx} className="font-bold text-text-primary">{part.slice(2, -2)}</strong>;
        }
        return <span key={idx}>{part}</span>;
      });
    };

    return (
      <span key={Math.random()} className={`${isBold ? 'font-bold' : ''} ${customClasses || 'text-text-primary'}`}>
        {renderWithBold(ent.text)}
      </span>
    );
  };

  return (
    <div className="bg-surface/60 border border-white/5 shadow-xl shadow-black/10 rounded-2xl p-6 hover:bg-surface/80 hover:border-accent-primary/20 transition-all duration-300 group mb-4">
      <div className="relative pr-16">
        {/* Action Buttons */}
        <div className="absolute right-0 top-0 opacity-0 group-hover:opacity-100 flex items-center gap-1 transition-opacity z-10">
          <button onClick={() => setIsEditing(true)} className="p-1.5 rounded-lg text-text-muted hover:text-accent-primary hover:bg-white/10 transition-colors" title="Edit Block">
            <Edit2 className="w-4 h-4" />
          </button>
          {onDelete && (
            <button onClick={() => { if (confirm('Bạn có chắc muốn xóa?')) onDelete(); }} className="p-1.5 rounded-lg text-text-muted hover:text-rose-500 hover:bg-rose-500/10 transition-colors" title="Delete Block">
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* ROW 1: Title & Date */}
        <div className="flex justify-between items-start mb-0.5 min-h-[24px]">
          <div className="text-[15px] font-bold text-accent-primary">
            {item.anchor || 'Untitled'}
          </div>
          <div className="text-[13px] text-text-secondary font-medium">
            {dateEntities.length > 0 ? dateEntities.map((ent, i) => (
              <React.Fragment key={i}>
                {renderEntityText(ent)}
                {i < dateEntities.length - 1 && ' - '}
              </React.Fragment>
            )) : <span className="text-text-muted italic text-[11px]">No Date</span>}
          </div>
        </div>

        {/* ROW 2: Subtitle & Links */}
        <div className="flex justify-between items-baseline mb-2">
          <div className="text-[13px] flex items-center flex-wrap">
            <span className="font-bold text-text-primary mr-2 flex items-center flex-wrap">
              {subtitleEntities.filter(e => ['ORG', 'JOB_TITLE', 'DEGREE'].includes(e.type)).length > 0 ? 
                subtitleEntities.filter(e => ['ORG', 'JOB_TITLE', 'DEGREE'].includes(e.type)).map((ent, i, arr) => (
                  <React.Fragment key={i}>
                    {renderEntityText(ent, true)}
                    {i < arr.length - 1 && ', '}
                  </React.Fragment>
                )) : null
              }
            </span>
            <span className="text-text-secondary flex items-center flex-wrap">
              {subtitleEntities.filter(e => !['ORG', 'JOB_TITLE', 'DEGREE'].includes(e.type)).length > 0 ? 
                subtitleEntities.filter(e => !['ORG', 'JOB_TITLE', 'DEGREE'].includes(e.type)).map((ent, i, arr) => (
                  <React.Fragment key={i}>
                    {renderEntityText(ent, false, 'text-text-secondary')}
                    {i < arr.length - 1 && ' · '}
                  </React.Fragment>
                )) : null
              }
            </span>
          </div>
          <div className="text-[12px] flex items-center flex-wrap gap-2">
            {linkEntities.map((ent, i) => (
              <React.Fragment key={i}>
                <span className="flex items-center gap-1 opacity-80 hover:opacity-100">
                  <Globe className="w-3 h-3 text-indigo-400" />
                  {renderEntityText(ent, false, 'text-indigo-400')}
                </span>
                {i < linkEntities.length - 1 && <span className="text-white/20">|</span>}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* ROW 3: Stack */}
        {tagEntities.length > 0 && (
          <div className="text-[13px] text-text-primary mb-2 leading-relaxed flex items-center flex-wrap">
            <span className="font-bold mr-1">Stack:</span>
            {tagEntities.map((ent, i) => (
              <React.Fragment key={i}>
                {renderEntityText(ent)}
                {i < tagEntities.length - 1 && ', '}
              </React.Fragment>
            ))}
          </div>
        )}

        {/* ROW 4: Description */}
        <div className="text-[13px] text-text-secondary leading-relaxed mt-2">
          {item.description ? item.description.split('\n').map((line, i) => {
            const trimmedLine = line.trim();
            if (!trimmedLine) return null;
            
            const isActualBullet = /^[-•◦]\s/.test(trimmedLine) || /^\*\s/.test(trimmedLine);
            const cleanLine = trimmedLine.replace(/^[-•*◦]\s*/, '');
            
            const renderWithBold = (text: string) => {
              const parts = text.split(/(\*\*.*?\*\*)/g);
              return parts.map((part, idx) => {
                if (part.startsWith('**') && part.endsWith('**')) {
                  return <strong key={idx} className="font-bold text-text-primary">{part.slice(2, -2)}</strong>;
                }
                return <span key={idx}>{part}</span>;
              });
            };
            
            if (isActualBullet) {
              return (
                <div key={i} className="flex gap-2 relative mt-1.5">
                  <span className="text-text-muted absolute left-0 mt-[1px] text-[10px]">•</span>
                  <span className="pl-4">{renderWithBold(cleanLine)}</span>
                </div>
              );
            } else {
              return (
                <div key={i} className="mb-2.5 text-[12.5px] italic text-text-secondary/90 leading-relaxed">
                  {renderWithBold(cleanLine)}
                </div>
              );
            }
          }) : <span className="italic opacity-50">No description provided.</span>}
        </div>
      </div>
    </div>
  );
}

function PersonalInfoSection({ info, onChange }: { info: any, onChange: (info: any) => void }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState(info || {});

  useEffect(() => {
    setEditData(info || {});
  }, [info]);

  const handleSave = () => {
    onChange(editData);
    setIsEditing(false);
  };

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2">
        <h4 className="font-bold text-text-primary uppercase tracking-wider text-sm">Personal Information</h4>
        {!isEditing && (
          <button onClick={() => setIsEditing(true)} className="text-xs font-bold bg-surface hover:bg-surface-hover px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1 text-accent-primary">
            <Edit2 className="w-3 h-3" /> Edit
          </button>
        )}
      </div>
      
      <div className="bg-surface/60 border border-white/5 shadow-xl shadow-black/10 rounded-2xl p-6 hover:bg-surface/80 hover:border-accent-primary/20 transition-all duration-300 relative group overflow-hidden">
        {isEditing ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 relative z-10">
            <div>
              <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Full Name</label>
              <input type="text" value={editData.full_name || ''} onChange={(e) => setEditData({...editData, full_name: e.target.value})} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" />
            </div>
            <div>
              <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Job Title</label>
              <input type="text" value={editData.title || ''} onChange={(e) => setEditData({...editData, title: e.target.value})} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" />
            </div>
            <div>
              <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Email</label>
              <input type="email" value={editData.email || ''} onChange={(e) => setEditData({...editData, email: e.target.value})} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" />
            </div>
            <div>
              <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Phone</label>
              <input type="text" value={editData.phone || ''} onChange={(e) => setEditData({...editData, phone: e.target.value})} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" />
            </div>
            <div>
              <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Location</label>
              <input type="text" value={editData.location || ''} onChange={(e) => setEditData({...editData, location: e.target.value})} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" />
            </div>
            <div>
              <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">LinkedIn</label>
              <input type="text" value={editData.linkedin || ''} onChange={(e) => setEditData({...editData, linkedin: e.target.value})} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" />
            </div>
            <div>
              <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">GitHub</label>
              <input type="text" value={editData.github || ''} onChange={(e) => setEditData({...editData, github: e.target.value})} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" />
            </div>
            <div>
              <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">YouTube</label>
              <input type="text" value={editData.youtube || ''} onChange={(e) => setEditData({...editData, youtube: e.target.value})} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" />
            </div>
            
            <div className="md:col-span-2 flex justify-end gap-2 mt-2">
              <button onClick={() => setIsEditing(false)} className="px-4 py-1.5 rounded-lg text-sm bg-surface hover:bg-surface-hover text-text-primary transition-colors">Cancel</button>
              <button onClick={handleSave} className="px-4 py-1.5 rounded-lg text-sm bg-accent-primary text-white font-bold hover:shadow-[0_0_15px_rgba(37,99,235,0.3)] transition-all">Save</button>
            </div>
          </div>
        ) : (
          <div className="text-center relative z-10 py-2">
            <h2 className="text-3xl font-black text-text-primary tracking-tight mb-1">{info?.full_name || 'Your Name'}</h2>
            <p className="text-lg text-text-secondary font-medium mb-6">{info?.title || 'Your Title'}</p>
            
            <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-3 text-[13px] text-text-secondary">
              {info?.phone && (
                <a href={`tel:${info.phone}`} className="flex items-center gap-1.5 hover:text-accent-primary transition-colors">
                  <Phone className="w-4 h-4 text-text-muted"/> {info.phone}
                </a>
              )}
              {info?.email && (
                <a href={`mailto:${info.email}`} className="flex items-center gap-1.5 hover:text-accent-primary transition-colors">
                  <Mail className="w-4 h-4 text-text-muted"/> {info.email}
                </a>
              )}
              {info?.location && (
                <span className="flex items-center gap-1.5">
                  <MapPin className="w-4 h-4 text-text-muted"/> {info.location}
                </span>
              )}
            </div>
            
            <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-3 mt-3 text-[13px] text-text-secondary">
              {info?.linkedin && (
                <a href={info.linkedin.startsWith('http') ? info.linkedin : `https://${info.linkedin}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 hover:text-indigo-400 transition-colors">
                  <Link2 className="w-4 h-4 text-indigo-400/80"/> {info.linkedin.replace(/^https?:\/\/(www\.)?/, '')}
                </a>
              )}
              {info?.github && (
                <a href={info.github.startsWith('http') ? info.github : `https://${info.github}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 hover:text-slate-200 transition-colors">
                  <Link2 className="w-4 h-4 text-slate-300/80"/> {info.github.replace(/^https?:\/\/(www\.)?/, '')}
                </a>
              )}
              {info?.youtube && (
                <a href={info.youtube.startsWith('http') ? info.youtube : `https://${info.youtube}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 hover:text-rose-400 transition-colors">
                  <Link2 className="w-4 h-4 text-rose-400/80"/> {info.youtube.replace(/^https?:\/\/(www\.)?/, '')}
                </a>
              )}
            </div>
            {(!info?.full_name && !info?.title && !info?.phone && !info?.email && !info?.location && !info?.linkedin && !info?.github && !info?.youtube) && (
              <span className="italic opacity-50 text-sm mt-4 block">Click edit to add your personal information...</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function SkillsSection({ skills, onChange }: { skills: Record<string, string[]>, onChange: (skills: Record<string, string[]>) => void }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState<Record<string, string>>({});

  useEffect(() => {
    const initialData: Record<string, string> = {};
    Object.entries(skills || {}).forEach(([cat, items]) => {
      initialData[cat] = items.join(', ');
    });
    setEditData(initialData);
  }, [skills]);

  const handleSave = () => {
    const newData: Record<string, string[]> = {};
    Object.entries(editData).forEach(([cat, val]) => {
      const parsed = val.split(',').map(s => s.trim()).filter(Boolean);
      if (parsed.length > 0) {
        newData[cat] = parsed;
      }
    });
    onChange(newData);
    setIsEditing(false);
  };

  const handleAddCategory = () => {
    const name = prompt("Enter new category name (e.g. Database, Languages):");
    if (name && !editData[name]) {
      setEditData({ ...editData, [name]: '' });
    }
  };

  const handleDeleteCategory = (cat: string) => {
    if (confirm(`Remove category "${cat}"?`)) {
      const newD = { ...editData };
      delete newD[cat];
      setEditData(newD);
    }
  };

  const handleCategoryRename = (oldCat: string, newCat: string) => {
    if (oldCat === newCat || !newCat) return;
    const newD = { ...editData };
    newD[newCat] = newD[oldCat];
    delete newD[oldCat];
    setEditData(newD);
  };

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2">
        <h4 className="font-bold text-text-primary uppercase tracking-wider text-sm">Technical Skills</h4>
        {!isEditing && (
          <button onClick={() => setIsEditing(true)} className="text-xs font-bold bg-surface hover:bg-surface-hover px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1 text-accent-primary">
            <Edit2 className="w-3 h-3" /> Edit
          </button>
        )}
      </div>

      <div className="bg-surface/60 border border-white/5 shadow-xl shadow-black/10 rounded-2xl p-6 hover:bg-surface/80 hover:border-accent-primary/20 transition-all duration-300 relative group">
        {isEditing ? (
          <div className="space-y-4">
            {Object.entries(editData).map(([category, val]) => (
              <div key={category} className="flex flex-col md:flex-row gap-2 md:gap-4 items-start">
                <div className="w-full md:w-1/3 min-w-[150px]">
                  <input 
                    type="text" 
                    value={category} 
                    onChange={(e) => handleCategoryRename(category, e.target.value)}
                    className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary font-bold outline-none focus:border-accent-primary" 
                    placeholder="Category Name"
                  />
                </div>
                <div className="flex-1 flex w-full gap-2">
                  <textarea 
                    value={val} 
                    onChange={(e) => setEditData({...editData, [category]: e.target.value})} 
                    className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary resize-none min-h-[40px] h-auto" 
                    placeholder="Comma separated skills..."
                  />
                  <button onClick={() => handleDeleteCategory(category)} className="p-2 text-text-muted hover:text-rose-500 rounded bg-white/5 h-[40px]"><Trash2 className="w-4 h-4"/></button>
                </div>
              </div>
            ))}
            
            <div className="flex justify-between items-center mt-6">
              <button onClick={handleAddCategory} className="text-xs font-bold flex items-center gap-1 text-accent-primary hover:bg-white/5 px-2 py-1 rounded">
                <Plus className="w-3 h-3" /> Add Category
              </button>
              <div className="flex gap-2">
                <button onClick={() => setIsEditing(false)} className="px-4 py-1.5 rounded-lg text-sm bg-surface hover:bg-surface-hover text-text-primary transition-colors">Cancel</button>
                <button onClick={handleSave} className="px-4 py-1.5 rounded-lg text-sm bg-accent-primary text-white font-bold hover:shadow-[0_0_15px_rgba(37,99,235,0.3)] transition-all">Save</button>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {Object.entries(skills || {}).length === 0 ? (
               <span className="italic opacity-50 text-sm">Click edit to add technical skills...</span>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-[13px] text-left">
                  <tbody>
                    {Object.entries(skills || {}).map(([category, items]) => (
                      <tr key={category} className="align-top border-b border-white/5 last:border-0 group/row hover:bg-white/5 transition-colors">
                        <td className="py-3 pl-2 pr-4 w-1/4 font-bold text-text-primary whitespace-nowrap">{category}:</td>
                        <td className="py-3 pr-2 text-text-secondary leading-relaxed">
                          {items.join(', ')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function LanguagesSection({ languages, onChange }: { languages: any[], onChange: (langs: any[]) => void }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState<any[]>([]);

  useEffect(() => {
    setEditData(languages || []);
  }, [languages]);

  const handleSave = () => {
    onChange(editData);
    setIsEditing(false);
  };

  const handleAddLanguage = () => {
    setEditData([...editData, { name: '', description: '' }]);
  };

  const handleUpdateLanguage = (index: number, field: string, value: string) => {
    const newData = [...editData];
    newData[index] = { ...newData[index], [field]: value };
    setEditData(newData);
  };

  const handleDeleteLanguage = (index: number) => {
    if (confirm("Remove this language?")) {
      const newData = [...editData];
      newData.splice(index, 1);
      setEditData(newData);
    }
  };

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2">
        <h4 className="font-bold text-text-primary uppercase tracking-wider text-sm">Languages</h4>
        {!isEditing && (
          <button onClick={() => setIsEditing(true)} className="text-xs font-bold bg-surface hover:bg-surface-hover px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1 text-accent-primary">
            <Edit2 className="w-3 h-3" /> Edit
          </button>
        )}
      </div>

      <div className="bg-surface/60 border border-white/5 shadow-xl shadow-black/10 rounded-2xl p-6 hover:bg-surface/80 hover:border-accent-primary/20 transition-all duration-300 relative group">
        {isEditing ? (
          <div className="space-y-4">
            {editData.map((lang, index) => (
              <div key={index} className="flex flex-col md:flex-row gap-2 md:gap-4 items-start relative p-4 border border-white/5 rounded-xl bg-black/10">
                <div className="w-full md:w-1/4">
                  <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Language</label>
                  <input 
                    type="text" 
                    value={lang.name || ''} 
                    onChange={(e) => handleUpdateLanguage(index, 'name', e.target.value)}
                    className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" 
                    placeholder="e.g. English"
                  />
                </div>
                <div className="flex-1 w-full">
                  <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Proficiency & Details</label>
                  <textarea 
                    value={lang.description || ''} 
                    onChange={(e) => handleUpdateLanguage(index, 'description', e.target.value)}
                    className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary resize-none min-h-[60px]" 
                    placeholder="e.g. TOEIC 800, Good reading/listening..."
                  />
                </div>
                <button onClick={() => handleDeleteLanguage(index)} className="absolute top-2 right-2 p-1.5 text-text-muted hover:text-rose-500 rounded bg-white/5"><Trash2 className="w-3.5 h-3.5"/></button>
              </div>
            ))}
            
            <div className="flex justify-between items-center mt-6">
              <button onClick={handleAddLanguage} className="text-xs font-bold flex items-center gap-1 text-accent-primary hover:bg-white/5 px-2 py-1 rounded">
                <Plus className="w-3 h-3" /> Add Language
              </button>
              <div className="flex gap-2">
                <button onClick={() => setIsEditing(false)} className="px-4 py-1.5 rounded-lg text-sm bg-surface hover:bg-surface-hover text-text-primary transition-colors">Cancel</button>
                <button onClick={handleSave} className="px-4 py-1.5 rounded-lg text-sm bg-accent-primary text-white font-bold hover:shadow-[0_0_15px_rgba(37,99,235,0.3)] transition-all">Save</button>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {(languages || []).length === 0 ? (
               <span className="italic opacity-50 text-sm">Click edit to add languages...</span>
            ) : (
              <div className="space-y-3">
                {(languages || []).map((lang, index) => (
                  <div key={index} className="text-[13px] text-text-secondary leading-relaxed">
                    <strong className="text-text-primary mr-2 font-bold">{lang.name}:</strong>
                    <span>{lang.description}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
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
  type SectionKey = 'experience' | 'projects' | 'education' | 'certifications';

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
    <div className="w-full pt-4 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 gap-4">
        <div>
            <h1 className="text-3xl font-black font-outfit tracking-tight mb-1">Upload & Review CV</h1>
            <p className="text-text-secondary text-sm">Review AI extracted entities before saving to My CVs.</p>
        </div>
        {status === 'done' && (
          <button onClick={handleReset} className="px-6 py-2.5 rounded-full bg-surface hover:bg-surface-hover border border-white/10 text-sm font-bold transition-all shadow-sm">
            Upload New
          </button>
        )}
      </div>

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
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-8 animate-in zoom-in-95 duration-500">
          
          {/* Main Feed: Experience & Projects */}
          <div className="xl:col-span-3 space-y-6">
            <h3 className="text-xl font-bold flex items-center gap-3">
              <FileText className="w-5 h-5 text-accent-primary" /> 
              Professional Background
              <span className="bg-surface  text-[10px] px-2 py-0.5 rounded-lg text-text-muted">
                {totalBlocks} Blocks
              </span>
            </h3>

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
            <div className="mb-8">
              <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2">
                <h4 className="font-bold text-text-primary uppercase tracking-wider text-sm">Experience</h4>
                <button onClick={() => addBlock('experience')} className="text-xs font-bold bg-surface hover:bg-surface-hover px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1 text-accent-primary">
                  <Plus className="w-3 h-3" /> Thêm Experience
                </button>
              </div>
              <div className="space-y-4">
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
            </div>

            {/* Projects Section */}
            <div className="mb-8">
              <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2">
                <h4 className="font-bold text-text-primary uppercase tracking-wider text-sm">Projects</h4>
                <button onClick={() => addBlock('projects')} className="text-xs font-bold bg-surface hover:bg-surface-hover px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1 text-accent-primary">
                  <Plus className="w-3 h-3" /> Thêm Project
                </button>
              </div>
              <div className="space-y-4">
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
            </div>

            {/* Education Section */}
            <div className="mb-8">
              <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2">
                <h4 className="font-bold text-text-primary uppercase tracking-wider text-sm">Education</h4>
                <button onClick={() => addBlock('education')} className="text-xs font-bold bg-surface hover:bg-surface-hover px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1 text-accent-primary">
                  <Plus className="w-3 h-3" /> Thêm Education
                </button>
              </div>
              <div className="space-y-4">
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
            </div>

            {/* Certifications Section */}
            <div className="mb-8">
              <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2">
                <h4 className="font-bold text-text-primary uppercase tracking-wider text-sm">Certifications</h4>
                <button onClick={() => addBlock('certifications')} className="text-xs font-bold bg-surface hover:bg-surface-hover px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1 text-accent-primary">
                  <Plus className="w-3 h-3" /> Thêm Certification
                </button>
              </div>
              <div className="space-y-4">
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
            </div>
          </div>

          {/* Sidebar: Skills & Metadata */}
          <div className="space-y-8">
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

                    <div className="pt-4 mt-2 flex flex-col gap-3">
                    <button 
                      onClick={handleSaveToMyCvs}
                      disabled={isSaving || saveSuccess}
                      className={cn(
                        "w-full flex items-center justify-center gap-2 py-3.5 rounded-xl font-bold transition-all duration-300",
                        saveSuccess 
                          ? "bg-emerald-500 text-white shadow-[0_0_20px_rgba(16,185,129,0.4)]" 
                          : "bg-gradient-to-r from-accent-primary to-accent-secondary text-white hover:shadow-[0_0_20px_rgba(37,99,235,0.4)] hover:scale-[1.02] active:scale-95 disabled:opacity-50 disabled:hover:scale-100 disabled:hover:shadow-none"
                      )}
                    >
                      {isSaving ? (
                        <><Loader2 className="w-5 h-5 animate-spin" /> Saving...</>
                      ) : saveSuccess ? (
                        <><Check className="w-5 h-5" /> Saved Successfully!</>
                      ) : (
                        <><Plus className="w-5 h-5" /> Save to My CVs</>
                      )}
                    </button>

                    <div className="grid grid-cols-2 gap-3">
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
