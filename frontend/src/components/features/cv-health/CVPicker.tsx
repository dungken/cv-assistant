import { useEffect, useState } from 'react';
import { AxiosError } from 'axios';
import { cvDocumentApi, cvHealthApi, type CvDocument } from '../../../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { Badge } from '../../ui/Badge';

interface Props {
    userId: string;
    onLinked: () => void;
}

const ROLES: Array<{ id: string; label: string }> = [
    { id: 'backend', label: 'Backend' },
    { id: 'frontend', label: 'Frontend' },
    { id: 'data', label: 'Data' },
    { id: 'devops', label: 'DevOps' },
    { id: 'ai_engineer', label: 'AI Engineer' },
    { id: 'fullstack', label: 'Fullstack' },
    { id: 'mobile', label: 'Mobile' },
];

/**
 * Pulls the user's existing CV documents and lets them pick one to link
 * to the CV Health pipeline. Linking writes to `skill_user_cv` via
 * POST /api/skills/cv/me, which also triggers a BackgroundTask Freshness
 * recompute on the server.
 *
 * Skills come from the chosen CV's latest version `dataJson`. Two shapes
 * are common in the repo:
 *   - `CVData.skills` = string[]                  (AI CV Designer flow)
 *   - `ParseResult.skills` = Record<string,string[]>   (NER upload flow)
 * Plus a fallback that scans `experience[].entities` for SKILL entities.
 *
 * Recency is conservatively defaulted to the current year — when NER
 * end-date extraction is wired in (§3.2.5), we'll derive per-skill recency
 * from `experience[].end_date` instead.
 */

interface NerEntity { text: string; type: string }
interface NerBlock { entities?: NerEntity[] }

function extractSkills(parsed: unknown): string[] {
    if (!parsed || typeof parsed !== 'object') return [];
    const obj = parsed as Record<string, unknown>;
    const out = new Set<string>();
    const push = (s: unknown) => {
        if (typeof s === 'string' && s.trim()) out.add(s.trim());
    };

    const skillsField = obj.skills;
    if (Array.isArray(skillsField)) {
        // CVData shape: string[]
        skillsField.forEach(push);
    } else if (skillsField && typeof skillsField === 'object') {
        // ParseResult shape: Record<category, string[]>
        Object.values(skillsField as Record<string, unknown>).forEach(arr => {
            if (Array.isArray(arr)) arr.forEach(push);
        });
    }

    // Fallback / supplement: collect SKILL entities from experience + projects.
    for (const key of ['experience', 'projects'] as const) {
        const blocks = obj[key];
        if (!Array.isArray(blocks)) continue;
        for (const b of blocks as NerBlock[]) {
            for (const e of b.entities ?? []) {
                if (e && (e.type === 'SKILL' || e.type === 'TECH')) push(e.text);
            }
        }
    }

    return Array.from(out);
}
export default function CVPicker({ userId, onLinked }: Props) {
    const [docs, setDocs] = useState<CvDocument[] | null>(null);
    const [loadingList, setLoadingList] = useState(false);
    const [listError, setListError] = useState<string | null>(null);

    const [selectedId, setSelectedId] = useState<number | null>(null);
    const [role, setRole] = useState<string>('backend');
    const [linking, setLinking] = useState(false);
    const [linkError, setLinkError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;
        setLoadingList(true);
        setListError(null);
        cvDocumentApi.list()
            .then(res => {
                if (cancelled) return;
                setDocs(res.data);
                if (res.data.length > 0) setSelectedId(res.data[0].id);
            })
            .catch(err => {
                if (cancelled) return;
                setListError(
                    err instanceof AxiosError ? err.message : 'Không tải được danh sách CV.'
                );
            })
            .finally(() => { if (!cancelled) setLoadingList(false); });
        return () => { cancelled = true; };
    }, []);

    async function handleUseCv() {
        if (!selectedId) return;
        setLinking(true);
        setLinkError(null);
        try {
            // Get the full CV document then load its latest version's dataJson
            // to extract the skills array.
            const docRes = await cvDocumentApi.getById(selectedId);
            const doc = docRes.data;
            const latestVersionInfo = doc.versions
                .slice()
                .sort((a, b) => b.versionNumber - a.versionNumber)[0];
            if (!latestVersionInfo) {
                throw new Error('CV không có version nào.');
            }
            const verRes = await cvDocumentApi.getVersion(doc.id, latestVersionInfo.id);
            const parsed = JSON.parse(verRes.data.dataJson);
            const skills = extractSkills(parsed);

            if (skills.length === 0) {
                throw new Error('CV này chưa có kỹ năng nào được trích xuất.');
            }

            const currentYear = new Date().getFullYear();
            await cvHealthApi.upsertCv(
                userId,
                role,
                skills.map(name => ({ name, last_used_year: currentYear })),
            );
            onLinked();
        } catch (err) {
            setLinkError(
                err instanceof AxiosError
                    ? (err.response?.data as { detail?: string } | undefined)?.detail
                      || err.message
                    : err instanceof Error
                      ? err.message
                      : 'Không liên kết được CV.'
            );
        } finally {
            setLinking(false);
        }
    }

    return (
        <Card className="bg-surface/80 border border-white/5">
            <CardHeader>
                <CardTitle>Chọn CV để theo dõi</CardTitle>
                <CardDescription>
                    Kết nối một CV bạn đã upload vào pipeline CV Health Intelligence.
                    Skills sẽ được sync và Freshness Score tính ngay.
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
                {loadingList ? (
                    <div className="text-sm text-text-secondary/60">Đang tải danh sách CV…</div>
                ) : listError ? (
                    <div className="p-4 rounded-xl bg-rose-500/5 border border-rose-500/10 text-sm text-rose-400">
                        {listError}
                    </div>
                ) : !docs || docs.length === 0 ? (
                    <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/10 text-sm text-amber-400">
                        Bạn chưa upload CV nào. Hãy vào <span className="font-mono">AI CV Designer</span>{' '}
                        hoặc <span className="font-mono">CV List</span> ở sidebar để upload trước.
                    </div>
                ) : (
                    <>
                        <div>
                            <div className="text-xs uppercase tracking-widest text-text-secondary font-bold mb-2">
                                CV của bạn ({docs.length})
                            </div>
                            <div className="grid gap-2">
                                {docs.map(d => (
                                    <button
                                        key={d.id}
                                        type="button"
                                        onClick={() => setSelectedId(d.id)}
                                        className={[
                                            'flex items-center justify-between gap-3 px-4 py-3 rounded-xl text-left transition-colors border',
                                            selectedId === d.id
                                                ? 'bg-accent-primary/10 border-accent-primary/30'
                                                : 'bg-surface/40 border-white/5 hover:bg-surface-hover/50',
                                        ].join(' ')}
                                    >
                                        <div className="flex-1 min-w-0">
                                            <div className="text-sm font-bold truncate">{d.name}</div>
                                            <div className="text-xs text-text-secondary mt-0.5">
                                                v{d.currentVersion} · cập nhật{' '}
                                                {new Date(d.updatedAt).toLocaleDateString('vi-VN')}
                                                {typeof d.atsScore === 'number' && (
                                                    <> · ATS {d.atsScore.toFixed(0)}</>
                                                )}
                                            </div>
                                        </div>
                                        {selectedId === d.id && (
                                            <Badge variant="default" className="shrink-0">Đang chọn</Badge>
                                        )}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div>
                            <div className="text-xs uppercase tracking-widest text-text-secondary font-bold mb-2">
                                Vai trò mục tiêu
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {ROLES.map(r => (
                                    <Button
                                        key={r.id}
                                        size="sm"
                                        variant={r.id === role ? 'default' : 'ghost'}
                                        onClick={() => setRole(r.id)}
                                        className="h-8 px-3 text-xs"
                                    >
                                        {r.label}
                                    </Button>
                                ))}
                            </div>
                        </div>

                        {linkError && (
                            <div className="p-3 rounded-xl bg-rose-500/5 border border-rose-500/10 text-sm text-rose-400">
                                {linkError}
                            </div>
                        )}

                        <Button
                            onClick={handleUseCv}
                            disabled={!selectedId || linking}
                            variant="default"
                            className="w-full"
                        >
                            {linking ? 'Đang sync…' : 'Dùng CV này cho CV Health'}
                        </Button>
                    </>
                )}
            </CardContent>
        </Card>
    );
}
