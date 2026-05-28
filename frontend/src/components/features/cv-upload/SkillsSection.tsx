import React, { useState, useEffect } from 'react';
import { Edit2, Plus, Trash2, X, Tag } from 'lucide-react';

export function SkillsSection({ skills, onChange }: { skills: Record<string, string[]>, onChange: (skills: Record<string, string[]>) => void }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState<Record<string, string[]>>({});
  const [tempInputs, setTempInputs] = useState<Record<string, string>>({});

  useEffect(() => {
    const initialData: Record<string, string[]> = {};
    Object.entries(skills || {}).forEach(([cat, items]) => {
      initialData[cat] = [...(items || [])];
    });
    setEditData(initialData);
  }, [skills]);

  const handleSave = () => {
    const newData: Record<string, string[]> = {};
    Object.entries(editData).forEach(([cat, list]) => {
      const filtered = (list || []).map(s => s.trim()).filter(Boolean);
      if (filtered.length > 0) {
        newData[cat] = filtered;
      }
    });
    onChange(newData);
    setIsEditing(false);
  };

  const handleAddCategory = () => {
    const name = prompt("Enter new category name (e.g. Database, Languages):");
    if (name && !editData[name]) {
      setEditData({ ...editData, [name]: [] });
      setTempInputs({ ...tempInputs, [name]: '' });
    }
  };

  const handleDeleteCategory = (cat: string) => {
    if (confirm(`Remove category "${cat}"?`)) {
      const newD = { ...editData };
      delete newD[cat];
      setEditData(newD);
      
      const newT = { ...tempInputs };
      delete newT[cat];
      setTempInputs(newT);
    }
  };

  const handleCategoryRename = (oldCat: string, newCat: string) => {
    if (oldCat === newCat || !newCat) return;
    const newD = { ...editData };
    newD[newCat] = newD[oldCat];
    delete newD[oldCat];
    setEditData(newD);

    const newT = { ...tempInputs };
    newT[newCat] = newT[oldCat];
    delete newT[oldCat];
    setTempInputs(newT);
  };

  const handleAddTag = (cat: string, value: string) => {
    const cleanValue = value.replace(/,/g, '').trim();
    if (!cleanValue) return;
    
    const currentTags = editData[cat] || [];
    if (currentTags.includes(cleanValue)) {
      setTempInputs({ ...tempInputs, [cat]: '' });
      return;
    }

    setEditData({
      ...editData,
      [cat]: [...currentTags, cleanValue]
    });
    setTempInputs({ ...tempInputs, [cat]: '' });
  };

  const handleDeleteTag = (cat: string, tagIndex: number) => {
    const currentTags = editData[cat] || [];
    const newTags = [...currentTags];
    newTags.splice(tagIndex, 1);
    setEditData({
      ...editData,
      [cat]: newTags
    });
  };

  const handleKeyDown = (cat: string, e: React.KeyboardEvent<HTMLInputElement>) => {
    const currentVal = tempInputs[cat] || '';
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      handleAddTag(cat, currentVal);
    } else if (e.key === 'Backspace' && !currentVal) {
      const currentTags = editData[cat] || [];
      if (currentTags.length > 0) {
        handleDeleteTag(cat, currentTags.length - 1);
      }
    }
  };

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2">
        <h4 className="font-bold text-text-primary uppercase tracking-wider text-sm flex items-center gap-2">
          <Tag className="w-4 h-4 text-accent-primary" /> Technical Skills
        </h4>
        {!isEditing && (
          <button onClick={() => setIsEditing(true)} className="text-xs font-bold bg-surface hover:bg-surface-hover px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1 text-accent-primary">
            <Edit2 className="w-3 h-3" /> Edit
          </button>
        )}
      </div>

      <div className="bg-surface/60 border border-white/5 shadow-xl shadow-black/10 rounded-2xl p-6 hover:bg-surface/80 hover:border-accent-primary/20 transition-all duration-300 relative group">
        {isEditing ? (
          <div className="space-y-6">
            {Object.entries(editData).map(([category, tags]) => (
              <div key={category} className="flex flex-col md:flex-row gap-2 md:gap-4 items-start border-b border-white/5 pb-4 last:border-0 last:pb-0">
                <div className="w-full md:w-1/4">
                  <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Category Name</label>
                  <input 
                    type="text" 
                    value={category} 
                    onChange={(e) => handleCategoryRename(category, e.target.value)}
                    className="w-full bg-black/20 border border-accent-primary/30 rounded p-2 text-sm text-text-primary font-bold outline-none focus:border-accent-primary" 
                    placeholder="Category Name"
                  />
                </div>
                
                <div className="flex-1 w-full space-y-2">
                  <label className="text-[10px] uppercase font-bold text-text-muted mb-1 block">Skills (Press Enter or Comma to add)</label>
                  <div className="flex w-full gap-2 items-start">
                    <div 
                      className="flex-1 bg-black/20 border border-accent-primary/30 rounded-xl p-2 flex flex-wrap gap-2 focus-within:border-accent-primary focus-within:bg-black/40 transition-all cursor-text min-h-[44px]"
                      onClick={(e) => {
                        const input = e.currentTarget.querySelector('input');
                        if (input) input.focus();
                      }}
                    >
                      {(tags || []).map((tag, tagIndex) => (
                        <span 
                          key={`${tag}-${tagIndex}`}
                          className="bg-accent-primary/10 border border-accent-primary/20 text-accent-primary text-xs font-semibold px-2.5 py-1 rounded-lg flex items-center gap-1.5 hover:bg-accent-primary/20 transition-all animate-in zoom-in-75 duration-150"
                        >
                          {tag}
                          <button 
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteTag(category, tagIndex);
                            }}
                            className="text-accent-primary/60 hover:text-accent-primary transition-colors cursor-pointer font-bold"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </span>
                      ))}
                      <input
                        type="text"
                        value={tempInputs[category] || ''}
                        onChange={(e) => setTempInputs({ ...tempInputs, [category]: e.target.value })}
                        onKeyDown={(e) => handleKeyDown(category, e)}
                        onBlur={() => handleAddTag(category, tempInputs[category] || '')}
                        className="flex-1 min-w-[120px] bg-transparent text-sm text-text-primary outline-none border-none p-0.5 focus:ring-0"
                        placeholder={(tags || []).length === 0 ? "Type skill & press Enter..." : "Add skill..."}
                      />
                    </div>
                    <button 
                      onClick={() => handleDeleteCategory(category)} 
                      className="p-2.5 text-text-muted hover:text-rose-500 rounded bg-white/5 h-[44px] flex items-center justify-center transition-colors"
                      title="Remove Category"
                    >
                      <Trash2 className="w-4 h-4"/>
                    </button>
                  </div>
                </div>
              </div>
            ))}
            
            <div className="flex justify-between items-center mt-6 pt-4 border-t border-white/5">
              <button onClick={handleAddCategory} className="text-xs font-bold flex items-center gap-1 text-accent-primary hover:bg-white/5 px-2 py-1 rounded transition-colors">
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
                        <td className="py-3 pr-2 text-text-secondary leading-relaxed flex flex-wrap gap-1.5 items-center">
                          {(items || []).map((item, idx) => (
                            <span 
                              key={idx}
                              className="bg-white/5 border border-white/10 text-text-secondary text-xs px-2.5 py-0.5 rounded-lg hover:bg-white/10 hover:text-text-primary transition-all duration-200 cursor-default font-medium"
                            >
                              {item}
                            </span>
                          ))}
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

