import React, { useState, useEffect } from 'react';
import { 
  CheckCircle2, Sparkles, Target, Save, 
  Layout, Send, ChevronRight, BarChart3, Bot 
} from 'lucide-react';
import { 
  chatbotApi, collectorApi, CVData, 
  OptimizationResponse, OptimizationSuggestion 
} from '../../services/api';
import CVPreview from './CVPreview';
import CVSectionEditor from './CVSectionEditor';
import ATSScoreDashboard from './ATSScoreDashboard';
import OptimizationPanel from './OptimizationPanel';
import { cn } from '../../lib/utils';

interface CVBuilderViewProps {
    sessionId: number;
    initialCvData: CVData;
    initialStep: number;
    onDataSync?: (data: CVData) => void;
    onStepSync?: (step: number) => void;
    isArtifactMode?: boolean;
}

const CVBuilderView: React.FC<CVBuilderViewProps> = ({ 
    sessionId, initialCvData, initialStep, onDataSync, onStepSync, isArtifactMode 
}) => {
    const [cvData, setCvData] = useState<CVData>(initialCvData);
    const [currentStep, setCurrentStep] = useState(initialStep);
    const [jdText, setJdText] = useState('');
    const [optimizationRes, setOptimizationRes] = useState<OptimizationResponse | null>(null);
    const [isOptimizing, setIsOptimizing] = useState(false);
    const [activeTab, setActiveTab] = useState<'editor' | 'preview' | 'analysis'>('preview');

    const steps = [
        "Cá nhân", "Học vấn", "Kinh nghiệm", "Kỹ năng", "Dự án", "Chứng chỉ"
    ];

    useEffect(() => {
        setCvData(initialCvData);
        setCurrentStep(initialStep);
        if (initialStep >= 7 && activeTab !== 'analysis') setActiveTab('editor');
    }, [initialCvData, initialStep]);

    const handleSectionUpdate = (type: string, index: number | null, newData: any) => {
        const updatedData = { ...cvData };
        if (type === 'personal_info') {
            updatedData.personal_info = newData;
        } else if (type === 'experience' && index !== null) {
            updatedData.experience[index] = newData;
        } else if (type === 'projects' && index !== null) {
            updatedData.projects[index] = newData;
        } else if (type === 'summary') {
            updatedData.summary = newData;
        }
        setCvData(updatedData);
        onDataSync?.(updatedData);
        
        collectorApi.updateProgress(sessionId, currentStep, JSON.stringify(updatedData), currentStep >= 7);
    };

    const handleOptimize = async () => {
        setIsOptimizing(true);
        setActiveTab('analysis');
        try {
            const res = await chatbotApi.getOptimizationSuggestions(cvData, jdText);
            setOptimizationRes(res.data);
        } catch (error) {
            console.error("Optimization failed:", error);
        }
        setIsOptimizing(false);
    };

    const handleApplySuggestion = async (id: string, preview?: string) => {
        if (!preview) return;
        
        const updatedData = { ...cvData };
        // Simple logic for summary first, can be expanded to skills/exp
        if (id.includes('summary')) {
            updatedData.summary = preview;
        } else if (id.includes('keyword') || id.includes('skill')) {
            // Logic to append missing keywords to skills section
            const newSkills = [...updatedData.skills];
            const suggestedSkills = preview.split(',').map(s => s.trim());
            suggestedSkills.forEach(s => {
                if (!newSkills.includes(s)) newSkills.push(s);
            });
            updatedData.skills = newSkills;
        }
        
        setCvData(updatedData);
        onDataSync?.(updatedData);
        // Remove suggestion after applying
        if (optimizationRes) {
            setOptimizationRes({
                ...optimizationRes,
                suggestions: optimizationRes.suggestions.filter(s => s.id !== id)
            });
        }
    };

    return (
        <div className="flex flex-col h-full bg-canvas overflow-hidden">
            {/* Progress Header */}
            <div className="p-6 bg-slate-900/40 backdrop-blur-md border-b border-white/5">
                <div className="flex justify-between items-center mb-4">
                    <div className="flex flex-col gap-1">
                        <h3 className="text-sm font-black uppercase tracking-[0.2em] text-accent-primary flex items-center gap-2">
                            {currentStep >= 7 ? (
                                <span className="flex items-center gap-2 text-emerald-500 font-black tracking-widest"><CheckCircle2 className="w-4 h-4" /> CV Construction Complete</span>
                            ) : (
                                <>Step {currentStep}/6: {steps[currentStep - 1]}</>
                            )}
                        </h3>
                        <span className="text-[10px] font-bold text-text-muted bg-white/5 px-2 py-1 rounded tracking-widest uppercase w-fit">
                            {Math.round((Math.min(currentStep, 6) / 6) * 100)}% Complete
                        </span>
                    </div>
                    
                    <button
                        className={cn(
                            "flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-xs transition-all duration-500 shadow-lg",
                            currentStep >= 7 
                                ? "bg-emerald-500 hover:bg-emerald-600 text-white shadow-[0_0_20px_rgba(16,185,129,0.3)]" 
                                : "bg-white/5 hover:bg-white/10 text-text-muted border border-white/10"
                        )}
                    >
                        📥 Export PDF
                    </button>
                </div>
                <div className="flex gap-1.5 h-1.5 w-full">
                    {steps.map((_, idx) => (
                        <div 
                            key={idx} 
                            className={cn(
                                "flex-1 rounded-full transition-all duration-500",
                                idx + 1 < currentStep ? "bg-emerald-500" : 
                                idx + 1 === currentStep ? "bg-accent-primary animate-pulse" : 
                                "bg-white/5"
                            )}
                        />
                    ))}
                </div>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 overflow-y-auto no-scrollbar p-6 space-y-8">
                {/* View Toggles */}
                {currentStep >= 7 && (
                    <div className="flex p-1 bg-white/5 border border-white/10 rounded-2xl w-fit mx-auto sticky top-0 z-10 backdrop-blur-md">
                        <button 
                            onClick={() => setActiveTab('preview')}
                            className={cn(
                                "flex items-center gap-2 px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all",
                                activeTab === 'preview' ? "bg-white/10 text-white shadow-lg" : "text-text-muted hover:text-white"
                            )}
                        >
                            Preview
                        </button>
                        <button 
                            onClick={() => setActiveTab('analysis')}
                            className={cn(
                                "flex items-center gap-2 px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all",
                                activeTab === 'analysis' ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/20" : "text-text-muted hover:text-white"
                            )}
                        >
                            <Target className="w-3.5 h-3.5" /> Market Analysis
                        </button>
                        <button 
                            onClick={() => setActiveTab('editor')}
                            className={cn(
                                "flex items-center gap-2 px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all",
                                activeTab === 'editor' ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/20" : "text-text-muted hover:text-white"
                            )}
                        >
                            Builder
                        </button>
                    </div>
                )}

                {activeTab === 'preview' && (
                    <div className="max-w-[800px] mx-auto rounded-2xl overflow-hidden shadow-2xl border border-white/5 bg-white scale-95 origin-top transition-transform duration-500">
                        <CVPreview data={cvData} />
                    </div>
                )}

                {activeTab === 'analysis' && (
                    <div className="max-w-[1000px] mx-auto space-y-8 animate-in fade-in zoom-in duration-500">
                        {optimizationRes ? (
                            <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
                                <div className="lg:col-span-3 space-y-8">
                                    <ATSScoreDashboard data={{
                                        total_score: optimizationRes.ats_score,
                                        breakdown: optimizationRes.breakdown,
                                        issues: optimizationRes.suggestions.map(s => ({
                                            category: s.category,
                                            severity: s.priority === 'critical' ? 'high' : s.priority === 'important' ? 'medium' : 'low',
                                            message: s.title,
                                            suggestion: s.description
                                        })),
                                        benchmark_avg: 72
                                    }} />
                                </div>
                                <div className="lg:col-span-2">
                                    <OptimizationPanel 
                                        suggestions={optimizationRes.suggestions} 
                                        onApply={handleApplySuggestion}
                                        isLoading={isOptimizing}
                                    />
                                </div>
                            </div>
                        ) : (
                            <div className="bg-slate-900/60 border border-white/5 rounded-3xl p-12 text-center space-y-6">
                                <div className="w-20 h-20 bg-indigo-500/10 rounded-full flex items-center justify-center mx-auto border border-indigo-500/20">
                                    <Target className="w-10 h-10 text-indigo-400" />
                                </div>
                                <div className="max-w-md mx-auto space-y-2">
                                    <h3 className="text-xl font-black text-white uppercase tracking-tighter">ATS & Market Optimization</h3>
                                    <p className="text-slate-400 text-sm">Paste the Job Description for the role you're targeting to get professional AI suggestions and ATS scoring.</p>
                                </div>
                                <div className="max-w-xl mx-auto space-y-4">
                                    <textarea 
                                        value={jdText}
                                        onChange={(e) => setJdText(e.target.value)}
                                        placeholder="Paste Job Description text here..."
                                        className="w-full bg-slate-950/50 border border-white/10 rounded-2xl p-6 text-sm text-slate-300 outline-none focus:border-indigo-500 transition-all min-h-[200px] resize-none"
                                    />
                                    <button 
                                        onClick={handleOptimize}
                                        disabled={!jdText.trim() || isOptimizing}
                                        className="w-full py-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-2xl text-sm font-black uppercase tracking-[0.2em] shadow-xl shadow-indigo-500/20 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                                    >
                                        {isOptimizing ? <><RefreshCw className="w-5 h-5 animate-spin" /> ANALYZING...</> : <><Sparkles className="w-5 h-5" /> REVEAL OPTIMIZATION PATH</>}
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'editor' && (
                    <div className="max-w-[800px] mx-auto space-y-4 animate-in fade-in zoom-in duration-500">
                        <CVSectionEditor 
                            title="Personal Information" 
                            sectionType="personal_info" 
                            initialData={cvData.personal_info} 
                            onSave={(data) => handleSectionUpdate('personal_info', null, data)} 
                        />
                        <CVSectionEditor 
                            title="Professional Summary" 
                            sectionType="summary" 
                            initialData={cvData.summary || ""} 
                            onSave={(data) => handleSectionUpdate('summary', null, data)} 
                        />
                        {cvData.experience.map((exp, idx) => (
                            <CVSectionEditor 
                                key={`exp-${idx}`}
                                title={`Experience: ${exp.company}`} 
                                sectionType="experience" 
                                initialData={exp} 
                                onSave={(data) => handleSectionUpdate('experience', idx, data)} 
                            />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

const RefreshCw: React.FC<{ className?: string }> = ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/></svg>
);

export default CVBuilderView;
