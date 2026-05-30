import { Link2 } from 'lucide-react';
import React, { useState, useEffect } from 'react';
import { Edit2, Check, X, Building, Mail, Phone, MapPin, Briefcase } from 'lucide-react';

export function PersonalInfoSection({ info, onChange }: { info: any, onChange: (info: any) => void }) {
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
          <div className="space-y-6 relative z-10">
            {/* Core Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
              <div className="md:col-span-2">
                <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Location</label>
                <input type="text" value={editData.location || ''} onChange={(e) => setEditData({...editData, location: e.target.value})} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" />
              </div>
            </div>

            {/* Social Links & Custom Titles */}
            <div className="border-t border-white/5 pt-4 space-y-4">
              <h5 className="text-xs font-bold text-accent-primary uppercase tracking-wider">Social Links & Titles</h5>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">LinkedIn Link</label>
                  <input type="text" value={editData.linkedin || ''} onChange={(e) => setEditData({...editData, linkedin: e.target.value})} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" placeholder="e.g. linkedin.com/in/dungdev" />
                </div>
                <div>
                  <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">LinkedIn Link Title</label>
                  <input type="text" value={editData.linkedin_title || ''} onChange={(e) => setEditData({...editData, linkedin_title: e.target.value})} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" placeholder="e.g. linkedin.com/in/dungdev (Optional)" />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">GitHub Link</label>
                  <input type="text" value={editData.github || ''} onChange={(e) => setEditData({...editData, github: e.target.value})} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" placeholder="e.g. github.com/dungken" />
                </div>
                <div>
                  <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">GitHub Link Title</label>
                  <input type="text" value={editData.github_title || ''} onChange={(e) => setEditData({...editData, github_title: e.target.value})} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" placeholder="e.g. github.com/dungken (Optional)" />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">YouTube Link</label>
                  <input type="text" value={editData.youtube || ''} onChange={(e) => setEditData({...editData, youtube: e.target.value})} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" placeholder="e.g. youtube.com/@dungkenn" />
                </div>
                <div>
                  <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">YouTube Link Title</label>
                  <input type="text" value={editData.youtube_title || ''} onChange={(e) => setEditData({...editData, youtube_title: e.target.value})} className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" placeholder="e.g. youtube.com/@dungkenn (Optional)" />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2">
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
              {info?.linkedin && typeof info.linkedin === 'string' && (
                <a href={info.linkedin.startsWith('http') ? info.linkedin : `https://${info.linkedin}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 hover:text-indigo-400 transition-colors">
                  <Link2 className="w-4 h-4 text-indigo-400/80"/> {info.linkedin_title || info.linkedin.replace(/^https?:\/\/(www\.)?/, '')}
                </a>
              )}
              {info?.github && typeof info.github === 'string' && (
                <a href={info.github.startsWith('http') ? info.github : `https://${info.github}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 hover:text-slate-200 transition-colors">
                  <Link2 className="w-4 h-4 text-slate-300/80"/> {info.github_title || info.github.replace(/^https?:\/\/(www\.)?/, '')}
                </a>
              )}
              {info?.youtube && typeof info.youtube === 'string' && (
                <a href={info.youtube.startsWith('http') ? info.youtube : `https://${info.youtube}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 hover:text-rose-400 transition-colors">
                  <Link2 className="w-4 h-4 text-rose-400/80"/> {info.youtube_title || info.youtube.replace(/^https?:\/\/(www\.)?/, '')}
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

