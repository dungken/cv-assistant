import React, { useState, useRef } from 'react';
import {
    UploadCloud, FileText, Link2, ClipboardPaste, Loader2, Brain,
    Briefcase, Building2, MapPin, TrendingUp, Star, CheckCircle,
    AlertCircle, Hash, ArrowRight, Trash2
} from 'lucide-react';
import { jdApi, JDParseResult } from '../../services/api';
import { cn } from '../../lib/utils';

type InputTab = 'upload' | 'paste' | 'url';
type Status = 'idle' | 'parsing' | 'done' | 'error';

const LEVEL_COLORS: Record<string, string> = {
    senior: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    mid: 'text-sky-400 bg-sky-500/10 border-sky-500/20',
    junior: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    intern: 'text-violet-400 bg-violet-500/10 border-violet-500/20',
    unspecified: 'text-text-muted bg-surface border-border',
};

export default function JDUpload() {
    const [activeTab, setActiveTab] = useState<InputTab>('paste');
    const [status, setStatus] = useState<Status>('idle');
    const [result, setResult] = useState<JDParseResult | null>(null);
    const [errorMsg, setErrorMsg] = useState('');

    // Upload tab state
    const [file, setFile] = useState<File | null>(null);
    const [isHovering, setIsHovering] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    // Paste tab state
    const [pasteText, setPasteText] = useState('');
    const [pasteTitle, setPasteTitle] = useState('');
    const [pasteCompany, setPasteCompany] = useState('');

    // URL tab state
    const [url, setUrl] = useState('');

    const tabs: { key: InputTab; label: string; icon: React.ReactNode }[] = [
        { key: 'upload', label: 'Upload File', icon: <UploadCloud className="w-4 h-4" /> },
        { key: 'paste', label: 'Paste Text', icon: <ClipboardPaste className="w-4 h-4" /> },
        { key: 'url', label: 'From URL', icon: <Link2 className="w-4 h-4" /> },
    ];

    const handleParse = async () => {
        setStatus('parsing');
        setErrorMsg('');
        try {
            let res;
            if (activeTab === 'upload' && file) {
                res = await jdApi.parseFile(file);
            } else if (activeTab === 'paste' && pasteText.trim()) {
                res = await jdApi.parseText(pasteText, pasteTitle, pasteCompany);
            } else if (activeTab === 'url' && url.trim()) {
                res = await jdApi.parseUrl(url);
            } else {
                setErrorMsg('Please provide input first.');
                setStatus('error');
                return;
            }
            setResult(res.data);
            setStatus('done');
        } catch (e: any) {
            setErrorMsg(e?.response?.data?.detail || e?.response?.data?.error || 'Parsing failed. Please check your input and try again.');
            setStatus('error');
        }
    };

    const handleReset = () => {
        setStatus('idle');
        setResult(null);
        setFile(null);
        setPasteText('');
        setUrl('');
        setErrorMsg('');
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsHovering(false);
        if (e.dataTransfer.files?.[0]) setFile(e.dataTransfer.files[0]);
    };

    const canParse = () => {
        if (status === 'parsing') return false;
        if (activeTab === 'upload') return !!file;
        if (activeTab === 'paste') return pasteText.trim().length > 20;
        if (activeTab === 'url') return url.trim().length > 10;
        return false;
    };

    return (
        <div className="p-8 w-full animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* Header */}
            <div className="flex justify-between items-end mb-8">
                <div>
                    <h2 className="text-4xl font-black tracking-tighter mb-2">JD Analysis</h2>
                    <p className="text-text-secondary">Upload or paste a Job Description for intelligent parsing.</p>
                </div>
                {status === 'done' && (
                    <button onClick={handleReset} className="px-6 py-2 rounded-full text-sm font-bold hover:bg-surface transition-all">
                        Analyze New JD
                    </button>
                )}
            </div>

            {/* Input Section */}
            {status !== 'done' && (
                <>
                    {/* Tab Selector */}
                    <div className="flex gap-2 mb-6">
                        {tabs.map(tab => (
                            <button
                                key={tab.key}
                                onClick={() => { setActiveTab(tab.key); setErrorMsg(''); }}
                                className={cn(
                                    "flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all",
                                    activeTab === tab.key
                                        ? "bg-accent-primary text-white shadow-lg shadow-accent-primary/20"
                                        : "bg-surface text-text-secondary hover:bg-accent-primary/10 hover:text-accent-primary hover:scale-[1.02]"
                                )}
                            >
                                {tab.icon}
                                {tab.label}
                            </button>
                        ))}
                    </div>

                    {/* Upload Tab */}
                    {activeTab === 'upload' && (
                        <div
                            onDragOver={(e) => { e.preventDefault(); setIsHovering(true); }}
                            onDragLeave={() => setIsHovering(false)}
                            onDrop={handleDrop}
                            className={cn(
                                "border-2 border-dashed rounded-3xl p-16 flex flex-col items-center justify-center transition-all duration-300 mb-6",
                                isHovering ? 'border-accent-primary bg-accent-primary/5 scale-[1.01]' : 'bg-surface/50'
                            )}
                        >
                            <input
                                ref={inputRef}
                                type="file"
                                className="hidden"
                                onChange={(e) => { if (e.target.files?.[0]) { setFile(e.target.files[0]); e.target.value = ''; } }}
                                accept=".pdf,.docx,.doc,.txt"
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
                                    <button onClick={() => setFile(null)} className="px-5 py-2 rounded-full text-text-secondary text-sm hover:bg-accent-primary/10 hover:text-accent-primary transition-all">
                                        Change
                                    </button>
                                </div>
                            ) : (
                                <>
                                    <div className="w-20 h-20 rounded-full bg-overlay flex items-center justify-center mb-5">
                                        <UploadCloud className="w-9 h-9 text-text-secondary" />
                                    </div>
                                    <h3 className="text-xl font-bold mb-2">Drop your JD file here</h3>
                                    <p className="text-text-muted text-sm text-center max-w-xs mb-6">
                                        Supports PDF, DOCX, and TXT files up to 10MB.
                                    </p>
                                    <button
                                        onClick={() => inputRef.current?.click()}
                                        className="px-8 py-3 rounded-full bg-text-primary text-canvas font-bold hover:bg-text-secondary transition-colors"
                                    >
                                        Select File
                                    </button>
                                </>
                            )}
                        </div>
                    )}

                    {/* Paste Tab */}
                    {activeTab === 'paste' && (
                        <div className="space-y-4 mb-6">
                            <div className="grid grid-cols-2 gap-4">
                                <input
                                    type="text"
                                    placeholder="Job Title (optional)"
                                    value={pasteTitle}
                                    onChange={(e) => setPasteTitle(e.target.value)}
                                    className="bg-surface rounded-xl px-4 py-3 text-sm text-text-primary placeholder:text-text-muted/50 outline-none focus:ring-2 focus:ring-accent-primary/30"
                                />
                                <input
                                    type="text"
                                    placeholder="Company (optional)"
                                    value={pasteCompany}
                                    onChange={(e) => setPasteCompany(e.target.value)}
                                    className="bg-surface rounded-xl px-4 py-3 text-sm text-text-primary placeholder:text-text-muted/50 outline-none focus:ring-2 focus:ring-accent-primary/30"
                                />
                            </div>
                            <textarea
                                placeholder="Paste the full Job Description here..."
                                value={pasteText}
                                onChange={(e) => setPasteText(e.target.value)}
                                rows={12}
                                className="w-full bg-surface rounded-2xl px-5 py-4 text-sm text-text-primary placeholder:text-text-muted/50 outline-none resize-none focus:ring-2 focus:ring-accent-primary/30 leading-relaxed"
                            />
                            <p className="text-[11px] text-text-muted/60">
                                {pasteText.length} characters
                            </p>
                        </div>
                    )}

                    {/* URL Tab */}
                    {activeTab === 'url' && (
                        <div className="mb-6">
                            <div className="flex gap-3">
                                <div className="flex-1 flex items-center bg-surface rounded-2xl px-5 py-4 focus-within:ring-2 focus-within:ring-accent-primary/30">
                                    <Link2 className="w-5 h-5 text-text-muted mr-3 flex-shrink-0" />
                                    <input
                                        type="url"
                                        placeholder="https://www.linkedin.com/jobs/view/... or any job listing URL"
                                        value={url}
                                        onChange={(e) => setUrl(e.target.value)}
                                        className="w-full bg-transparent text-sm text-text-primary placeholder:text-text-muted/50 outline-none"
                                    />
                                </div>
                            </div>
                            <p className="text-[11px] text-text-muted/60 mt-3">
                                Supports most job listing websites including LinkedIn, VietnamWorks, TopCV, etc.
                            </p>
                        </div>
                    )}

                    {/* Parse Button */}
                    <button
                        onClick={handleParse}
                        disabled={!canParse()}
                        className={cn(
                            "w-full py-4 rounded-2xl font-bold text-sm flex items-center justify-center gap-2 transition-all",
                            canParse()
                                ? "bg-accent-primary text-white hover:shadow-[0_0_30px_rgba(37,99,235,0.3)]"
                                : "bg-surface text-text-muted cursor-not-allowed"
                        )}
                    >
                        {status === 'parsing' ? (
                            <><Loader2 className="w-5 h-5 animate-spin" /> Analyzing JD...</>
                        ) : (
                            <><Brain className="w-5 h-5" /> Analyze Job Description</>
                        )}
                    </button>
                </>
            )}

            {/* Error State */}
            {status === 'error' && (
                <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 mt-6 flex gap-4 items-start">
                    <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
                    <div>
                        <p className="font-bold">Analysis Failed</p>
                        <p className="text-sm mt-1 opacity-80">{errorMsg}</p>
                    </div>
                </div>
            )}

            {/* Results Panel */}
            {status === 'done' && result && (
                <div className="space-y-6 animate-in zoom-in-95 duration-500">
                    {/* Summary Cards */}
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                        {result.title && (
                            <div className="bg-surface/50 rounded-2xl p-5">
                                <div className="flex items-center gap-2 mb-2">
                                    <Briefcase className="w-4 h-4 text-accent-primary" />
                                    <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">Position</span>
                                </div>
                                <p className="font-bold text-text-primary text-sm leading-snug">{result.title}</p>
                            </div>
                        )}
                        {result.company && (
                            <div className="bg-surface/50 rounded-2xl p-5">
                                <div className="flex items-center gap-2 mb-2">
                                    <Building2 className="w-4 h-4 text-violet-400" />
                                    <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">Company</span>
                                </div>
                                <p className="font-bold text-text-primary text-sm">{result.company}</p>
                            </div>
                        )}
                        {result.level !== 'unspecified' && (
                            <div className="bg-surface/50 rounded-2xl p-5">
                                <div className="flex items-center gap-2 mb-2">
                                    <TrendingUp className="w-4 h-4 text-amber-400" />
                                    <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">Level</span>
                                </div>
                                <span className={cn("px-3 py-1 rounded-lg border text-xs font-bold capitalize", LEVEL_COLORS[result.level] || LEVEL_COLORS.unspecified)}>
                                    {result.level}{result.experience_years ? ` (${result.experience_years} yrs)` : ''}
                                </span>
                            </div>
                        )}
                        {result.location && (
                            <div className="bg-surface/50 rounded-2xl p-5">
                                <div className="flex items-center gap-2 mb-2">
                                    <MapPin className="w-4 h-4 text-rose-400" />
                                    <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">Location</span>
                                </div>
                                <p className="font-bold text-text-primary text-sm">{result.location}</p>
                            </div>
                        )}
                    </div>

                    {/* Skills */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Required Skills */}
                        <div className="bg-surface/50 rounded-2xl p-6">
                            <h3 className="text-sm font-bold mb-4 flex items-center gap-2">
                                <Star className="w-4 h-4 text-amber-400" />
                                Required Skills
                                <span className="text-[10px] font-normal text-text-muted ml-auto">
                                    {result.extracted_skills.required.length}
                                </span>
                            </h3>
                            <div className="flex flex-wrap gap-2">
                                {result.extracted_skills.required.map((skill: string, i: number) => (
                                    <span key={i} className="px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-bold">
                                        {skill}
                                    </span>
                                ))}
                                {result.extracted_skills.required.length === 0 && (
                                    <span className="text-xs text-text-muted italic">No required skills detected</span>
                                )}
                            </div>
                        </div>

                        {/* Preferred Skills */}
                        <div className="bg-surface/50 rounded-2xl p-6">
                            <h3 className="text-sm font-bold mb-4 flex items-center gap-2">
                                <Star className="w-4 h-4 text-sky-400" />
                                Preferred Skills
                                <span className="text-[10px] font-normal text-text-muted ml-auto">
                                    {result.extracted_skills.preferred.length}
                                </span>
                            </h3>
                            <div className="flex flex-wrap gap-2">
                                {result.extracted_skills.preferred.map((skill: string, i: number) => (
                                    <span key={i} className="px-3 py-1.5 rounded-lg bg-sky-500/10 border border-sky-500/20 text-sky-400 text-xs font-bold">
                                        {skill}
                                    </span>
                                ))}
                                {result.extracted_skills.preferred.length === 0 && (
                                    <span className="text-xs text-text-muted italic">No preferred skills detected</span>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Sections */}
                    {(Object.entries(result.sections) as [string, string[]][]).map(([sectionKey, items]) => {
                        if (!items || items.length === 0) return null;
                        const sectionLabels: Record<string, { label: string; icon: React.ReactNode }> = {
                            requirements: { label: 'Requirements', icon: <CheckCircle className="w-4 h-4 text-emerald-400" /> },
                            responsibilities: { label: 'Responsibilities', icon: <Briefcase className="w-4 h-4 text-sky-400" /> },
                            benefits: { label: 'Benefits', icon: <Star className="w-4 h-4 text-amber-400" /> },
                            about: { label: 'About', icon: <Building2 className="w-4 h-4 text-violet-400" /> },
                            preferred: { label: 'Nice to Have', icon: <TrendingUp className="w-4 h-4 text-teal-400" /> },
                        };
                        const meta = sectionLabels[sectionKey];
                        if (!meta) return null;

                        return (
                            <div key={sectionKey} className="bg-surface/40 rounded-2xl p-6">
                                <h3 className="text-sm font-bold mb-4 flex items-center gap-2">
                                    {meta.icon}
                                    {meta.label}
                                    <span className="text-[10px] font-normal text-text-muted ml-auto">{items.length} items</span>
                                </h3>
                                <ul className="space-y-2">
                                    {items.map((item: string, i: number) => (
                                        <li key={i} className="flex gap-3 text-sm text-text-secondary leading-relaxed">
                                            <span className="text-accent-primary/40 mt-1.5 flex-shrink-0">
                                                <ArrowRight className="w-3 h-3" />
                                            </span>
                                            {item}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        );
                    })}

                    {/* Metadata */}
                    <div className="p-5 rounded-2xl bg-overlay/30">
                        <p className="text-[10px] font-black text-text-muted uppercase mb-3 tracking-[0.2em]">Parse Metadata</p>
                        <div className="flex flex-wrap gap-6 text-sm">
                            <div className="flex items-center gap-2 text-text-secondary">
                                <Hash className="w-4 h-4 text-text-muted" />
                                <span>Language: <strong className="text-text-primary uppercase">{result.metadata.language}</strong></span>
                            </div>
                            <div className="flex items-center gap-2 text-text-secondary">
                                <FileText className="w-4 h-4 text-text-muted" />
                                <span>Method: <strong className="text-text-primary capitalize">{result.metadata.input_method}</strong></span>
                            </div>
                            <div className="flex items-center gap-2 text-text-secondary">
                                <Brain className="w-4 h-4 text-text-muted" />
                                <span>Parse time: <strong className="text-text-primary">{result.metadata.parse_time_ms}ms</strong></span>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
