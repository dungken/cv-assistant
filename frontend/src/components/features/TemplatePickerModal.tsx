import React, { useState, useEffect } from 'react';
import { X, Check, Eye, Layout, Tag, Loader2 } from 'lucide-react';
import { templateApi } from '../../services/api';
import { cn } from '../../lib/utils';

interface TemplateItem {
    id: number;
    name: string;
    description?: string;
    category?: string;
    thumbnailUrl?: string;
    layoutHtml?: string;
    stylesCss?: string;
    usageCount?: number;
}

interface TemplatePickerModalProps {
    isOpen: boolean;
    currentTemplateId?: number | null;
    onClose: () => void;
    onConfirm: (template: TemplateItem) => void;
}

const TemplatePickerModal: React.FC<TemplatePickerModalProps> = ({
    isOpen,
    currentTemplateId,
    onClose,
    onConfirm,
}) => {
    const [templates, setTemplates] = useState<TemplateItem[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [selectedId, setSelectedId] = useState<number | null>(currentTemplateId || null);
    const [categoryFilter, setCategoryFilter] = useState<string>('all');
    const [previewTemplate, setPreviewTemplate] = useState<TemplateItem | null>(null);

    useEffect(() => {
        if (!isOpen) return;
        setIsLoading(true);
        templateApi.getAll(false)
            .then(res => {
                setTemplates(res.data as TemplateItem[]);
            })
            .catch(() => setTemplates([]))
            .finally(() => setIsLoading(false));
    }, [isOpen]);

    useEffect(() => {
        setSelectedId(currentTemplateId || null);
    }, [currentTemplateId, isOpen]);

    if (!isOpen) return null;

    const categories = Array.from(
        new Set(templates.map(t => t.category).filter(Boolean) as string[])
    );

    const filtered = categoryFilter === 'all'
        ? templates
        : templates.filter(t => t.category === categoryFilter);

    const handleConfirm = () => {
        const tpl = templates.find(t => t.id === selectedId);
        if (tpl) onConfirm(tpl);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="bg-slate-900 border border-white/10 rounded-3xl w-full max-w-5xl max-h-[90vh] flex flex-col shadow-2xl">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-white/10">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-accent-primary/20 flex items-center justify-center">
                            <Layout className="w-5 h-5 text-accent-primary" />
                        </div>
                        <div>
                            <h2 className="text-lg font-black text-white uppercase tracking-wider">Chọn Template CV</h2>
                            <p className="text-xs text-slate-400">Chọn một mẫu phù hợp với ngành nghề của bạn</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="w-9 h-9 rounded-xl hover:bg-white/5 flex items-center justify-center text-slate-400 hover:text-white transition-all"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>

                {/* Category filters */}
                {categories.length > 0 && (
                    <div className="px-6 py-3 border-b border-white/5 flex items-center gap-2 overflow-x-auto no-scrollbar">
                        <button
                            onClick={() => setCategoryFilter('all')}
                            className={cn(
                                "px-3 py-1 rounded-lg text-xs font-bold uppercase tracking-wider transition-all whitespace-nowrap",
                                categoryFilter === 'all'
                                    ? "bg-accent-primary text-white"
                                    : "bg-white/5 text-slate-400 hover:text-white"
                            )}
                        >
                            Tất cả
                        </button>
                        {categories.map(cat => (
                            <button
                                key={cat}
                                onClick={() => setCategoryFilter(cat)}
                                className={cn(
                                    "px-3 py-1 rounded-lg text-xs font-bold uppercase tracking-wider transition-all whitespace-nowrap",
                                    categoryFilter === cat
                                        ? "bg-accent-primary text-white"
                                        : "bg-white/5 text-slate-400 hover:text-white"
                                )}
                            >
                                {cat}
                            </button>
                        ))}
                    </div>
                )}

                {/* Grid */}
                <div className="flex-1 overflow-y-auto p-6">
                    {isLoading ? (
                        <div className="flex items-center justify-center h-64 text-slate-400">
                            <Loader2 className="w-6 h-6 animate-spin mr-2" />
                            Đang tải templates...
                        </div>
                    ) : filtered.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-64 text-slate-500 text-sm">
                            <Layout className="w-10 h-10 mb-3 opacity-30" />
                            Chưa có template nào trong danh mục này
                        </div>
                    ) : (
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                            {filtered.map(t => (
                                <div
                                    key={t.id}
                                    onClick={() => setSelectedId(t.id)}
                                    className={cn(
                                        "group relative cursor-pointer rounded-xl overflow-hidden border-2 transition-all duration-200",
                                        selectedId === t.id
                                            ? "border-accent-primary shadow-lg shadow-accent-primary/20 scale-[1.02]"
                                            : "border-white/10 hover:border-white/30"
                                    )}
                                >
                                    {/* Thumbnail */}
                                    <div className="aspect-[3/4] bg-slate-800 relative overflow-hidden">
                                        {t.thumbnailUrl ? (
                                            <img
                                                src={t.thumbnailUrl}
                                                alt={t.name}
                                                className="w-full h-full object-cover"
                                            />
                                        ) : (
                                            <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-slate-800 to-slate-900">
                                                <Layout className="w-12 h-12 text-slate-600" />
                                            </div>
                                        )}
                                        {selectedId === t.id && (
                                            <div className="absolute top-2 right-2 w-7 h-7 rounded-full bg-accent-primary flex items-center justify-center shadow-lg">
                                                <Check className="w-4 h-4 text-white" />
                                            </div>
                                        )}
                                        <button
                                            onClick={(e) => { e.stopPropagation(); setPreviewTemplate(t); }}
                                            className="absolute bottom-2 right-2 w-7 h-7 rounded-full bg-black/70 backdrop-blur-sm flex items-center justify-center text-white opacity-0 group-hover:opacity-100 transition-opacity"
                                            title="Xem full"
                                        >
                                            <Eye className="w-3.5 h-3.5" />
                                        </button>
                                    </div>
                                    {/* Meta */}
                                    <div className="p-3 bg-slate-900/80">
                                        <div className="text-sm font-bold text-white truncate">{t.name}</div>
                                        <div className="flex items-center gap-1.5 mt-1">
                                            {t.category && (
                                                <span className="flex items-center gap-1 text-[10px] text-slate-400 bg-white/5 px-1.5 py-0.5 rounded">
                                                    <Tag className="w-2.5 h-2.5" /> {t.category}
                                                </span>
                                            )}
                                            {typeof t.usageCount === 'number' && t.usageCount > 0 && (
                                                <span className="text-[10px] text-slate-500">
                                                    {t.usageCount} lượt dùng
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between p-6 border-t border-white/10 bg-slate-950/40">
                    <span className="text-xs text-slate-500">
                        {selectedId
                            ? `Đã chọn: ${templates.find(t => t.id === selectedId)?.name}`
                            : 'Chọn một template để áp dụng'}
                    </span>
                    <div className="flex gap-2">
                        <button
                            onClick={onClose}
                            className="px-4 py-2 bg-white/5 hover:bg-white/10 text-slate-400 rounded-xl text-xs font-bold uppercase tracking-wider transition-all"
                        >
                            Hủy
                        </button>
                        <button
                            onClick={handleConfirm}
                            disabled={!selectedId}
                            className="px-6 py-2 bg-accent-primary hover:bg-accent-primary/80 text-white rounded-xl text-xs font-black uppercase tracking-widest shadow-lg transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                            Áp dụng Template
                        </button>
                    </div>
                </div>
            </div>

            {/* Full Preview Modal */}
            {previewTemplate && (
                <div
                    className="fixed inset-0 z-[60] flex items-center justify-center bg-black/90 p-8 animate-in fade-in"
                    onClick={() => setPreviewTemplate(null)}
                >
                    <div
                        className="bg-white rounded-2xl max-w-3xl max-h-[90vh] overflow-hidden shadow-2xl"
                        onClick={e => e.stopPropagation()}
                    >
                        <div className="flex items-center justify-between p-4 bg-slate-100 border-b">
                            <div>
                                <div className="text-base font-black text-slate-900">{previewTemplate.name}</div>
                                {previewTemplate.description && (
                                    <div className="text-xs text-slate-500">{previewTemplate.description}</div>
                                )}
                            </div>
                            <button
                                onClick={() => setPreviewTemplate(null)}
                                className="w-8 h-8 rounded-lg hover:bg-slate-200 flex items-center justify-center text-slate-600"
                            >
                                <X className="w-4 h-4" />
                            </button>
                        </div>
                        <div className="overflow-y-auto max-h-[75vh]">
                            {previewTemplate.thumbnailUrl ? (
                                <img src={previewTemplate.thumbnailUrl} alt={previewTemplate.name} className="w-full" />
                            ) : previewTemplate.layoutHtml ? (
                                <div className="p-6">
                                    <style dangerouslySetInnerHTML={{ __html: previewTemplate.stylesCss || '' }} />
                                    <div dangerouslySetInnerHTML={{ __html: previewTemplate.layoutHtml }} />
                                </div>
                            ) : (
                                <div className="p-20 text-center text-slate-400">
                                    <Layout className="w-16 h-16 mx-auto mb-4 opacity-30" />
                                    Preview không khả dụng
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default TemplatePickerModal;
