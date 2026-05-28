import React, { useState, useEffect } from 'react';
import { Edit2, Check, X, Plus, Trash2, ExternalLink } from 'lucide-react';

export function LanguagesSection({ languages, onChange }: { languages: any[], onChange: (langs: any[]) => void }) {
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
    setEditData([...editData, { name: '', description: '', link: '', link_title: 'View Certificate' }]);
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
              <div key={index} className="flex flex-col gap-3 relative p-4 border border-white/5 rounded-xl bg-black/10">
                <div className="flex flex-col md:flex-row gap-4 items-start">
                  <div className="w-full md:w-1/4">
                    <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Language</label>
                    <input 
                      type="text" 
                      value={lang.name || ''} 
                      onChange={(e) => handleUpdateLanguage(index, 'name', e.target.value)}
                      className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" 
                      placeholder="e.g. Japanese"
                    />
                  </div>
                  <div className="flex-1 w-full">
                    <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Proficiency & Details</label>
                    <textarea 
                      value={lang.description || ''} 
                      onChange={(e) => handleUpdateLanguage(index, 'description', e.target.value)}
                      className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary resize-none min-h-[50px]" 
                      placeholder="e.g. JLPT N3. Good reading/listening..."
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Certificate Link (Optional)</label>
                    <input 
                      type="text" 
                      value={lang.link || ''} 
                      onChange={(e) => handleUpdateLanguage(index, 'link', e.target.value)}
                      className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" 
                      placeholder="e.g. https://github.com/..."
                    />
                  </div>
                  <div>
                    <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Link Title</label>
                    <input 
                      type="text" 
                      value={lang.link_title || ''} 
                      onChange={(e) => handleUpdateLanguage(index, 'link_title', e.target.value)}
                      className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary outline-none focus:border-accent-primary" 
                      placeholder="e.g. View Certificate"
                    />
                  </div>
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
                  <div key={index} className="text-[13px] text-text-secondary leading-relaxed flex flex-wrap items-center gap-x-2">
                    <strong className="text-text-primary font-bold">{lang.name}:</strong>
                    <span>{lang.description}</span>
                    {lang.link && (
                      <a 
                        href={lang.link.startsWith('http') ? lang.link : `https://${lang.link}`} 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        className="text-accent-primary hover:text-accent-secondary inline-flex items-center gap-0.5 font-medium hover:underline group"
                      >
                        <ExternalLink className="w-3 h-3 group-hover:scale-110 transition-transform"/> {lang.link_title || 'View Certificate'}
                      </a>
                    )}
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

