import React, { useState, useRef, useCallback, useEffect } from 'react';
import { X, Sparkles, FileText, Target, LayoutGrid, ClipboardList, Network, GripVertical, BarChart3, Shield } from 'lucide-react';
import CVBuilderView from '../features/CVBuilderView';
import CVUpload from '../features/CVUpload';
import SkillMatch from '../features/SkillMatch';
import CareerPath from '../features/CareerPath';
import JDUpload from '../features/JDUpload';
import KnowledgeGraph from '../features/KnowledgeGraph';
import MarketDashboard from '../features/MarketDashboard';
import ATSScoreDashboard from '../features/ATSScoreDashboard';
import AdminPortal from '../features/AdminPortal';
import { cn } from '../../lib/utils';
import { CVData } from '../../services/api';

interface ArtifactPanelProps {
    isOpen: boolean;
    onClose: () => void;
    type: 'builder' | 'upload' | 'match' | 'career' | 'ats' | 'jd' | 'graph' | 'market' | 'admin' | null;
    sessionId: number | null;
    // Props for Builder
    cvData?: CVData;
    currentStep?: number;
    onUpdateCvData?: (data: CVData) => void;
    onUpdateStep?: (step: number) => void;
    userId?: string | null;
}

const MIN_PANEL_WIDTH = 380;
const MAX_PANEL_RATIO = 0.7; // Panel can't exceed 70% of viewport
const DEFAULT_PANEL_RATIO = 0.45; // 45% default

const ArtifactPanel: React.FC<ArtifactPanelProps> = ({
    isOpen, onClose, type, sessionId, cvData, currentStep, onUpdateCvData, onUpdateStep, userId
}) => {
    const [panelWidth, setPanelWidth] = useState<number>(() => {
        const saved = localStorage.getItem('artifactPanelWidth');
        return saved ? parseInt(saved, 10) : Math.round(window.innerWidth * DEFAULT_PANEL_RATIO);
    });
    const isDragging = useRef(false);
    const panelRef = useRef<HTMLDivElement>(null);

    // Persist width
    useEffect(() => {
        localStorage.setItem('artifactPanelWidth', String(panelWidth));
    }, [panelWidth]);

    // Clamp on window resize
    useEffect(() => {
        const handleResize = () => {
            setPanelWidth(w => Math.max(MIN_PANEL_WIDTH, Math.min(window.innerWidth * MAX_PANEL_RATIO, w)));
        };
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    const handleMouseDown = useCallback((e: React.MouseEvent) => {
        e.preventDefault();
        isDragging.current = true;
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';

        const handleMouseMove = (e: MouseEvent) => {
            if (!isDragging.current) return;
            const newWidth = window.innerWidth - e.clientX;
            const clamped = Math.max(MIN_PANEL_WIDTH, Math.min(window.innerWidth * MAX_PANEL_RATIO, newWidth));
            setPanelWidth(clamped);
        };

        const handleMouseUp = () => {
            isDragging.current = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
    }, []);

    if (!isOpen || !type) return null;

    const getTitle = () => {
        switch (type) {
            case 'builder': return 'CV AI Builder';
            case 'upload': return 'Data Ingestion';
            case 'match': return 'Skill Matrix';
            case 'career': return 'Career Paths';
            case 'ats': return 'ATS Score';
            case 'jd': return 'JD Analysis';
            case 'graph': return 'Knowledge Graph';
            case 'market': return 'Market Insights';
            case 'admin': return 'Admin Dashboard';
            default: return 'Assistant Tool';
        }
    };

    const getIcon = () => {
        switch (type) {
            case 'builder': return <Sparkles className="w-5 h-5 text-accent-primary" />;
            case 'upload': return <FileText className="w-5 h-5 text-accent-secondary" />;
            case 'match': return <Target className="w-5 h-5 text-accent-primary" />;
            case 'career': return <LayoutGrid className="w-5 h-5 text-accent-secondary" />;
            case 'ats': return <BarChart3 className="w-5 h-5 text-orange-400" />;
            case 'jd': return <ClipboardList className="w-5 h-5 text-teal-400" />;
            case 'graph': return <Network className="w-5 h-5 text-cyan-400" />;
            case 'market': return <BarChart3 className="w-5 h-5 text-indigo-400" />;
            case 'admin': return <Shield className="w-5 h-5 text-emerald-500" />;
            default: return null;
        }
    };

    return (
        <>
            {/* ── Resize Handle ── */}
            <div
                onMouseDown={handleMouseDown}
                className="hidden lg:flex w-[6px] flex-shrink-0 cursor-col-resize items-center justify-center group relative z-50 select-none"
            >
                <div className="w-[2px] h-full bg-white/[0.04] group-hover:bg-accent-primary/30 transition-colors duration-200" />
                <div className="absolute inset-y-0 flex items-center justify-center pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                    <div className="w-5 h-10 rounded-full bg-surface/90 border border-white/10 flex items-center justify-center shadow-lg backdrop-blur-sm">
                        <GripVertical className="w-3 h-3 text-text-muted" />
                    </div>
                </div>
            </div>

            {/* ── Panel ── */}
            <div
                ref={panelRef}
                style={{ width: panelWidth }}
                className="flex-shrink-0 bg-canvas z-40 shadow-2xl flex flex-col h-full border-l border-white/[0.04] overflow-hidden max-lg:!w-[calc(100%-68px)] max-lg:fixed max-lg:inset-y-0 max-lg:right-0"
            >
                <header className="h-20 flex items-center justify-between px-8 border-b border-white/[0.05] bg-canvas/40 backdrop-blur-3xl sticky top-0 z-30 flex-shrink-0">
                    <div className="flex items-center gap-4 group">
                        <div className="w-12 h-12 rounded-2xl bg-accent-primary/10 border border-accent-primary/20 flex items-center justify-center transition-all group-hover:scale-110 group-hover:rotate-6">
                            {getIcon()}
                        </div>
                        <div>
                            <h2 className="text-[11px] font-black uppercase tracking-[0.3em] text-accent-primary font-outfit mb-0.5">Assistant Tool</h2>
                            <h3 className="text-lg font-bold text-text-primary tracking-tight">{getTitle()}</h3>
                        </div>
                    </div>
                    <button 
                        onClick={onClose}
                        className="w-10 h-10 flex items-center justify-center rounded-xl bg-surface hover:bg-accent-primary hover:text-white transition-all text-text-muted border border-white/[0.05] shadow-sm hover:shadow-lg hover:shadow-accent-primary/20"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </header>

                <div className="flex-1 overflow-y-auto no-scrollbar">
                    {type === 'builder' && sessionId && cvData && currentStep !== undefined && (
                        <CVBuilderView
                            sessionId={sessionId}
                            initialCvData={cvData}
                            initialStep={currentStep}
                            onDataSync={onUpdateCvData}
                            onStepSync={onUpdateStep}
                            isArtifactMode={true}
                            userId={userId}
                        />
                    )}
                    {type === 'upload' && <CVUpload onParsedCvData={onUpdateCvData} />}
                    {type === 'match' && <SkillMatch />}
                    {type === 'career' && <CareerPath />}
                    {type === 'ats' && (
                        <ATSScoreDashboard
                            data={{
                                total_score: 68,
                                breakdown: {
                                    keyword_match: 62,
                                    format_quality: 74,
                                    experience_alignment: 69,
                                    skills_alignment: 67
                                },
                                issues: [
                                    {
                                        category: 'keyword_match',
                                        severity: 'high',
                                        message: 'Thiếu từ khóa theo JD',
                                        suggestion: 'Bổ sung các từ khóa kỹ năng trùng với JD ở phần Experience và Skills.'
                                    },
                                    {
                                        category: 'experience_alignment',
                                        severity: 'medium',
                                        message: 'Mô tả kinh nghiệm chưa đủ định lượng',
                                        suggestion: 'Thêm số liệu tác động (%, thời gian, quy mô) cho mỗi bullet.'
                                    }
                                ],
                                benchmark_avg: 63
                            }}
                        />
                    )}
                    {type === 'jd' && <JDUpload />}
                    {type === 'graph' && <KnowledgeGraph />}
                    {type === 'market' && <MarketDashboard />}
                </div>
            </div>
        </>
    );
};

export default ArtifactPanel;
