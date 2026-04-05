import React, { memo, useState, useRef, useEffect } from 'react';
import { User, Sparkles, Copy, Check, Edit3, X, CornerDownLeft, ThumbsUp, ThumbsDown, Star } from 'lucide-react';
import { Source } from '../../services/api';
import { cn } from '../../lib/utils';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Badge } from '../ui/Badge';

interface MessageItemProps {
    role: 'user' | 'assistant';
    content: string;
    sources?: Source[];
    onEdit?: (newContent: string) => void;
    onShowFeedback?: () => void;
    onSentiment?: (sentiment: 'positive' | 'negative') => void;
    isStreaming?: boolean;
    onOpenTool?: (tool: string) => void;
    onQuickAction?: (action: string) => void;
    isPersonalized?: boolean;
}

/** Icon-only button with a CSS tooltip that appears on hover */
const IconBtn: React.FC<{
    onClick: () => void;
    tip: string;
    tipSide?: 'top' | 'bottom';
    children: React.ReactNode;
}> = ({ onClick, tip, tipSide = 'top', children }) => (
    <div className="relative group/tip">
        <button
            onClick={onClick}
            className="flex items-center justify-center w-7 h-7 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-hover transition-all"
        >
            {children}
        </button>
        <div className={cn(
            "absolute left-1/2 -translate-x-1/2 px-2 py-0.5 text-[11px] bg-surface border border-white/10 rounded-md whitespace-nowrap opacity-0 group-hover/tip:opacity-100 pointer-events-none transition-opacity shadow-lg z-50",
            tipSide === 'top' ? "bottom-full mb-1.5" : "top-full mt-1.5"
        )}>
            {tip}
        </div>
    </div>
);

const MessageItem: React.FC<MessageItemProps> = ({ role, content, sources, onEdit, onShowFeedback, onSentiment, isStreaming, onOpenTool, onQuickAction, isPersonalized }) => {
    const [copied, setCopied] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [editValue, setEditValue] = useState(content);
    const [sentiment, setSentiment] = useState<'positive' | 'negative' | null>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        if (isEditing && textareaRef.current) {
            textareaRef.current.focus();
            textareaRef.current.setSelectionRange(editValue.length, editValue.length);
            autoResize();
        }
    }, [isEditing]);

    const autoResize = () => {
        const el = textareaRef.current;
        if (!el) return;
        el.style.height = 'auto';
        el.style.height = el.scrollHeight + 'px';
    };

    const handleCopy = () => {
        navigator.clipboard.writeText(content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleEditSave = () => {
        if (!editValue.trim() || editValue === content) {
            setIsEditing(false);
            setEditValue(content);
            return;
        }
        onEdit?.(editValue.trim());
        setIsEditing(false);
    };

    const handleEditCancel = () => {
        setIsEditing(false);
        setEditValue(content);
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Escape') handleEditCancel();
    };

    const handleSentiment = (s: 'positive' | 'negative') => {
        setSentiment(s);
        onSentiment?.(s);
    };

    const isCvRelated = content.toLowerCase().includes('cv') || 
                        content.toLowerCase().includes('sơ yếu lý lịch') || 
                        content.toLowerCase().includes('optimized') || 
                        content.toLowerCase().includes('generated');

    const shouldParseStructured = role === 'assistant' && !isStreaming;
    const ctaMatches = shouldParseStructured ? Array.from(content.matchAll(/\[TOOL_CTA:([^|\]]+)\|([^\]]+)\]/g)) : [];
    const checklistMatches = shouldParseStructured ? Array.from(content.matchAll(/\[TOOL_CHECKLIST:([^|\]]+)\|([^\]]+)\]/g)) : [];
    const quickMatches = shouldParseStructured ? Array.from(content.matchAll(/\[TOOL_QUICK_ACTION:([^|\]]+)\|([^\]]+)\]/g)) : [];

    const cleanContent = shouldParseStructured
        ? content
            .replace(/\[TOOL_CTA:[^\]]+\]\n?/g, '')
            .replace(/\[TOOL_CHECKLIST:[^\]]+\]\n?/g, '')
            .replace(/\[TOOL_QUICK_ACTION:[^\]]+\]\n?/g, '')
            .trim()
        : content;

    const renderInlineBreaks = (children: React.ReactNode): React.ReactNode =>
        React.Children.toArray(children).flatMap((child) => {
            if (typeof child === 'string') {
                const parts = child
                    .replace(/&nbsp;/gi, ' ')
                    .split(/<br\s*\/?>/gi);
                if (parts.length === 1) return parts[0];
                return parts.flatMap((part, idx) => (idx === 0 ? [part] : [<br key={`br-${idx}`} />, part]));
            }
            return child;
        });

    return (
        <div className={cn(
            "group flex gap-3 sm:gap-4 py-5 animate-in fade-in slide-in-from-bottom-2 duration-700 fill-mode-both",
            role === 'user' ? "flex-row-reverse" : "flex-row"
        )}>
            {/* Avatar */}
            <div className={cn(
                "relative w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center mt-0.5 transition-all duration-300",
                role === 'user'
                    ? "bg-surface/60 text-text-secondary"
                    : "bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/25",
                role === 'assistant' && isStreaming && "animate-ai-thinking"
            )}>
                {role === 'user'
                    ? <User className="w-4 h-4" strokeWidth={1.5} />
                    : <Sparkles className="w-4 h-4 fill-current" />}
                {role === 'assistant' && isPersonalized !== undefined && (
                    <span
                        className={cn(
                            "absolute -bottom-1 -right-1 w-2.5 h-2.5 rounded-full border border-canvas",
                            isPersonalized ? "bg-emerald-400" : "bg-amber-400"
                        )}
                        title={isPersonalized ? 'Đã biết về bạn' : 'Khách mới'}
                    />
                )}
            </div>

            {/* Content area */}
            <div className={cn(
                "flex-1 min-w-0 flex flex-col",
                role === 'user' ? "items-end" : "items-start"
            )}>
                {isEditing ? (
                    /* ── Edit mode ── */
                    <div className="w-full max-w-[85%] flex flex-col gap-2">
                        <textarea
                            ref={textareaRef}
                            value={editValue}
                            onChange={(e) => { setEditValue(e.target.value); autoResize(); }}
                            onKeyDown={handleKeyDown}
                            className="w-full bg-surface/60 border border-accent-primary/40 text-text-primary rounded-2xl px-5 py-4 outline-none resize-none text-[15px] leading-relaxed caret-accent-primary prompt-textarea"
                            style={{ minHeight: '56px' }}
                        />
                        <div className="flex items-center gap-2 justify-end">
                            <button
                                onClick={handleEditCancel}
                                className="flex items-center gap-1.5 h-8 px-3 rounded-full text-[12px] font-medium text-text-secondary hover:text-text-primary hover:bg-surface-hover transition-all"
                            >
                                <X size={13} /> Cancel
                            </button>
                            <button
                                onClick={handleEditSave}
                                disabled={!editValue.trim()}
                                className="flex items-center gap-1.5 h-8 px-4 rounded-full text-[12px] font-semibold bg-accent-primary text-white hover:opacity-90 transition-all disabled:opacity-40"
                            >
                                <CornerDownLeft size={13} /> Send
                            </button>
                        </div>
                    </div>
                ) : role === 'user' ? (
                    /* ── User bubble — icons inline to the left ── */
                    <div className="flex items-start gap-2">
                        {/* Action icons — same row, left of bubble */}
                        <div className="flex gap-0.5 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity duration-200 mt-2">
                            <IconBtn onClick={handleCopy} tip={copied ? 'Copied!' : 'Copy'}>
                                {copied
                                    ? <Check className="w-3.5 h-3.5 text-emerald-500" />
                                    : <Copy className="w-3.5 h-3.5" />}
                            </IconBtn>
                            {onEdit && (
                                <IconBtn onClick={() => { setEditValue(content); setIsEditing(true); }} tip="Edit">
                                    <Edit3 className="w-3.5 h-3.5" />
                                </IconBtn>
                            )}
                        </div>
                        {/* Bubble */}
                        <div className="bg-surface px-5 py-3.5 rounded-2xl rounded-tr-md text-text-primary shadow-sm max-w-[80ch]">
                            <div className="markdown-content text-[15px]">
                                <ReactMarkdown
                                    remarkPlugins={[remarkGfm]}
                                    components={{
                                        td: ({ children, ...props }) => <td {...props}>{renderInlineBreaks(children)}</td>,
                                        th: ({ children, ...props }) => <th {...props}>{renderInlineBreaks(children)}</th>,
                                    }}
                                >
                                    {content}
                                </ReactMarkdown>
                            </div>
                        </div>
                    </div>
                ) : (
                    /* ── Assistant message — icons inline below content ── */
                    <div className="w-full">
                        <div className={cn(
                            "markdown-content text-text-primary min-h-[24px]",
                            !content && "opacity-40"
                        )}>
                            {!cleanContent ? (
                                <div className="flex gap-2 py-1">
                                    <div className="h-2 bg-text-primary rounded-full w-24 animate-pulse"></div>
                                    <div className="h-2 bg-text-primary rounded-full w-12 animate-pulse opacity-50"></div>
                                </div>
                            ) : (
                                <ReactMarkdown
                                    remarkPlugins={isStreaming ? [] : [remarkGfm]}
                                    components={{
                                        td: ({ children, ...props }) => <td {...props}>{renderInlineBreaks(children)}</td>,
                                        th: ({ children, ...props }) => <th {...props}>{renderInlineBreaks(children)}</th>,
                                    }}
                                >
                                    {cleanContent}
                                </ReactMarkdown>
                            )}
                        </div>

                        {role === 'assistant' && !isStreaming && (
                            <div className="mt-3 space-y-2">
                                {ctaMatches.map((m, idx) => (
                                    <button
                                        key={`cta-${idx}`}
                                        onClick={() => onOpenTool?.(m[1])}
                                        className="inline-flex items-center rounded-xl bg-accent-primary/15 hover:bg-accent-primary text-accent-primary hover:text-white px-4 py-2 text-sm font-bold transition-all"
                                    >
                                        {m[2]}
                                    </button>
                                ))}

                                {checklistMatches.map((m, idx) => (
                                    <div key={`check-${idx}`} className="rounded-xl bg-secondary/30 border border-white/10 p-3">
                                        <p className="text-xs font-bold uppercase tracking-wider text-text-secondary mb-2">Checklist</p>
                                        <ul className="space-y-1.5">
                                            {m[2].split(';').map((step, stepIdx) => (
                                                <li key={stepIdx} className="text-sm text-text-primary">• {step.trim()}</li>
                                            ))}
                                        </ul>
                                    </div>
                                ))}

                                {quickMatches.length > 0 && (
                                    <div className="flex gap-2 flex-wrap">
                                        {quickMatches.map((m, idx) => (
                                            <button
                                                key={`quick-${idx}`}
                                                onClick={() => onQuickAction?.(m[1])}
                                                className="inline-flex items-center rounded-xl bg-surface hover:bg-surface-hover border border-white/10 px-3 py-2 text-sm font-medium transition-all"
                                            >
                                                {m[2]}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Action icons — below content, same left edge */}
                        <div className="flex items-center gap-0.5 mt-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                            <IconBtn onClick={handleCopy} tip={copied ? 'Copied!' : 'Copy'} tipSide="bottom">
                                {copied
                                    ? <Check className="w-3.5 h-3.5 text-emerald-500" />
                                    : <Copy className="w-3.5 h-3.5" />}
                            </IconBtn>
                            
                            <IconBtn onClick={() => handleSentiment('positive')} tip="Helpful" tipSide="bottom">
                                <ThumbsUp className={cn("w-3.5 h-3.5", sentiment === 'positive' && "fill-emerald-500 text-emerald-500")} />
                            </IconBtn>
                            
                            <IconBtn onClick={() => handleSentiment('negative')} tip="Not helpful" tipSide="bottom">
                                <ThumbsDown className={cn("w-3.5 h-3.5", sentiment === 'negative' && "fill-rose-500 text-rose-500")} />
                            </IconBtn>

                            {isCvRelated && onShowFeedback && (
                                <IconBtn onClick={onShowFeedback} tip="Rate CV Quality" tipSide="bottom">
                                    <Star className="w-3.5 h-3.5 text-amber-400" />
                                </IconBtn>
                            )}
                        </div>

                        {/* Sources */}
                        {sources && sources.length > 0 && (
                            <div className="flex flex-wrap gap-2 pt-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                                {sources.map((s, i) => (
                                    <Badge key={i} variant="secondary" className="cursor-default normal-case tracking-normal px-3 py-1 gap-2">
                                        <span className="w-1 h-1 rounded-full bg-accent-secondary" />
                                        {s.title}
                                    </Badge>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

const areMessageItemPropsEqual = (prev: MessageItemProps, next: MessageItemProps) => {
    if (prev.role !== next.role) return false;
    if (prev.content !== next.content) return false;
    if (prev.isStreaming !== next.isStreaming) return false;
    if (prev.isPersonalized !== next.isPersonalized) return false;

    const prevSources = prev.sources || [];
    const nextSources = next.sources || [];
    if (prevSources.length !== nextSources.length) return false;
    for (let i = 0; i < prevSources.length; i++) {
        if (
            prevSources[i].title !== nextSources[i].title ||
            prevSources[i].type !== nextSources[i].type ||
            prevSources[i].relevance !== nextSources[i].relevance
        ) return false;
    }

    // Intentionally ignore callback identity changes to reduce rerenders.
    return true;
};

export default memo(MessageItem, areMessageItemPropsEqual);
