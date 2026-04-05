import React, { useState, useEffect } from 'react';
import { X, ArrowLeftRight } from 'lucide-react';
import { cvDocumentApi, CvDiff } from '../../services/api';

interface DiffViewProps {
    docId: number;
    versionA: number;
    versionB: number;
    onClose: () => void;
}

interface DiffLine {
    type: 'added' | 'removed' | 'unchanged';
    key: string;
    oldValue?: string;
    newValue?: string;
}

function computeDiff(oldJson: string, newJson: string): DiffLine[] {
    const lines: DiffLine[] = [];
    try {
        const oldObj = JSON.parse(oldJson);
        const newObj = JSON.parse(newJson);
        diffObjects(oldObj, newObj, '', lines);
    } catch {
        // Fallback: line-by-line comparison
        const oldLines = oldJson.split('\n');
        const newLines = newJson.split('\n');
        const maxLen = Math.max(oldLines.length, newLines.length);
        for (let i = 0; i < maxLen; i++) {
            const ol = oldLines[i] || '';
            const nl = newLines[i] || '';
            if (ol === nl) {
                lines.push({ type: 'unchanged', key: `line-${i}`, oldValue: ol, newValue: nl });
            } else {
                if (ol) lines.push({ type: 'removed', key: `old-${i}`, oldValue: ol });
                if (nl) lines.push({ type: 'added', key: `new-${i}`, newValue: nl });
            }
        }
    }
    return lines;
}

function diffObjects(oldObj: any, newObj: any, prefix: string, lines: DiffLine[]) {
    const allKeys = new Set([...Object.keys(oldObj || {}), ...Object.keys(newObj || {})]);
    for (const key of allKeys) {
        const path = prefix ? `${prefix}.${key}` : key;
        const oldVal = oldObj?.[key];
        const newVal = newObj?.[key];

        if (oldVal === undefined) {
            lines.push({ type: 'added', key: path, newValue: formatValue(newVal) });
        } else if (newVal === undefined) {
            lines.push({ type: 'removed', key: path, oldValue: formatValue(oldVal) });
        } else if (typeof oldVal === 'object' && typeof newVal === 'object' && !Array.isArray(oldVal)) {
            diffObjects(oldVal, newVal, path, lines);
        } else {
            const oldStr = formatValue(oldVal);
            const newStr = formatValue(newVal);
            if (oldStr !== newStr) {
                lines.push({ type: 'removed', key: path, oldValue: oldStr });
                lines.push({ type: 'added', key: path, newValue: newStr });
            } else {
                lines.push({ type: 'unchanged', key: path, oldValue: oldStr, newValue: newStr });
            }
        }
    }
}

function formatValue(val: any): string {
    if (val === null || val === undefined) return '';
    if (typeof val === 'string') return val;
    if (Array.isArray(val)) return val.map(v => typeof v === 'string' ? v : JSON.stringify(v)).join(', ');
    return JSON.stringify(val, null, 2);
}

const DiffView: React.FC<DiffViewProps> = ({ docId, versionA, versionB, onClose }) => {
    const [diff, setDiff] = useState<CvDiff | null>(null);
    const [diffLines, setDiffLines] = useState<DiffLine[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [showAll, setShowAll] = useState(false);

    useEffect(() => {
        loadDiff();
    }, [docId, versionA, versionB]);

    const loadDiff = async () => {
        setIsLoading(true);
        try {
            const res = await cvDocumentApi.diff(docId, versionA, versionB);
            setDiff(res.data);
            setDiffLines(computeDiff(res.data.oldVersion.dataJson, res.data.newVersion.dataJson));
        } catch {
            // handle error
        } finally {
            setIsLoading(false);
        }
    };

    const changedLines = diffLines.filter(l => l.type !== 'unchanged');
    const displayLines = showAll ? diffLines : changedLines;

    return (
        <div className="border-t border-white/5 bg-secondary/10 px-8 py-6 max-h-[50vh] overflow-y-auto animate-in slide-in-from-bottom-4 duration-300">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <h3 className="font-bold text-text-primary text-sm">Diff View</h3>
                    <span className="text-[10px] bg-accent-primary/10 text-accent-primary px-2 py-1 rounded-lg font-bold flex items-center gap-1">
                        v{versionA} <ArrowLeftRight className="w-3 h-3" /> v{versionB}
                    </span>
                    <span className="text-[10px] text-text-secondary/50">
                        {changedLines.length} change{changedLines.length !== 1 ? 's' : ''}
                    </span>
                </div>
                <div className="flex items-center gap-2">
                    <button onClick={() => setShowAll(!showAll)}
                        className="text-[9px] font-bold text-text-secondary bg-secondary/30 hover:bg-secondary/50 px-2 py-1 rounded-lg transition-colors">
                        {showAll ? 'Changes Only' : 'Show All'}
                    </button>
                    <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-secondary/50 text-text-secondary">
                        <X className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {isLoading ? (
                <div className="flex items-center justify-center py-10">
                    <div className="w-6 h-6 border-2 border-accent-primary/30 border-t-accent-primary rounded-full animate-spin"></div>
                </div>
            ) : displayLines.length === 0 ? (
                <p className="text-center text-text-secondary/50 text-sm py-10">No differences found</p>
            ) : (
                <div className="font-mono text-xs space-y-0.5">
                    {displayLines.map((line, i) => (
                        <div key={i}
                            className={`flex gap-3 px-3 py-1.5 rounded-lg ${
                                line.type === 'added' ? 'bg-emerald-500/10 text-emerald-400' :
                                line.type === 'removed' ? 'bg-red-500/10 text-red-400' :
                                'text-text-secondary/50'
                            }`}>
                            <span className="w-5 text-right text-text-secondary/30 select-none flex-shrink-0">
                                {line.type === 'added' ? '+' : line.type === 'removed' ? '-' : ' '}
                            </span>
                            <span className="text-text-secondary/40 w-40 truncate flex-shrink-0 font-bold">{line.key}</span>
                            <span className="flex-1 break-all">
                                {line.type === 'added' ? line.newValue : line.type === 'removed' ? line.oldValue : line.oldValue}
                            </span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default DiffView;
