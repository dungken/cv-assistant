import React, { useState, useRef, useEffect } from 'react';
import {
    Plus,
    Mic,
    Send,
    Briefcase,
    LayoutGrid,
    FileText,
    Search,
    Zap,
    PenTool,
    Mail,
    TrendingUp,
    SlidersHorizontal,
    ChevronDown,
    Check,
    Cpu,
    Cloud,
    ClipboardList,
    Network,
    Target,
    BarChart3,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useTranslation } from 'react-i18next';

interface PromptBarProps {
    isLoading: boolean;
    onSend: (message: string) => void;
    showChips: boolean;
    onModeSelect?: (mode: string) => void;
    activeTool?: string | null; // US-26: currently active tool type
}

const MODELS = [
    { id: 'ollama', name: 'qwen2.5:3b', label: 'Ollama Local', icon: <Cpu size={13} /> },
    { id: 'groq', name: 'llama-3.3-70b', label: 'Groq Cloud', icon: <Cloud size={13} /> },
];

// US-26: Tool-specific suggestion chips when a tool is active
const TOOL_SUGGESTIONS: Record<string, { icon: React.ReactNode; labelKey: string; message: string }[]> = {
    match: [
        { icon: <Target size={14} className="text-emerald-400" />, labelKey: 'tool_context.suggestions.match_backend', message: 'Mình muốn apply vị trí Backend Developer, phân tích kỹ năng giúp mình' },
        { icon: <Search size={14} className="text-emerald-400" />, labelKey: 'tool_context.suggestions.match_frontend', message: 'Phân tích kỹ năng React và TypeScript của mình so với thị trường' },
        { icon: <Zap size={14} className="text-emerald-400" />, labelKey: 'tool_context.suggestions.match_gap', message: 'Mình còn thiếu kỹ năng gì để apply Senior Developer?' },
    ],
    career: [
        { icon: <TrendingUp size={14} className="text-amber-400" />, labelKey: 'tool_context.suggestions.career_goal', message: 'Mình đang là Junior Developer, muốn lên Senior trong 3 năm' },
        { icon: <Briefcase size={14} className="text-amber-400" />, labelKey: 'tool_context.suggestions.career_transition', message: 'Mình muốn chuyển từ Backend sang DevOps, cần chuẩn bị gì?' },
        { icon: <Zap size={14} className="text-amber-400" />, labelKey: 'tool_context.suggestions.career_skills', message: 'Kỹ năng nào quan trọng nhất để thăng tiến trong ngành IT?' },
    ],
    upload: [
        { icon: <FileText size={14} className="text-sky-400" />, labelKey: 'tool_context.suggestions.upload_improve', message: 'Mình vừa upload CV, giúp mình cải thiện nó' },
        { icon: <Search size={14} className="text-sky-400" />, labelKey: 'tool_context.suggestions.upload_compare', message: 'So sánh CV của mình với JD mà mình muốn apply' },
        { icon: <Zap size={14} className="text-sky-400" />, labelKey: 'tool_context.suggestions.upload_ats', message: 'CV của mình đạt bao nhiêu điểm ATS?' },
    ],
    jd: [
        { icon: <ClipboardList size={14} className="text-teal-400" />, labelKey: 'tool_context.suggestions.jd_analyze', message: 'Phân tích JD này và cho mình biết yêu cầu chính' },
        { icon: <Search size={14} className="text-teal-400" />, labelKey: 'tool_context.suggestions.jd_match', message: 'So sánh yêu cầu JD này với kỹ năng của mình' },
        { icon: <Zap size={14} className="text-teal-400" />, labelKey: 'tool_context.suggestions.jd_tips', message: 'Cho mình tips để CV phù hợp hơn với JD này' },
    ],
    graph: [
        { icon: <Network size={14} className="text-cyan-400" />, labelKey: 'tool_context.suggestions.graph_explore', message: 'Cho mình xem các kỹ năng liên quan đến React' },
        { icon: <TrendingUp size={14} className="text-cyan-400" />, labelKey: 'tool_context.suggestions.graph_path', message: 'Lộ trình học từ JavaScript đến Full-stack Developer' },
    ],
    market: [
        { icon: <LayoutGrid size={14} className="text-indigo-400" />, labelKey: 'tool_context.suggestions.market_trends', message: 'Kỹ năng nào đang hot nhất trên thị trường IT hiện tại?' },
        { icon: <TrendingUp size={14} className="text-indigo-400" />, labelKey: 'tool_context.suggestions.market_salary', message: 'Mức lương trung bình cho Backend Developer ở Việt Nam?' },
    ],
    ats: [
        { icon: <BarChart3 size={14} className="text-orange-400" />, labelKey: 'tool_context.suggestions.upload_ats', message: 'Mình muốn chấm điểm ATS cho CV này' },
        { icon: <ClipboardList size={14} className="text-orange-400" />, labelKey: 'tool_context.suggestions.jd_analyze', message: 'Mình sẽ dán JD để so sánh ATS' },
    ],
};

// US-26: Tool display info (icon, label key, color)
const TOOL_INFO: Record<string, { icon: React.ReactNode; labelKey: string }> = {
    match: { icon: <Search size={14} />, labelKey: 'prompt.match_label' },
    career: { icon: <Zap size={14} />, labelKey: 'prompt.career_label' },
    upload: { icon: <FileText size={14} />, labelKey: 'prompt.upload_label' },
    jd: { icon: <ClipboardList size={14} />, labelKey: 'prompt.jd_label' },
    graph: { icon: <Network size={14} />, labelKey: 'prompt.graph_label' },
    market: { icon: <LayoutGrid size={14} />, labelKey: 'prompt.market_label' },
    ats: { icon: <BarChart3 size={14} />, labelKey: 'prompt.ats_label' },
};

const PromptBar: React.FC<PromptBarProps> = ({
    isLoading, onSend, showChips, onModeSelect, activeTool
}) => {
    const { t } = useTranslation();
    const [input, setInput] = useState('');
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [isModelOpen, setIsModelOpen] = useState(false);
    const [selectedModel, setSelectedModel] = useState(MODELS[0]);

    // Single ref wrapping trigger buttons + popup — fixes double-click toggle bug
    const menuContainerRef = useRef<HTMLDivElement>(null);
    const modelContainerRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (menuContainerRef.current && !menuContainerRef.current.contains(event.target as Node)) {
                setIsMenuOpen(false);
            }
            if (modelContainerRef.current && !modelContainerRef.current.contains(event.target as Node)) {
                setIsModelOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Auto-resize textarea
    useEffect(() => {
        const el = textareaRef.current;
        if (!el) return;
        el.style.height = 'auto';
        el.style.height = Math.min(el.scrollHeight, 200) + 'px';
    }, [input]);

    const menuItems = [
        { icon: <PenTool size={16} />, label: t('prompt.builder_label'), desc: t('prompt.builder_desc'), action: () => onModeSelect?.('builder') },
        { icon: <FileText size={16} />, label: t('prompt.upload_label'), desc: t('prompt.upload_desc'), action: () => onModeSelect?.('upload') },
        { icon: <ClipboardList size={16} />, label: t('prompt.jd_label'), desc: t('prompt.jd_desc'), action: () => onModeSelect?.('jd') },
        { icon: <BarChart3 size={16} />, label: t('prompt.ats_label'), desc: t('prompt.ats_desc'), action: () => onModeSelect?.('ats') },
        { icon: <Search size={16} />, label: t('prompt.match_label'), desc: t('prompt.match_desc'), action: () => onModeSelect?.('match') },
        { icon: <Zap size={16} />, label: t('prompt.career_label'), desc: t('prompt.career_desc'), action: () => onModeSelect?.('career') },
        { icon: <Network size={16} />, label: t('prompt.graph_label'), desc: t('prompt.graph_desc'), action: () => onModeSelect?.('graph') },
    ];

    const handleSend = (override?: string) => {
        const text = override || input;
        if (!text.trim() || isLoading) return;
        onSend(text);
        if (!override) setInput('');
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const suggestionChips = [
        { icon: <PenTool size={14} className="text-violet-400" />, label: t('prompt.chips.build'), action: () => onModeSelect?.('builder') },
        { icon: <FileText size={14} className="text-sky-400" />, label: t('prompt.chips.upload'), action: () => onModeSelect?.('upload') },
        { icon: <ClipboardList size={14} className="text-teal-400" />, label: t('prompt.chips.jd'), action: () => onModeSelect?.('jd') },
        { icon: <Search size={14} className="text-emerald-400" />, label: t('prompt.chips.match'), action: () => onModeSelect?.('match') },
        { icon: <Zap size={14} className="text-amber-400" />, label: t('prompt.chips.career'), action: () => onModeSelect?.('career') },
        { icon: <Network size={14} className="text-cyan-400" />, label: t('prompt.chips.graph'), action: () => onModeSelect?.('graph') },
        { icon: <Briefcase size={14} className="text-rose-400" />, label: t('prompt.chips.interview'), action: () => handleSend("Give me effective tips to prepare for a job interview") },
        { icon: <TrendingUp size={14} className="text-teal-400" />, label: t('prompt.chips.trends'), action: () => handleSend("What are the current IT job market trends and in-demand skills?") },
        { icon: <Mail size={14} className="text-orange-400" />, label: t('prompt.chips.cover_letter'), action: () => handleSend("Help me write a professional cover letter for a software engineering position") },
        { icon: <LayoutGrid size={14} className="text-pink-400" />, label: t('prompt.chips.compare'), action: () => handleSend("Compare Software Engineer vs Data Engineer roles: skills, salary, and career growth") },
    ];

    // US-26: Active tool info for banner
    const activeToolInfo = activeTool && activeTool !== 'builder' ? TOOL_INFO[activeTool] : null;
    const activeToolSuggestions = activeTool && activeTool !== 'builder' ? TOOL_SUGGESTIONS[activeTool] : null;

    return (
        <div className="w-full relative z-[100]">
            <div className="chat-stream-width">
                {/* US-26: Tool Context Banner */}
                {activeToolInfo && (
                    <div className="flex items-center gap-2 px-4 py-2 mb-2 rounded-2xl bg-accent-primary/8 border border-accent-primary/15 animate-in fade-in slide-in-from-bottom-1 duration-300">
                        <div className="flex items-center justify-center w-6 h-6 rounded-lg bg-accent-primary/15 text-accent-primary flex-shrink-0">
                            {activeToolInfo.icon}
                        </div>
                        <span className="text-[12px] font-semibold text-accent-primary tracking-wide font-outfit">
                            {t('tool_context.supporting')}: {t(activeToolInfo.labelKey)}
                        </span>
                        <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse ml-auto flex-shrink-0" />
                    </div>
                )}

                {/* Main Input Container */}
                <div className="prompt-wrapper">
                <div className="prompt-container rounded-3xl transition-all duration-200">
                    {/* Textarea row */}
                    <div className="px-6 pt-5 pb-3">
                        <textarea
                            ref={textareaRef}
                            rows={1}
                            className="w-full bg-transparent outline-none resize-none text-[16px] text-text-primary placeholder:text-text-secondary/40 caret-accent-primary font-outfit leading-relaxed prompt-textarea"
                            placeholder={t('prompt.placeholder')}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            disabled={isLoading}
                            style={{ minHeight: '28px', maxHeight: '200px' }}
                        />
                    </div>

                    {/* Action bar row */}
                    <div className="flex items-center justify-between px-4 pb-4 pt-1">
                        {/* Left: Tools menu */}
                        <div ref={menuContainerRef} className="relative flex items-center gap-1">
                            {/* Tools popup — above */}
                            {isMenuOpen && (
                                <div className="absolute bottom-full mb-3 left-0 w-64 bg-surface border border-white/8 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.35)] py-1.5 animate-in fade-in slide-in-from-bottom-2 duration-200 z-[999] overflow-hidden">
                                    {menuItems.map((item, idx) => (
                                        <button
                                            key={idx}
                                            onClick={() => { item.action(); setIsMenuOpen(false); }}
                                            className="w-full flex items-center gap-3 px-4 py-3 hover:bg-surface-hover transition-colors text-left group"
                                        >
                                            <div className="text-text-secondary group-hover:text-accent-primary transition-colors flex-shrink-0">
                                                {item.icon}
                                            </div>
                                            <div>
                                                <div className="text-[13px] font-semibold text-text-primary group-hover:text-accent-primary transition-colors font-outfit leading-none mb-0.5">
                                                    {item.label}
                                                </div>
                                                <div className="text-[11px] text-text-secondary/60">
                                                    {item.desc}
                                                </div>
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            )}

                            <button
                                onClick={() => setIsMenuOpen(prev => !prev)}
                                className={cn(
                                    "flex items-center justify-center w-9 h-9 rounded-full transition-all duration-200",
                                    "hover:bg-overlay/8 text-text-secondary hover:text-text-primary",
                                    isMenuOpen && "bg-overlay/10 text-text-primary rotate-45"
                                )}
                            >
                                <Plus size={20} strokeWidth={2} />
                            </button>
                            <button
                                onClick={() => setIsMenuOpen(prev => !prev)}
                                className={cn(
                                    "flex items-center gap-1.5 h-9 px-3 rounded-full transition-all duration-200",
                                    "hover:bg-overlay/8 text-text-secondary hover:text-text-primary text-[13px] font-medium",
                                    isMenuOpen && "bg-overlay/10 text-text-primary"
                                )}
                            >
                                <SlidersHorizontal size={15} strokeWidth={2} />
                                {t('prompt.tools')}
                            </button>
                        </div>

                        {/* Right: Model selector + Mic + Send */}
                        <div className="flex items-center gap-1">
                            {/* Model selector */}
                            <div ref={modelContainerRef} className="relative">
                                {isModelOpen && (
                                    <div className="absolute bottom-full mb-3 right-0 w-52 bg-surface border border-white/8 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.35)] py-1.5 animate-in fade-in slide-in-from-bottom-2 duration-200 z-[999] overflow-hidden">
                                        {MODELS.map((model) => (
                                            <button
                                                key={model.id}
                                                onClick={() => { setSelectedModel(model); setIsModelOpen(false); }}
                                                className="w-full flex items-center justify-between gap-3 px-4 py-3 hover:bg-surface-hover transition-colors text-left group"
                                            >
                                                <div className="flex items-center gap-2.5">
                                                    <span className="text-text-secondary group-hover:text-accent-primary transition-colors">
                                                        {model.icon}
                                                    </span>
                                                    <div>
                                                        <div className="text-[13px] font-semibold text-text-primary font-outfit leading-none mb-0.5">
                                                            {model.name}
                                                        </div>
                                                        <div className="text-[11px] text-text-secondary/60">
                                                            {model.label}
                                                        </div>
                                                    </div>
                                                </div>
                                                {selectedModel.id === model.id && (
                                                    <Check size={14} className="text-accent-primary flex-shrink-0" />
                                                )}
                                            </button>
                                        ))}
                                    </div>
                                )}
                                <button
                                    onClick={() => setIsModelOpen(prev => !prev)}
                                    className={cn(
                                        "flex items-center gap-1.5 h-9 px-3 rounded-full transition-all duration-200",
                                        "hover:bg-overlay/8 text-text-secondary hover:text-text-primary text-[13px] font-medium",
                                        isModelOpen && "bg-overlay/10 text-text-primary"
                                    )}
                                >
                                    {selectedModel.icon}
                                    {selectedModel.name}
                                    <ChevronDown size={13} strokeWidth={2.5} className={cn("transition-transform duration-200", isModelOpen && "rotate-180")} />
                                </button>
                            </div>

                            <button className="flex items-center justify-center w-9 h-9 rounded-full hover:bg-overlay/8 text-text-secondary hover:text-text-primary transition-all duration-200">
                                <Mic size={18} strokeWidth={1.75} />
                            </button>
                            <button
                                onClick={() => handleSend()}
                                disabled={isLoading || !input.trim()}
                                className={cn(
                                    "flex items-center justify-center w-9 h-9 rounded-full transition-all duration-200",
                                    input.trim() && !isLoading
                                        ? "bg-accent-primary text-white hover:opacity-90 shadow-lg"
                                        : "text-text-secondary/30 cursor-default"
                                )}
                            >
                                <Send size={15} strokeWidth={2} />
                            </button>
                        </div>
                    </div>
                </div>
                </div>{/* end prompt-wrapper */}

                {/* Suggestion chips — below input */}
                {/* US-26: Show tool-specific suggestions when tool is active, default chips otherwise */}
                {activeToolSuggestions ? (
                    <div className="flex flex-wrap items-center justify-center gap-2 mt-4 animate-in fade-in slide-in-from-bottom-2 duration-500">
                        {activeToolSuggestions.map((chip, idx) => (
                            <button
                                key={`tool-${idx}`}
                                onClick={() => handleSend(chip.message)}
                                className="action-chip"
                            >
                                {chip.icon}
                                {t(chip.labelKey)}
                            </button>
                        ))}
                    </div>
                ) : showChips ? (
                    <div className="flex flex-wrap items-center justify-center gap-2 mt-5 animate-in fade-in slide-in-from-bottom-2 duration-700 delay-200">
                        {suggestionChips.map((chip, idx) => (
                            <button
                                key={idx}
                                onClick={chip.action}
                                className="action-chip"
                            >
                                {chip.icon}
                                {chip.label}
                            </button>
                        ))}
                    </div>
                ) : null}
            </div>
        </div>
    );
};

export default PromptBar;
