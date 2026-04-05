import React, { useState } from 'react';
import { Sparkles, Save, RotateCcw, Check, X, AlertCircle } from 'lucide-react';
import { chatbotApi } from '../../services/api';
import { cn } from '../../lib/utils';

interface CVSectionEditorProps {
    title: string;
    sectionType: string;
    initialData: any;
    onSave: (data: any) => void;
}

const CVSectionEditor: React.FC<CVSectionEditorProps> = ({ title, sectionType, initialData, onSave }) => {
    const [isEditing, setIsEditing] = useState(false);
    const [data, setData] = useState(initialData);
    const [isRewriting, setIsRewriting] = useState(false);
    const [showComparison, setShowComparison] = useState(false);
    const [rewrittenData, setRewrittenData] = useState<any>(null);

    const handleRewrite = async () => {
        setIsRewriting(true);
        try {
            // Logic varies by section type
            if (sectionType === 'experience' || sectionType === 'projects') {
                const res = await chatbotApi.rewriteSection(
                    data.position || data.name || "Software Developer",
                    data.company || "Project",
                    data.description || []
                );
                setRewrittenData({ ...data, description: res.data.rewritten_points });
                setShowComparison(true);
            }
        } catch (error) {
            console.error("Rewrite failed:", error);
        }
        setIsRewriting(false);
    };

    const handleApplyAI = () => {
        setData(rewrittenData);
        setShowComparison(false);
        onSave(rewrittenData);
    };

    const handleSave = () => {
        onSave(data);
        setIsEditing(false);
    };

    // Render logic for different sections
    const renderContent = () => {
        if (sectionType === 'personal_info') {
            return (
                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                        <label className="text-[10px] font-black uppercase text-text-muted">Full Name</label>
                        <input 
                            className="w-full bg-white/5 border border-white/10 rounded-lg p-2 text-sm focus:border-accent-primary outline-none"
                            value={data.full_name} 
                            onChange={e => setData({...data, full_name: e.target.value})}
                        />
                    </div>
                    <div className="space-y-1">
                        <label className="text-[10px] font-black uppercase text-text-muted">Title</label>
                        <input 
                            className="w-full bg-white/5 border border-white/10 rounded-lg p-2 text-sm focus:border-accent-primary outline-none"
                            value={data.title} 
                            onChange={e => setData({...data, title: e.target.value})}
                        />
                    </div>
                </div>
            );
        }
        
        if (sectionType === 'experience' || sectionType === 'projects') {
            return (
                <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-1">
                            <label className="text-[10px] font-black uppercase text-text-muted">
                                {sectionType === 'experience' ? 'Position' : 'Project Name'}
                            </label>
                            <input 
                                className="w-full bg-white/5 border border-white/10 rounded-lg p-2 text-sm outline-none"
                                value={data.position || data.name} 
                                onChange={e => setData({...data, [sectionType === 'experience' ? 'position' : 'name']: e.target.value})}
                            />
                        </div>
                        <div className="space-y-1">
                            <label className="text-[10px] font-black uppercase text-text-muted">
                                {sectionType === 'experience' ? 'Company' : 'Link/Org'}
                            </label>
                            <input 
                                className="w-full bg-white/5 border border-white/10 rounded-lg p-2 text-sm outline-none"
                                value={data.company || data.link} 
                                onChange={e => setData({...data, [sectionType === 'experience' ? 'company' : 'link']: e.target.value})}
                            />
                        </div>
                    </div>
                    
                    <div className="space-y-2">
                        <div className="flex justify-between items-center">
                            <label className="text-[10px] font-black uppercase text-text-muted">Description (Bullet points)</label>
                            {(sectionType === 'experience' || sectionType === 'projects') && (
                                <button 
                                    onClick={handleRewrite}
                                    disabled={isRewriting}
                                    className="flex items-center gap-1.5 px-3 py-1 bg-accent-primary/20 hover:bg-accent-primary/30 text-accent-primary rounded-full text-[10px] font-black uppercase tracking-wider transition-all disabled:opacity-50"
                                >
                                    <Sparkles className={cn("w-3 h-3", isRewriting && "animate-spin")} />
                                    {isRewriting ? "AI is Thinking..." : "AI Rewrite (STAR)"}
                                </button>
                            )}
                        </div>
                        
                        {(data.description || []).map((point: string, idx: number) => (
                            <div key={idx} className="flex gap-2 group">
                                <span className="text-accent-primary mt-2 flex-shrink-0">•</span>
                                <textarea 
                                    className="flex-1 bg-white/5 border border-white/10 rounded-lg p-2 text-sm outline-none min-h-[60px] resize-none focus:border-accent-primary/50 group-hover:bg-white/10 transition-all font-serif italic"
                                    value={point}
                                    onChange={e => {
                                        const newDesc = [...data.description];
                                        newDesc[idx] = e.target.value;
                                        setData({...data, description: newDesc});
                                    }}
                                />
                                <button 
                                    onClick={() => {
                                        const newDesc = data.description.filter((_: any, i: number) => i !== idx);
                                        setData({...data, description: newDesc});
                                    }}
                                    className="opacity-0 group-hover:opacity-100 p-1 text-red-500 hover:bg-red-500/10 rounded transition-all h-fit mt-1"
                                >
                                    <X className="w-3 h-3" />
                                </button>
                            </div>
                        ))}
                        <button 
                            onClick={() => setData({...data, description: [...(data.description || []), ""]})}
                            className="w-full py-2 border border-dashed border-white/10 rounded-lg text-[10px] uppercase font-black text-text-muted hover:bg-white/5 hover:text-text-primary transition-all"
                        >
                            + Add Bullet Point
                        </button>
                    </div>
                </div>
            );
        }

        return <div className="text-xs text-text-muted italic">Edit mode for {sectionType} coming soon...</div>;
    };

    return (
        <div className="bg-surface border border-white/5 rounded-2xl p-6 mb-6 group transition-all hover:border-white/10 shadow-lg relative overflow-hidden">
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-3">
                    <div className="w-1.5 h-6 bg-accent-primary rounded-full" />
                    <h4 className="font-black uppercase tracking-[0.15em] text-sm">{title}</h4>
                </div>
                
                <div className="flex gap-2">
                    {isEditing ? (
                        <>
                            <button 
                                onClick={() => { setIsEditing(false); setData(initialData); }}
                                className="p-2 text-text-muted hover:text-white transition-all"
                            >
                                <RotateCcw className="w-4 h-4" />
                            </button>
                            <button 
                                onClick={handleSave}
                                className="flex items-center gap-2 px-4 py-1.5 bg-emerald-500 text-white rounded-lg text-xs font-black uppercase tracking-widest shadow-lg shadow-emerald-500/20"
                            >
                                <Save className="w-3 h-3" /> Save
                            </button>
                        </>
                    ) : (
                        <button 
                            onClick={() => setIsEditing(true)}
                            className="px-4 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-xs font-black uppercase tracking-widest transition-all"
                        >
                            Edit
                        </button>
                    )}
                </div>
            </div>

            {/* Content Area */}
            {isEditing ? (
                <div className="animate-in fade-in slide-in-from-top-1 duration-300">
                    {renderContent()}
                </div>
            ) : (
                <div className="text-sm text-text-primary/70 leading-relaxed pl-4 border-l border-white/5 italic">
                    {sectionType === 'personal_info' && `${data.full_name} | ${data.title}`}
                    {(sectionType === 'experience' || sectionType === 'projects') && (
                        <div className="space-y-1">
                            <p className="font-bold text-text-primary">{data.position || data.name} @ {data.company || data.link}</p>
                            <p className="line-clamp-2 opacity-50">{(data.description || []).join(' ')}</p>
                        </div>
                    )}
                </div>
            )}

            {/* Comparison Modal */}
            {showComparison && rewrittenData && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/60 backdrop-blur-md animate-in fade-in duration-300">
                    <div className="bg-canvas border border-white/10 rounded-3xl w-full max-w-4xl max-h-[80vh] overflow-hidden flex flex-col shadow-2xl">
                        <div className="p-6 border-b border-white/10 flex justify-between items-center bg-slate-900/50">
                            <div>
                                <h3 className="text-xl font-black text-accent-primary uppercase tracking-widest">Compare AI Improvements✨</h3>
                                <p className="text-xs text-text-muted mt-1">AI has rewritten your experience using high-impact action verbs and STAR format.</p>
                            </div>
                            <button onClick={() => setShowComparison(false)} className="p-2 hover:bg-white/5 rounded-full"><X/></button>
                        </div>
                        
                        <div className="flex-1 overflow-y-auto p-8 grid grid-cols-2 gap-8 bg-slate-950/30">
                            <div className="space-y-4">
                                <p className="text-[10px] font-black uppercase tracking-widest text-text-muted flex items-center gap-2">
                                    <AlertCircle className="w-3 h-3"/> Original
                                </p>
                                <div className="bg-white/5 rounded-2xl p-6 border border-white/5 text-sm leading-relaxed space-y-4 font-serif opacity-60">
                                    {data.description.map((p: string, i: number) => <p key={i}>• {p}</p>)}
                                </div>
                            </div>
                            
                            <div className="space-y-4">
                                <p className="text-[10px] font-black uppercase tracking-widest text-accent-primary flex items-center gap-2">
                                    <Sparkles className="w-3 h-3 animate-pulse"/> AI Optimized (Professional)
                                </p>
                                <div className="bg-accent-primary/5 rounded-2xl p-6 border border-accent-primary/20 text-sm leading-relaxed space-y-4 font-serif relative">
                                    <div className="absolute top-0 right-0 w-16 h-16 bg-accent-primary/5 rounded-full blur-3xl -z-10" />
                                    {rewrittenData.description.map((p: string, i: number) => (
                                        <p key={i} className="animate-in slide-in-from-right-4 fade-in duration-500" style={{animationDelay: `${i*100}ms`}}>
                                            <span className="text-accent-primary font-bold mr-2">•</span> {p}
                                        </p>
                                    ))}
                                </div>
                            </div>
                        </div>

                        <div className="p-6 border-t border-white/10 bg-slate-900/50 flex justify-end gap-3">
                            <button 
                                onClick={() => setShowComparison(false)}
                                className="px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest text-text-muted hover:text-white transition-all"
                            >
                                Discard AI Version
                            </button>
                            <button 
                                onClick={handleApplyAI}
                                className="px-8 py-3 bg-accent-primary text-white rounded-xl text-xs font-black uppercase tracking-widest shadow-xl shadow-accent-primary/20 hover:scale-105 active:scale-95 transition-all flex items-center gap-2"
                            >
                                <Check className="w-4 h-4" /> Apply Improvements
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CVSectionEditor;
