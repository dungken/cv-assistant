import { Entity } from '../../../services/api';
import React, { useState, useEffect } from 'react';
import { Edit2, Trash2, Globe, Plus, X, Lock, Users, Briefcase, Link2 } from 'lucide-react';

export function ExperienceCard({ 
  item, 
  title, 
  onUpdate,
  onDelete
}: { 
  item: any; 
  title: string;
  onUpdate: (updatedItem: any) => void;
  onDelete?: () => void;
}) {
  const [isEditing, setIsEditing] = useState(false);
  
  // Form states
  const [editAnchor, setEditAnchor] = useState(item.anchor || '');
  const [editDesc, setEditDesc] = useState(item.description || '');
  const [editSubtitle, setEditSubtitle] = useState('');
  const [editLocation, setEditLocation] = useState('');
  const [editDates, setEditDates] = useState('');
  
  // Tag chips state
  const [editStackTags, setEditStackTags] = useState<string[]>([]);
  const [tempStackInput, setTempStackInput] = useState('');
  
  // Custom enhanced fields
  const [editJobMode, setEditJobMode] = useState(item.job_mode || '');
  const [editLocationMode, setEditLocationMode] = useState(item.location_mode || '');
  const [editTeamSize, setEditTeamSize] = useState(item.team_size || '');
  const [editIsNda, setEditIsNda] = useState(item.is_nda || false);
  const [editCustomLinks, setEditCustomLinks] = useState<{ url: string; title: string }[]>([]);

  useEffect(() => {
    if (isEditing) {
      setEditAnchor(item.anchor || '');
      setEditDesc(item.description || '');
      
      const entities = (item.entities || []) as Entity[];
      const getTexts = (types: string[]) => entities.filter((e: Entity) => types.includes(e.type)).map((e: Entity) => e.text);
      
      setEditSubtitle(getTexts(['ORG', 'JOB_TITLE', 'DEGREE', 'MAJOR', 'CERT', 'PROJECT']).join(', '));
      setEditLocation(getTexts(['LOC']).join(', '));
      setEditDates(getTexts(['DATE']).join(' - '));
      
      const rawSkills = entities.filter((e: Entity) => e.type === 'SKILL').map((e: Entity) => e.text);
      setEditStackTags(rawSkills);
      setTempStackInput('');
      
      setEditJobMode(item.job_mode || '');
      setEditLocationMode(item.location_mode || '');
      setEditTeamSize(item.team_size || '');
      setEditIsNda(item.is_nda || false);
      
      if (item.custom_links && item.custom_links.length > 0) {
        setEditCustomLinks(item.custom_links);
      } else {
        const rawLinks = entities.filter((e: Entity) => e.type === 'LINK').map((e: Entity) => e.text);
        setEditCustomLinks(rawLinks.map(url => ({ url, title: '' })));
      }
    }
  }, [isEditing, item]);

  const handleAddStackTag = (val: string) => {
    const clean = val.trim();
    if (clean && !editStackTags.includes(clean)) {
      setEditStackTags([...editStackTags, clean]);
    }
    setTempStackInput('');
  };

  const handleStackInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddStackTag(tempStackInput);
    } else if (e.key === ',') {
      e.preventDefault();
      handleAddStackTag(tempStackInput);
    } else if (e.key === 'Backspace' && !tempStackInput) {
      if (editStackTags.length > 0) {
        const nextTags = [...editStackTags];
        nextTags.pop();
        setEditStackTags(nextTags);
      }
    }
  };

  const handleStackInputBlur = () => {
    handleAddStackTag(tempStackInput);
  };

  const handleRemoveStackTag = (idx: number) => {
    const nextTags = [...editStackTags];
    nextTags.splice(idx, 1);
    setEditStackTags(nextTags);
  };

  const handleAddLink = () => {
    setEditCustomLinks([...editCustomLinks, { url: '', title: '' }]);
  };

  const handleRemoveLink = (idx: number) => {
    const nextLinks = [...editCustomLinks];
    nextLinks.splice(idx, 1);
    setEditCustomLinks(nextLinks);
  };

  const handleLinkChange = (idx: number, key: 'url' | 'title', value: string) => {
    const nextLinks = [...editCustomLinks];
    nextLinks[idx] = { ...nextLinks[idx], [key]: value };
    setEditCustomLinks(nextLinks);
  };

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

    // Add Stack / Skills tags directly as SKILL entities
    editStackTags.forEach(tag => {
      const t = tag.trim();
      if (t) newEntities.push({ text: t, type: 'SKILL', start: 0, end: 0, confidence: 1 });
    });

    // Add links into entities as well for backwards compatibility
    editCustomLinks.forEach(link => {
      if (link.url.trim()) {
        newEntities.push({ text: link.url.trim(), type: 'LINK', start: 0, end: 0, confidence: 1 });
      }
    });

    onUpdate({
      anchor: editAnchor,
      description: editDesc,
      entities: newEntities,
      job_mode: editJobMode,
      location_mode: editLocationMode,
      team_size: editTeamSize,
      is_nda: editIsNda,
      custom_links: editCustomLinks.filter(l => l.url.trim())
    });
    setIsEditing(false);
  };

  if (isEditing) {
    const isJobRelated = title === 'Experience' || title === 'Project';
    
    return (
      <div className="bg-surface/60 border border-white/5 shadow-xl shadow-black/10 rounded-2xl p-6 relative mb-4 animate-in fade-in duration-200">
        <div className="space-y-6">
          
          {/* Section: Main Header Fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Title / Anchor</label>
              <input type="text" value={editAnchor} onChange={e => setEditAnchor(e.target.value)} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" placeholder="e.g. Backend Developer" />
            </div>
            <div>
              <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Organization / Role</label>
              <input type="text" value={editSubtitle} onChange={e => setEditSubtitle(e.target.value)} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" placeholder="e.g. Smart Sports Tablet (SST)" />
            </div>
            <div>
              <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Dates</label>
              <input type="text" value={editDates} onChange={e => setEditDates(e.target.value)} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" placeholder="e.g. Jan 2026 - Jun 2026" />
            </div>
            <div>
              <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Location</label>
              <input type="text" value={editLocation} onChange={e => setEditLocation(e.target.value)} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" placeholder="e.g. Ho Chi Minh City, Remote" />
            </div>
            
            {/* STACK / SKILLS tags input */}
            <div>
              <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Stack / Skills (Tag Chips)</label>
              <div 
                className="flex flex-wrap gap-1.5 p-2 bg-black/20 border border-accent-primary/30 hover:border-accent-primary/50 focus-within:border-accent-primary focus-within:bg-black/30 rounded-xl min-h-[38px] cursor-text items-center transition-all duration-200"
                onClick={() => document.getElementById(`stack-input-${item.anchor}`)?.focus()}
              >
                {editStackTags.map((tag, idx) => (
                  <span key={idx} className="inline-flex items-center gap-1.5 bg-accent-primary/10 border border-accent-primary/30 text-accent-primary text-xs px-2.5 py-0.5 rounded-lg font-medium hover:bg-accent-primary/15 transition-all">
                    {tag}
                    <button 
                      type="button" 
                      onClick={(e) => { e.stopPropagation(); handleRemoveStackTag(idx); }} 
                      className="text-accent-primary/70 hover:text-accent-primary hover:bg-accent-primary/25 rounded p-0.5 transition-colors"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
                <input 
                  id={`stack-input-${item.anchor}`}
                  type="text" 
                  value={tempStackInput} 
                  onChange={e => setTempStackInput(e.target.value)} 
                  onKeyDown={handleStackInputKeyDown}
                  onBlur={handleStackInputBlur}
                  className="flex-1 bg-transparent border-none outline-none text-xs text-text-primary min-w-[100px]" 
                  placeholder={editStackTags.length === 0 ? "Press Enter or Comma to add stack..." : ""}
                />
              </div>
            </div>
          </div>

          {/* Section: Job Mode & Team Details (Only for Job related items) */}
          {isJobRelated && (
            <div className="border-t border-white/5 pt-4 space-y-4">
              <h5 className="text-xs font-bold text-accent-primary uppercase tracking-wider flex items-center gap-1.5">
                <Briefcase className="w-3.5 h-3.5" /> Job Details & Privacy
              </h5>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Employment Type</label>
                  <select 
                    value={editJobMode} 
                    onChange={e => setEditJobMode(e.target.value)}
                    className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary h-[38px]"
                  >
                    <option value="" className="bg-surface">-- Select Type --</option>
                    <option value="Full-time" className="bg-surface">Full-time</option>
                    <option value="Freelance" className="bg-surface">Freelance</option>
                    <option value="Part-time" className="bg-surface">Part-time</option>
                    <option value="Contract" className="bg-surface">Contract</option>
                    <option value="Internship" className="bg-surface">Internship</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Workplace Type</label>
                  <select 
                    value={editLocationMode} 
                    onChange={e => setEditLocationMode(e.target.value)}
                    className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary h-[38px]"
                  >
                    <option value="" className="bg-surface">-- Select Workplace --</option>
                    <option value="Remote" className="bg-surface">Remote</option>
                    <option value="Hybrid" className="bg-surface">Hybrid</option>
                    <option value="On-site" className="bg-surface">On-site</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Team Size</label>
                  <input 
                    type="text" 
                    value={editTeamSize} 
                    onChange={e => setEditTeamSize(e.target.value)} 
                    className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" 
                    placeholder="e.g. 5 developers" 
                  />
                </div>
              </div>
              <div className="flex items-center gap-2 mt-2 bg-black/10 border border-white/5 rounded-xl p-3">
                <input 
                  type="checkbox" 
                  id="nda-checkbox"
                  checked={editIsNda} 
                  onChange={e => setEditIsNda(e.target.checked)} 
                  className="rounded border-accent-primary/30 text-accent-primary focus:ring-accent-primary h-4 w-4 bg-black/20 cursor-pointer" 
                />
                <label htmlFor="nda-checkbox" className="text-sm font-semibold text-text-primary flex items-center gap-1.5 cursor-pointer select-none">
                  <Lock className="w-3.5 h-3.5 text-rose-400" /> Dự án thuộc diện Bảo mật (NDA) - Hiển thị nhãn Khóa & NDA
                </label>
              </div>
            </div>
          )}

          {/* Section: Dynamic Link Builder */}
          <div className="border-t border-white/5 pt-4 space-y-4">
            <div className="flex justify-between items-center">
              <h5 className="text-xs font-bold text-accent-primary uppercase tracking-wider flex items-center gap-1.5">
                <Link2 className="w-3.5 h-3.5" /> Interactive Links & Titles
              </h5>
              <button 
                type="button" 
                onClick={handleAddLink} 
                className="text-xs font-bold text-accent-primary hover:bg-white/5 px-2 py-1 rounded flex items-center gap-1 transition-colors"
              >
                <Plus className="w-3 h-3" /> Add Link
              </button>
            </div>

            {editCustomLinks.length === 0 ? (
              <p className="text-xs italic text-text-muted">No links added. Click 'Add Link' to attach live demos, source code, or credentials.</p>
            ) : (
              <div className="space-y-3">
                {editCustomLinks.map((link, idx) => (
                  <div key={idx} className="flex gap-3 items-center animate-in slide-in-from-left-2 duration-150">
                    <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-2 bg-black/10 p-2.5 rounded-xl border border-white/5">
                      <div>
                        <label className="text-[9px] uppercase font-bold text-text-muted mb-0.5 block">Link URL</label>
                        <input 
                          type="text" 
                          value={link.url} 
                          onChange={e => handleLinkChange(idx, 'url', e.target.value)} 
                          placeholder="e.g. https://smartsports.vn/" 
                          className="w-full bg-black/20 border border-white/10 rounded p-1.5 text-xs text-text-primary outline-none focus:border-accent-primary" 
                        />
                      </div>
                      <div>
                        <label className="text-[9px] uppercase font-bold text-text-muted mb-0.5 block">Display Title (Anchor)</label>
                        <input 
                          type="text" 
                          value={link.title} 
                          onChange={e => handleLinkChange(idx, 'title', e.target.value)} 
                          placeholder="e.g. smartsports.vn, View Certificate" 
                          className="w-full bg-black/20 border border-white/10 rounded p-1.5 text-xs text-text-primary outline-none focus:border-accent-primary" 
                        />
                      </div>
                    </div>
                    <button 
                      type="button" 
                      onClick={() => handleRemoveLink(idx)} 
                      className="p-2 text-text-muted hover:text-rose-500 rounded bg-white/5 hover:bg-rose-500/10 transition-colors"
                      title="Remove Link"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Section: Description Text Area */}
          <div className="border-t border-white/5 pt-4">
            <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Description</label>
            <textarea value={editDesc} onChange={e => setEditDesc(e.target.value)} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary resize-y min-h-[260px] font-mono text-[12px] leading-relaxed" placeholder="Italic summary paragraph...&#10;- **Bullet Title:** Bullet details..." />
          </div>

        </div>

        <div className="flex justify-end gap-2 mt-6 pt-4 border-t border-white/5">
          <button onClick={() => setIsEditing(false)} className="px-4 py-1.5 rounded-lg text-sm bg-surface hover:bg-surface-hover text-text-primary transition-colors">Cancel</button>
          <button onClick={handleSave} className="px-4 py-1.5 rounded-lg text-sm bg-accent-primary text-white font-bold hover:shadow-[0_0_15px_rgba(37,99,235,0.3)] transition-all">Save</button>
        </div>
      </div>
    );
  }

  // --- View Mode ---
  const entities = (item.entities || []) as Entity[];
  const dateEntities = entities.filter((ent: Entity) => ent.type === 'DATE');
  const subtitleEntities = entities.filter((ent: Entity) => ['ORG', 'JOB_TITLE', 'DEGREE', 'MAJOR', 'LOC', 'PER', 'CERT', 'PROJECT'].includes(ent.type));
  const tagEntities = entities.filter((ent: Entity) => !['DATE', 'LINK', 'ORG', 'JOB_TITLE', 'DEGREE', 'MAJOR', 'LOC', 'PER', 'CERT', 'PROJECT'].includes(ent.type));

  const renderEntityText = (ent: Entity, isBold: boolean = false, customClasses?: string) => {
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

  const isJobRelated = title === 'Experience' || title === 'Project';
  const customLinks = item.custom_links || [];

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
          <div className="text-[15px] font-bold text-accent-primary flex items-center gap-2">
            {item.anchor || 'Untitled'}
            {isJobRelated && item.is_nda && (
              <span className="flex items-center gap-1 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-[10px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider">
                <Lock className="w-2.5 h-2.5" /> NDA
              </span>
            )}
          </div>
          <div className="text-[13px] text-text-secondary font-medium">
            {dateEntities.length > 0 ? dateEntities.map((ent: Entity, i: number) => (
              <React.Fragment key={i}>
                {renderEntityText(ent)}
                {i < dateEntities.length - 1 && ' - '}
              </React.Fragment>
            )) : <span className="text-text-muted italic text-[11px]">No Date</span>}
          </div>
        </div>

        {/* ROW 2: Subtitle, Workplace Metadata & Links */}
        <div className="flex justify-between items-baseline mb-2 flex-wrap gap-2">
          <div className="text-[13px] flex items-center flex-wrap gap-y-1">
            {/* Organization / Primary block */}
            <span className="font-bold text-text-primary mr-2 flex items-center flex-wrap">
              {subtitleEntities.filter((e: Entity) => ['ORG', 'JOB_TITLE', 'DEGREE'].includes(e.type)).length > 0 ? 
                subtitleEntities.filter((e: Entity) => ['ORG', 'JOB_TITLE', 'DEGREE'].includes(e.type)).map((ent: Entity, i: number, arr: Entity[]) => (
                  <React.Fragment key={i}>
                    {renderEntityText(ent, true)}
                    {i < arr.length - 1 && ', '}
                  </React.Fragment>
                )) : null
              }
            </span>

            {/* Employment details: Job Mode, Workplace, Team size */}
            {isJobRelated && (item.job_mode || item.location_mode || item.team_size) && (
              <span className="text-text-muted/80 text-[12.5px] font-medium mr-2 flex items-center gap-1.5">
                {item.job_mode && <span>· {item.job_mode}</span>}
                {item.location_mode && <span>· {item.location_mode}</span>}
                {item.team_size && (
                  <span className="flex items-center gap-1">
                    · <Users className="w-3 h-3 text-text-muted" /> Team size: {item.team_size}
                  </span>
                )}
              </span>
            )}

            {/* Workplace Location */}
            <span className="text-text-secondary flex items-center flex-wrap">
              {subtitleEntities.filter((e: Entity) => !['ORG', 'JOB_TITLE', 'DEGREE'].includes(e.type)).length > 0 ? 
                subtitleEntities.filter((e: Entity) => !['ORG', 'JOB_TITLE', 'DEGREE'].includes(e.type)).map((ent: Entity, i: number, arr: Entity[]) => (
                  <React.Fragment key={i}>
                    {renderEntityText(ent, false, 'text-text-secondary')}
                    {i < arr.length - 1 && ' · '}
                  </React.Fragment>
                )) : null
              }
            </span>
          </div>
          
          {/* Custom structured Links */}
          <div className="text-[12px] flex items-center flex-wrap gap-2">
            {customLinks.map((link: any, i: number) => {
              const displayTitle = link.title || link.url.replace(/^https?:\/\/(www\.)?/, '');
              return (
                <React.Fragment key={i}>
                  <a 
                    href={link.url.startsWith('http') ? link.url : `https://${link.url}`} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className="flex items-center gap-1 text-indigo-400 hover:text-indigo-300 font-semibold opacity-90 hover:opacity-100 transition-all"
                  >
                    <Globe className="w-3.5 h-3.5" />
                    <span>{displayTitle}</span>
                  </a>
                  {i < customLinks.length - 1 && <span className="text-white/20">|</span>}
                </React.Fragment>
              );
            })}
          </div>
        </div>

        {/* ROW 3: Stack (Upgraded Tag Chips) */}
        {tagEntities.length > 0 && (
          <div className="text-[13px] text-text-primary mb-3 leading-relaxed flex items-center flex-wrap gap-1.5 mt-2.5">
            <span className="font-bold text-text-secondary text-[12px] mr-1.5 uppercase tracking-wider">Stack:</span>
            {tagEntities.map((ent: Entity, i: number) => (
              <span key={i} className="inline-flex items-center bg-white/5 border border-white/10 hover:border-accent-primary/30 hover:bg-accent-primary/5 text-text-primary text-xs px-2.5 py-0.5 rounded-lg font-medium transition-all duration-200">
                {renderEntityText(ent)}
              </span>
            ))}
          </div>
        )}

        {/* ROW 4: Description */}
        <div className="text-[13px] text-text-secondary leading-relaxed mt-2">
          {item.description ? item.description.split('\n').map((line: string, i: number) => {
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
