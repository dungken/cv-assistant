import React, { useState } from 'react';
import { Clock, RotateCcw, GitCompare, Star, Tag, Edit3, Check, X } from 'lucide-react';
import { CvDocument, CvVersionInfo } from '../../services/api';

interface VersionTimelineProps {
    document: CvDocument;
    onClose: () => void;
    onDiff: (vA: number, vB: number) => void;
    onRestore: (versionNumber: number) => Promise<void>;
    onUpdateVersion: (versionId: number, data: { note?: string; tag?: string; isStarred?: boolean }) => Promise<void>;
}

const VersionTimeline: React.FC<VersionTimelineProps> = ({ document: doc, onClose, onDiff, onRestore, onUpdateVersion }) => {
    const [diffA, setDiffA] = useState<number | null>(null);
    const [editingNote, setEditingNote] = useState<number | null>(null);
    const [noteText, setNoteText] = useState('');
    const [restoringVersion, setRestoringVersion] = useState<number | null>(null);

    const timeAgo = (dateStr: string) => {
        const diff = Date.now() - new Date(dateStr).getTime();
        const mins = Math.floor(diff / 60000);
        if (mins < 60) return `${mins}m ago`;
        const hours = Math.floor(mins / 60);
        if (hours < 24) return `${hours}h ago`;
        const days = Math.floor(hours / 24);
        if (days < 7) return `${days}d ago`;
        return new Date(dateStr).toLocaleDateString();
    };

    const handleRestore = async (versionNumber: number) => {
        setRestoringVersion(versionNumber);
        try { await onRestore(versionNumber); } finally { setRestoringVersion(null); }
    };

    const handleSaveNote = async (v: CvVersionInfo) => {
        await onUpdateVersion(v.id, { note: noteText });
        setEditingNote(null);
    };

    const handleToggleStar = async (v: CvVersionInfo) => {
        await onUpdateVersion(v.id, { isStarred: !v.isStarred });
    };

    return (
        <div className="border-t border-white/5 bg-secondary/10 px-8 py-6 max-h-[40vh] overflow-y-auto animate-in slide-in-from-bottom-4 duration-300">
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h3 className="font-bold text-text-primary text-sm">Version History</h3>
                    <p className="text-[10px] text-text-secondary/60">{doc.name} &middot; {doc.versions.length} version{doc.versions.length !== 1 ? 's' : ''}</p>
                </div>
                <div className="flex items-center gap-2">
                    {diffA !== null && (
                        <span className="text-[10px] bg-accent-primary/10 text-accent-primary px-2 py-1 rounded-lg font-bold">
                            Select second version to compare
                        </span>
                    )}
                    <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-secondary/50 text-text-secondary">
                        <X className="w-4 h-4" />
                    </button>
                </div>
            </div>

            <div className="space-y-1">
                {doc.versions.map((v, i) => (
                    <div key={v.id} className="flex items-start gap-3 group">
                        {/* Timeline dot & line */}
                        <div className="flex flex-col items-center pt-1">
                            <div className={`w-3 h-3 rounded-full border-2 ${i === 0 ? 'bg-accent-primary border-accent-primary' : 'bg-transparent border-text-secondary/30'}`} />
                            {i < doc.versions.length - 1 && <div className="w-px h-full bg-text-secondary/10 min-h-[2rem]" />}
                        </div>

                        {/* Content */}
                        <div className={`flex-1 pb-3 ${diffA === v.versionNumber ? 'bg-accent-primary/5 -mx-2 px-2 rounded-xl' : ''}`}>
                            <div className="flex items-center gap-2">
                                <span className="text-xs font-bold text-text-primary">
                                    v{v.versionNumber}
                                    {i === 0 && <span className="ml-1 text-[9px] bg-accent-primary/10 text-accent-primary px-1.5 py-0.5 rounded-md font-black uppercase">current</span>}
                                </span>
                                <span className="text-[10px] text-text-secondary/50">{timeAgo(v.createdAt)}</span>
                                {v.isStarred && <Star className="w-3 h-3 text-amber-400 fill-amber-400" />}
                                {v.tag && <span className="text-[9px] bg-accent-secondary/10 text-accent-secondary px-1.5 py-0.5 rounded-md font-bold">{v.tag}</span>}
                            </div>

                            {editingNote === v.id ? (
                                <div className="flex items-center gap-2 mt-1">
                                    <input type="text" value={noteText} onChange={(e) => setNoteText(e.target.value)}
                                        className="flex-1 bg-secondary/50 text-text-primary rounded-lg px-2 py-1 text-xs outline-none focus:ring-1 focus:ring-accent-primary/30" autoFocus />
                                    <button onClick={() => handleSaveNote(v)} className="p-1 text-emerald-500 hover:bg-emerald-500/10 rounded"><Check className="w-3 h-3" /></button>
                                    <button onClick={() => setEditingNote(null)} className="p-1 text-text-secondary hover:bg-secondary/50 rounded"><X className="w-3 h-3" /></button>
                                </div>
                            ) : (
                                <p className="text-[11px] text-text-secondary/70 mt-0.5">{v.note || 'No note'}</p>
                            )}

                            {/* Actions */}
                            <div className="flex items-center gap-1 mt-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                                {i > 0 && (
                                    <button onClick={() => handleRestore(v.versionNumber)} disabled={restoringVersion === v.versionNumber}
                                        className="flex items-center gap-1 text-[9px] font-bold text-accent-primary bg-accent-primary/10 hover:bg-accent-primary/20 px-2 py-1 rounded-lg transition-colors">
                                        <RotateCcw className="w-3 h-3" /> Restore
                                    </button>
                                )}
                                <button onClick={() => {
                                    if (diffA === null) { setDiffA(v.versionNumber); }
                                    else { onDiff(diffA, v.versionNumber); setDiffA(null); }
                                }}
                                    className="flex items-center gap-1 text-[9px] font-bold text-text-secondary bg-secondary/30 hover:bg-secondary/50 px-2 py-1 rounded-lg transition-colors">
                                    <GitCompare className="w-3 h-3" /> {diffA === null ? 'Diff' : 'Compare'}
                                </button>
                                <button onClick={() => handleToggleStar(v)}
                                    className="p-1 text-text-secondary hover:text-amber-400 transition-colors">
                                    <Star className={`w-3 h-3 ${v.isStarred ? 'fill-amber-400 text-amber-400' : ''}`} />
                                </button>
                                <button onClick={() => { setEditingNote(v.id); setNoteText(v.note || ''); }}
                                    className="p-1 text-text-secondary hover:text-accent-primary transition-colors">
                                    <Edit3 className="w-3 h-3" />
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default VersionTimeline;
