import React, { useState, useEffect } from 'react';
import { Search, Plus, FileText, Trash2, RotateCcw, Edit3, Download, Clock, Star, Filter, X, ChevronDown } from 'lucide-react';
import { cvDocumentApi, CvDocument } from '../../services/api';
import VersionTimeline from './VersionTimeline';
import DiffView from './DiffView';

interface CVListPageProps {
    onClose: () => void;
    onSelect: (doc: CvDocument, dataJson: string) => void;
}

const CVListPage: React.FC<CVListPageProps> = ({ onClose, onSelect }) => {
    const [documents, setDocuments] = useState<CvDocument[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isInitialLoading, setIsInitialLoading] = useState(true);
    const [isSearching, setIsSearching] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [sortBy, setSortBy] = useState('updated');
    const [debouncedSearchQuery, setDebouncedSearchQuery] = useState(searchQuery);
    const [selectedDoc, setSelectedDoc] = useState<CvDocument | null>(null);
    const [showTimeline, setShowTimeline] = useState(false);
    const [diffVersions, setDiffVersions] = useState<{ docId: number; vA: number; vB: number } | null>(null);
    const [error, setError] = useState('');

    // Debounce search query
    useEffect(() => {
        const timer = setTimeout(() => setDebouncedSearchQuery(searchQuery), 300);
        return () => clearTimeout(timer);
    }, [searchQuery]);

    useEffect(() => {
        const controller = new AbortController();
        loadDocuments(controller.signal);
        return () => controller.abort();
    }, [debouncedSearchQuery, sortBy]);

    const loadDocuments = async (signal?: AbortSignal) => {
        if (isInitialLoading) setIsLoading(true);
        else setIsSearching(true);

        try {
            const res = await cvDocumentApi.list({ 
                query: debouncedSearchQuery || undefined, 
                sortBy 
            }, { signal });
            setDocuments(res.data);
            setError('');
        } catch (err: any) {
            if (err.name === 'CanceledError' || err.name === 'AbortError') return;
            setError('Failed to load CV documents');
        } finally {
            setIsLoading(false);
            setIsInitialLoading(false);
            setIsSearching(false);
        }
    };

    const handleDelete = async (id: number) => {
        try {
            await cvDocumentApi.delete(id);
            setDocuments(prev => prev.filter(d => d.id !== id));
            if (selectedDoc?.id === id) { setSelectedDoc(null); setShowTimeline(false); }
        } catch { setError('Failed to delete'); }
    };

    const handleRestore = async (id: number) => {
        try {
            await cvDocumentApi.restore(id);
            await loadDocuments();
        } catch { setError('Failed to restore'); }
    };

    const handleOpen = async (doc: CvDocument) => {
        setIsLoading(true);
        try {
            // Get the latest version ID (doc.versions is sorted by VersionNumber DESC)
            const latestVersion = doc.versions[0];
            if (!latestVersion) throw new Error('No version found');
            
            const detail = await cvDocumentApi.getVersion(doc.id, latestVersion.id);
            onSelect(doc, detail.data.dataJson);
        } catch {
            setError('Failed to open CV document');
        } finally {
            setIsLoading(false);
        }
    };

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

    return (
        <div className="fixed inset-0 z-50 bg-canvas/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-300">
            <div className="w-full max-w-5xl max-h-[90vh] overflow-hidden bg-surface rounded-3xl shadow-2xl border border-white/5 flex flex-col">
                {/* Header */}
                <div className="px-8 py-6 border-b border-white/5 flex items-center justify-between">
                    <div>
                        <h2 className="text-2xl font-black tracking-tighter">My CVs</h2>
                        <p className="text-xs text-text-secondary mt-1">{documents.length} document{documents.length !== 1 ? 's' : ''}</p>
                    </div>
                    <button onClick={onClose} className="p-2 rounded-xl hover:bg-secondary/50 transition-colors">
                        <X className="w-5 h-5 text-text-secondary" />
                    </button>
                </div>

                {/* Toolbar */}
                <div className="px-8 py-4 flex items-center gap-4 border-b border-white/5">
                    <div className="relative flex-1">
                        {isSearching ? (
                            <div className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 border-2 border-accent-primary/30 border-t-accent-primary rounded-full animate-spin" />
                        ) : (
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary/40" />
                        )}
                        <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Search CVs..."
                            className="w-full bg-secondary/50 text-text-primary rounded-xl pl-10 pr-4 py-2.5 outline-none focus:ring-2 focus:ring-accent-primary/20 text-sm font-medium placeholder:text-text-secondary/30" />
                    </div>
                    <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}
                        className="bg-secondary/50 text-text-primary rounded-xl px-4 py-2.5 outline-none text-sm font-medium appearance-none pr-8">
                        <option value="updated">Latest Updated</option>
                        <option value="created">Latest Created</option>
                        <option value="name">Name A-Z</option>
                    </select>
                </div>

                {error && <div className="mx-8 mt-4 bg-red-500/10 border border-red-500/20 text-red-500 text-xs py-3 px-4 rounded-xl text-center font-bold">{error}</div>}

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-8">
                    {isLoading && isInitialLoading ? (
                        <div className="flex items-center justify-center py-20">
                            <div className="w-8 h-8 border-2 border-accent-primary/30 border-t-accent-primary rounded-full animate-spin"></div>
                        </div>
                    ) : documents.length === 0 ? (
                        <div className="text-center py-20">
                            <FileText className="w-16 h-16 text-text-secondary/20 mx-auto mb-4" />
                            <p className="text-text-secondary font-medium">No CV documents yet</p>
                            <p className="text-text-secondary/60 text-sm mt-1">Create your first CV using the CV Builder</p>
                        </div>
                    ) : (
                        <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 transition-all duration-300 ${isSearching ? 'opacity-40 grayscale-[20%] scale-[0.99]' : 'opacity-100'}`}>
                            {documents.map(doc => (
                                <div key={doc.id}
                                    className={`group bg-secondary/20 hover:bg-secondary/40 rounded-2xl p-5 transition-all cursor-pointer border border-transparent hover:border-accent-primary/20 ${selectedDoc?.id === doc.id ? 'border-accent-primary/40 bg-accent-primary/5' : ''}`}
                                    onClick={() => { setSelectedDoc(doc); setShowTimeline(true); setDiffVersions(null); }}>
                                    <div className="flex items-start justify-between mb-3">
                                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-primary/20 to-accent-secondary/20 flex items-center justify-center">
                                            <FileText className="w-5 h-5 text-accent-primary" />
                                        </div>
                                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button onClick={(e) => { e.stopPropagation(); handleOpen(doc); }}
                                                className="p-1.5 rounded-lg bg-accent-primary/10 text-accent-primary hover:bg-accent-primary hover:text-white transition-all shadow-sm"
                                                title="Open in Builder">
                                                <Edit3 className="w-3.5 h-3.5" />
                                            </button>
                                            <button onClick={(e) => { e.stopPropagation(); handleDelete(doc.id); }}
                                                className="p-1.5 rounded-lg hover:bg-red-500/10 text-text-secondary hover:text-red-500 transition-colors">
                                                <Trash2 className="w-3.5 h-3.5" />
                                            </button>
                                        </div>
                                    </div>

                                    <h3 className="font-bold text-text-primary text-sm truncate mb-1">{doc.name}</h3>
                                    {doc.template && <p className="text-[10px] font-bold text-accent-primary/60 uppercase tracking-wider mb-2">{doc.template}</p>}

                                    <div className="flex items-center gap-3 text-[10px] text-text-secondary/60 font-medium">
                                        <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {timeAgo(doc.updatedAt)}</span>
                                        <span>v{doc.currentVersion}</span>
                                        {doc.atsScore && <span className="text-emerald-500 font-bold">{doc.atsScore}/100</span>}
                                    </div>

                                    {doc.targetJd && (
                                        <p className="mt-2 text-[10px] text-text-secondary/50 truncate">JD: {doc.targetJd}</p>
                                    )}

                                    {doc.versions.some(v => v.isStarred) && (
                                        <Star className="w-3 h-3 text-amber-400 fill-amber-400 mt-2" />
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Version Timeline Panel */}
                {showTimeline && selectedDoc && !diffVersions && (
                    <VersionTimeline
                        document={selectedDoc}
                        onClose={() => setShowTimeline(false)}
                        onDiff={(vA, vB) => setDiffVersions({ docId: selectedDoc.id, vA, vB })}
                        onRestore={async (versionNumber) => {
                            await cvDocumentApi.restoreVersion(selectedDoc.id, versionNumber);
                            await loadDocuments();
                        }}
                        onUpdateVersion={async (versionId, data) => {
                            await cvDocumentApi.updateVersion(versionId, data);
                            await loadDocuments();
                        }}
                    />
                )}

                {/* Diff View */}
                {diffVersions && (
                    <DiffView
                        docId={diffVersions.docId}
                        versionA={diffVersions.vA}
                        versionB={diffVersions.vB}
                        onClose={() => setDiffVersions(null)}
                    />
                )}
            </div>
        </div>
    );
};

export default CVListPage;
