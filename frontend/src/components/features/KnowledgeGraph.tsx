import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import {
    Search, X, TrendingUp, Layers, GitBranch,
    ZoomIn, ZoomOut, Maximize2, Minimize2, Info, Loader2,
    ChevronRight, ArrowRight, Link2, GitMerge, Compass
} from 'lucide-react';
import { skillApi, GraphNode, GraphEdge, SkillNode, OntologyStats } from '../../services/api';
import { cn } from '../../lib/utils';

// ─── Category Color Map ─────────────────────────────────────────────────────

const CATEGORY_COLORS: Record<string, string> = {
    'Programming Languages': '#6366f1',
    'Frontend Development': '#06b6d4',
    'Backend Development': '#8b5cf6',
    'Database': '#f59e0b',
    'DevOps & Infrastructure': '#10b981',
    'Data Engineering': '#ec4899',
    'Machine Learning & AI': '#f43f5e',
    'Mobile Development': '#14b8a6',
    'Security': '#ef4444',
    'Version Control & Collaboration': '#64748b',
    'Testing & QA': '#a855f7',
    'Architecture & Methodologies': '#0ea5e9',
    'Game Development': '#f97316',
    'Blockchain': '#eab308',
    'Embedded & IoT': '#84cc16',
    'Other': '#71717a',
};

const EDGE_COLORS: Record<string, string> = {
    'REQUIRES': '#f43f5e',
    'RELATED_TO': '#6366f1',
    'PART_OF': '#10b981',
    'LEADS_TO': '#f59e0b',
};

const EDGE_LABELS: Record<string, string> = {
    'REQUIRES': 'requires',
    'RELATED_TO': 'related',
    'PART_OF': 'part of',
    'LEADS_TO': 'leads to',
};

// ─── Force Simulation ────────────────────────────────────────────────────────

interface SimNode extends GraphNode {
    x: number;
    y: number;
    vx: number;
    vy: number;
    radius: number;
    pinned?: boolean;
}

function runForceSimulation(
    nodes: SimNode[],
    edges: GraphEdge[],
    width: number,
    height: number,
    iterations: number = 240
) {
    const centerX = width / 2;
    const centerY = height / 2;

    // Initialize positions in a circle
    nodes.forEach((n, i) => {
        if (n.x === 0 && n.y === 0) {
            const angle = (2 * Math.PI * i) / nodes.length;
            const r = Math.min(width, height) * 0.25;
            n.x = centerX + r * Math.cos(angle) + (Math.random() - 0.5) * 40;
            n.y = centerY + r * Math.sin(angle) + (Math.random() - 0.5) * 40;
        }
        n.vx = 0;
        n.vy = 0;
    });

    const nodeMap = new Map(nodes.map(n => [n.id, n]));

    for (let iter = 0; iter < iterations; iter++) {
        const alpha = 1 - iter / iterations;
        const decay = alpha * 0.8;

        // Repulsion
        for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
                const a = nodes[i], b = nodes[j];
                const dx = b.x - a.x;
                const dy = b.y - a.y;
                const distSq = dx * dx + dy * dy || 1;
                const dist = Math.sqrt(distSq);
                
                // Inverse square repulsion
                const repulsionScale = 2500;
                const force = (repulsionScale * decay) / distSq;
                const fx = (dx / dist) * force;
                const fy = (dy / dist) * force;
                a.vx -= fx; a.vy -= fy;
                b.vx += fx; b.vy += fy;

                // Collision prevention
                const minDist = a.radius + b.radius + 15;
                if (dist < minDist) {
                    const overlap = (minDist - dist) * 0.5 * decay;
                    const ox = (dx / dist) * overlap;
                    const oy = (dy / dist) * overlap;
                    a.vx -= ox; a.vy -= oy;
                    b.vx += ox; b.vy += oy;
                }
            }
        }

        // Attraction (edges)
        for (const edge of edges) {
            const a = nodeMap.get(edge.source);
            const b = nodeMap.get(edge.target);
            if (!a || !b) continue;
            const dx = b.x - a.x;
            const dy = b.y - a.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const targetDist = 180;
            const force = (dist - targetDist) * 0.04 * decay;
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            a.vx += fx; a.vy += fy;
            b.vx -= fx; b.vy -= fy;
        }

        // Center gravity
        for (const n of nodes) {
            n.vx += (centerX - n.x) * 0.003 * decay;
            n.vy += (centerY - n.y) * 0.003 * decay;
        }

        // Apply velocity
        for (const n of nodes) {
            if (n.pinned) continue;
            n.vx *= 0.65;
            n.vy *= 0.65;
            n.x += n.vx;
            n.y += n.vy;
            // Strict Bounds
            n.x = Math.max(n.radius + 20, Math.min(width - n.radius - 20, n.x));
            n.y = Math.max(n.radius + 20, Math.min(height - n.radius - 20, n.y));
        }
    }
}


// ─── Component ───────────────────────────────────────────────────────────────

const KnowledgeGraph: React.FC = () => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    // Data
    const [nodes, setNodes] = useState<SimNode[]>([]);
    const [edges, setEdges] = useState<GraphEdge[]>([]);
    const [stats, setStats] = useState<OntologyStats | null>(null);
    const [selectedSkill, setSelectedSkill] = useState<SkillNode | null>(null);
    const [hoveredNode, setHoveredNode] = useState<string | null>(null);

    // Search
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<{ name: string; category: string }[]>([]);
    const [isSearching, setIsSearching] = useState(false);

    // Canvas state
    const [zoom, setZoom] = useState(1);
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
    const [loading, setLoading] = useState(true);
    const [centerSkill, setCenterSkill] = useState<string | undefined>(undefined);
    const [isFullscreen, setIsFullscreen] = useState(false);

    // Refs for animation loop
    const nodesRef = useRef<SimNode[]>([]);
    const edgesRef = useRef<GraphEdge[]>([]);
    const hoveredRef = useRef<string | null>(null);
    const selectedRef = useRef<string | null>(null);
    const zoomRef = useRef(1);
    const panRef = useRef({ x: 0, y: 0 });
    const animRef = useRef<number>(0);
    const draggedNodeRef = useRef<SimNode | null>(null);

    // Sync refs
    useEffect(() => { nodesRef.current = nodes; }, [nodes]);
    useEffect(() => { edgesRef.current = edges; }, [edges]);
    useEffect(() => { hoveredRef.current = hoveredNode; }, [hoveredNode]);
    useEffect(() => { selectedRef.current = selectedSkill?.name?.toLowerCase() || null; }, [selectedSkill]);
    useEffect(() => { zoomRef.current = zoom; }, [zoom]);
    useEffect(() => { panRef.current = pan; }, [pan]);

    // ── Load graph data ──
    const loadGraph = useCallback(async (center?: string) => {
        setLoading(true);
        try {
            const [graphRes, statsRes] = await Promise.all([
                skillApi.getGraphData(center, center ? 2 : 1, center ? 60 : 80),
                skillApi.getStats(),
            ]);

            const gd = graphRes.data;
            const canvas = canvasRef.current;
            const w = canvas?.width || 800;
            const h = canvas?.height || 600;

            const simNodes: SimNode[] = gd.nodes.map(n => ({
                ...n,
                x: 0, y: 0, vx: 0, vy: 0,
                // Reduced radii: center 18, others 6-16
                radius: n.distance === 0 ? 18 : 6 + n.demand * 10,
            }));

            runForceSimulation(simNodes, gd.edges, w, h);

            setNodes(simNodes);
            setEdges(gd.edges);
            setStats(statsRes.data);
        } catch (err) {
            console.error('Failed to load graph', err);
        }
        setLoading(false);
    }, []);

    useEffect(() => { loadGraph(centerSkill); }, [centerSkill, loadGraph]);

    // ── Canvas resize ──
    useEffect(() => {
        const resize = () => {
            const canvas = canvasRef.current;
            const container = containerRef.current;
            if (!canvas || !container) return;
            const dpr = window.devicePixelRatio || 1;
            const rect = container.getBoundingClientRect();
            canvas.width = rect.width * dpr;
            canvas.height = rect.height * dpr;
            canvas.style.width = rect.width + 'px';
            canvas.style.height = rect.height + 'px';
            const ctx = canvas.getContext('2d');
            if (ctx) ctx.scale(dpr, dpr);
        };
        // Small delay so the DOM has time to update in fullscreen mode
        const timer = setTimeout(resize, 50);
        window.addEventListener('resize', resize);
        return () => { clearTimeout(timer); window.removeEventListener('resize', resize); };
    }, [isFullscreen]);

    // ── Esc key to exit fullscreen ──
    useEffect(() => {
        if (!isFullscreen) return;
        const handleKey = (e: KeyboardEvent) => {
            if (e.key === 'Escape') setIsFullscreen(false);
        };
        window.addEventListener('keydown', handleKey);
        return () => window.removeEventListener('keydown', handleKey);
    }, [isFullscreen]);

    // ── Render loop ──
    useEffect(() => {
        const render = () => {
            const canvas = canvasRef.current;
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            if (!ctx) return;
            const dpr = window.devicePixelRatio || 1;
            const w = canvas.width / dpr;
            const h = canvas.height / dpr;
            const z = zoomRef.current;
            const p = panRef.current;
            const hovered = hoveredRef.current;
            const selected = selectedRef.current;
            const ns = nodesRef.current;
            const es = edgesRef.current;

            ctx.clearRect(0, 0, w, h);
            ctx.save();
            ctx.translate(p.x, p.y);
            ctx.scale(z, z);

            const nodeMap = new Map(ns.map(n => [n.id, n]));

            // Draw edges
            for (const edge of es) {
                const a = nodeMap.get(edge.source);
                const b = nodeMap.get(edge.target);
                if (!a || !b) continue;

                const isHighlighted = hovered === a.id || hovered === b.id || selected === a.id || selected === b.id;
                const alpha = isHighlighted ? 0.7 : 0.08;
                const color = EDGE_COLORS[edge.type] || '#444';

                ctx.beginPath();
                ctx.strokeStyle = color;
                ctx.globalAlpha = alpha;
                ctx.lineWidth = isHighlighted ? 1.5 : 0.8;

                // Subtle curved line
                const dx = b.x - a.x;
                const dy = b.y - a.y;
                const mx = (a.x + b.x) / 2;
                const my = (a.y + b.y) / 2;
                const cx = mx + dy * 0.08;
                const cy = my - dx * 0.08;

                ctx.moveTo(a.x, a.y);
                ctx.quadraticCurveTo(cx, cy, b.x, b.y);
                ctx.stroke();

                // Small arrow
                if (isHighlighted || z > 0.8) {
                    const t = 0.88;
                    const ax2 = (1-t)*(1-t)*a.x + 2*(1-t)*t*cx + t*t*b.x;
                    const ay2 = (1-t)*(1-t)*a.y + 2*(1-t)*t*cy + t*t*b.y;
                    const tangentX = 2*(1-t)*(cx - a.x) + 2*t*(b.x - cx);
                    const tangentY = 2*(1-t)*(cy - a.y) + 2*t*(b.y - cy);
                    const angle = Math.atan2(tangentY, tangentX);
                    const arrowSize = isHighlighted ? 6 : 4;

                    ctx.beginPath();
                    ctx.moveTo(ax2, ay2);
                    ctx.lineTo(ax2 - arrowSize * Math.cos(angle - 0.4), ay2 - arrowSize * Math.sin(angle - 0.4));
                    ctx.lineTo(ax2 - arrowSize * Math.cos(angle + 0.4), ay2 - arrowSize * Math.sin(angle + 0.4));
                    ctx.closePath();
                    ctx.fillStyle = color;
                    ctx.fill();
                }
            }

            ctx.globalAlpha = 1;

            // Draw nodes
            for (const node of ns) {
                const isHovered = hovered === node.id;
                const isSelected = selected === node.id;
                const r = node.radius;
                const color = CATEGORY_COLORS[node.category] || CATEGORY_COLORS['Other'];

                // Subtle outer ring
                if (isHovered || isSelected) {
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, r + 6, 0, Math.PI * 2);
                    ctx.fillStyle = color + '15';
                    ctx.fill();
                }

                // Crisp Node circle
                ctx.beginPath();
                ctx.arc(node.x, node.y, r, 0, Math.PI * 2);
                ctx.fillStyle = isHovered || isSelected ? color : color + 'cc';
                ctx.fill();
                
                // Border
                ctx.strokeStyle = isSelected ? '#fff' : (isHovered ? '#fff' : 'rgba(255,255,255,0.2)');
                ctx.lineWidth = isSelected ? 3 : 1.5;
                ctx.stroke();

                // Trending dot
                if (node.trending) {
                    ctx.beginPath();
                    ctx.arc(node.x + r * 0.7, node.y - r * 0.7, 3.5, 0, Math.PI * 2);
                    ctx.fillStyle = '#22c55e';
                    ctx.fill();
                    ctx.strokeStyle = 'rgba(255,255,255,0.4)';
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }

                // Adaptive Label visibility
                const shouldShowLabel = isHovered || isSelected || z > 0.6 || node.distance === 0;
                
                if (shouldShowLabel) {
                    const labelStr = node.label.length > 20 ? node.label.slice(0, 18) + '…' : node.label;
                    ctx.font = `${(isHovered || isSelected) ? '700' : '500'} ${Math.max(10, 12/z)}px Inter, sans-serif`;
                    const metrics = ctx.measureText(labelStr);
                    const tw = metrics.width + 12;
                    const th = 14;
                    
                    // Box background
                    ctx.fillStyle = isHovered || isSelected ? 'rgba(15,15,20,0.95)' : 'rgba(15,15,20,0.6)';
                    ctx.beginPath();
                    const lx = node.x - tw/2;
                    const ly = node.y + r + 8;
                    ctx.roundRect(lx, ly, tw, th + 6, 6);
                    ctx.fill();
                    
                    if (isHovered || isSelected) {
                        ctx.strokeStyle = color;
                        ctx.lineWidth = 1;
                        ctx.stroke();
                    }

                    // Text
                    ctx.fillStyle = isHovered || isSelected ? '#fff' : 'rgba(255,255,255,0.85)';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(labelStr, node.x, ly + (th/2) + 3);
                }
            }

            ctx.restore();
            animRef.current = requestAnimationFrame(render);
        };

        animRef.current = requestAnimationFrame(render);
        return () => cancelAnimationFrame(animRef.current);
    }, []);

    // ── Mouse interactions ──
    const getNodeAt = (clientX: number, clientY: number): SimNode | null => {
        const canvas = canvasRef.current;
        if (!canvas) return null;
        const rect = canvas.getBoundingClientRect();
        const x = (clientX - rect.left - pan.x) / zoom;
        const y = (clientY - rect.top - pan.y) / zoom;

        for (let i = nodes.length - 1; i >= 0; i--) {
            const n = nodes[i];
            const dx = n.x - x, dy = n.y - y;
            if (dx * dx + dy * dy <= (n.radius + 4) * (n.radius + 4)) return n;
        }
        return null;
    };

    const handleMouseMove = (e: React.MouseEvent) => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        if (draggedNodeRef.current) {
            const rect = canvas.getBoundingClientRect();
            const x = (e.clientX - rect.left - pan.x) / zoom;
            const y = (e.clientY - rect.top - pan.y) / zoom;
            
            draggedNodeRef.current.x = x;
            draggedNodeRef.current.y = y;
            draggedNodeRef.current.pinned = true;
            canvas.style.cursor = 'grabbing';
            return;
        }

        if (isDragging) {
            setPan(p => ({ x: p.x + e.movementX, y: p.y + e.movementY }));
            canvas.style.cursor = 'grabbing';
            return;
        }

        const node = getNodeAt(e.clientX, e.clientY);
        setHoveredNode(node?.id || null);
        canvas.style.cursor = node ? 'pointer' : 'grab';
    };

    const handleMouseDown = (e: React.MouseEvent) => {
        const node = getNodeAt(e.clientX, e.clientY);
        if (node) {
            draggedNodeRef.current = node;
            const canvas = canvasRef.current;
            if (canvas) canvas.style.cursor = 'grabbing';
        } else {
            setIsDragging(true);
            setDragStart({ x: e.clientX, y: e.clientY });
        }
    };

    const handleMouseUp = () => {
        setIsDragging(false);
        draggedNodeRef.current = null;
        const canvas = canvasRef.current;
        if (canvas) canvas.style.cursor = 'grab';
    };

    const handleClick = async (e: React.MouseEvent) => {
        const node = getNodeAt(e.clientX, e.clientY);
        if (node) {
            try {
                const res = await skillApi.getSkillNode(node.label);
                setSelectedSkill(res.data);
            } catch { /* ignore */ }
        } else {
            setSelectedSkill(null);
        }
    };

    const handleDoubleClick = (e: React.MouseEvent) => {
        const node = getNodeAt(e.clientX, e.clientY);
        if (node) {
            setCenterSkill(node.label);
            setSearchQuery('');
        }
    };

    const handleWheel = (e: React.WheelEvent) => {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        setZoom(z => Math.max(0.3, Math.min(3, z * delta)));
    };

    // ── Search ──
    useEffect(() => {
        if (!searchQuery.trim()) { setSearchResults([]); return; }
        const timeout = setTimeout(async () => {
            setIsSearching(true);
            try {
                const res = await skillApi.searchSkills(searchQuery, 8);
                setSearchResults(res.data.results.map(r => ({ name: r.name, category: r.category })));
            } catch { setSearchResults([]); }
            setIsSearching(false);
        }, 250);
        return () => clearTimeout(timeout);
    }, [searchQuery]);

    const selectSearchResult = (name: string) => {
        setCenterSkill(name);
        setSearchQuery('');
        setSearchResults([]);
    };

    const resetView = () => {
        setCenterSkill(undefined);
        setZoom(1);
        setPan({ x: 0, y: 0 });
        setSelectedSkill(null);
    };

    // ─── Render ──────────────────────────────────────────────────────────────

    const graphContent = (
        <div className={cn(
            "flex flex-col bg-canvas relative overflow-hidden",
            isFullscreen
                ? "fixed inset-0 z-[9999] h-screen w-screen"
                : "h-full"
        )}>
            {/* ── Header Bar ── */}
            <div className="px-6 py-5 border-b border-white/5 bg-canvas/80 backdrop-blur-xl z-20">
                {/* Search */}
                <div className="relative mb-4">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                        placeholder="Search skills... (e.g. React, Python, Docker)"
                        className="w-full pl-11 pr-10 py-3 rounded-2xl bg-surface border border-white/5 text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-accent-primary/30 transition-all font-outfit"
                    />
                    {searchQuery && (
                        <button onClick={() => { setSearchQuery(''); setSearchResults([]); }} className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary transition-colors">
                            <X className="w-4 h-4" />
                        </button>
                    )}
                    {isSearching && <Loader2 className="absolute right-10 top-1/2 -translate-y-1/2 w-4 h-4 text-accent-primary animate-spin" />}

                    {/* Search dropdown */}
                    {searchResults.length > 0 && (
                        <div className="absolute top-full mt-2 left-0 right-0 bg-surface border border-white/8 rounded-2xl shadow-2xl py-1 z-50 max-h-64 overflow-y-auto">
                            {searchResults.map((r, i) => (
                                <button
                                    key={i}
                                    onClick={() => selectSearchResult(r.name)}
                                    className="w-full flex items-center gap-3 px-4 py-3 hover:bg-surface-hover transition-colors text-left group"
                                >
                                    <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: CATEGORY_COLORS[r.category] || '#666' }} />
                                    <div>
                                        <div className="text-sm font-medium text-text-primary group-hover:text-accent-primary transition-colors">{r.name}</div>
                                        <div className="text-xs text-text-muted">{r.category}</div>
                                    </div>
                                    <ChevronRight className="w-3.5 h-3.5 text-text-muted ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* Stats bar */}
                <div className="flex items-center gap-4 flex-wrap">
                    {stats && (
                        <>
                            <div className="flex items-center gap-1.5 text-xs text-text-muted">
                                <Layers className="w-3.5 h-3.5" />
                                <span className="font-semibold text-text-primary">{stats.total_nodes}</span> nodes
                            </div>
                            <div className="flex items-center gap-1.5 text-xs text-text-muted">
                                <GitBranch className="w-3.5 h-3.5" />
                                <span className="font-semibold text-text-primary">{stats.total_edges}</span> edges
                            </div>
                            <div className="flex items-center gap-1.5 text-xs text-text-muted">
                                <TrendingUp className="w-3.5 h-3.5" />
                                <span className="font-semibold text-text-primary">{stats.connectivity}%</span> connected
                            </div>
                        </>
                    )}

                    <div className="ml-auto flex items-center gap-2">
                        {centerSkill && (
                            <button
                                onClick={resetView}
                                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent-primary/10 text-accent-primary text-xs font-medium hover:bg-accent-primary/20 transition-all"
                            >
                                <Compass className="w-3 h-3" />
                                Reset to overview
                            </button>
                        )}
                        <button
                            onClick={() => setIsFullscreen(f => !f)}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface border border-white/5 text-text-secondary text-xs font-medium hover:text-text-primary hover:bg-surface-hover transition-all shadow-sm"
                            title={isFullscreen ? 'Exit fullscreen (Esc)' : 'Fullscreen'}
                        >
                            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
                            {isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
                        </button>
                    </div>
                </div>
            </div>

            {/* ── Canvas Area ── */}
            <div ref={containerRef} className="flex-1 relative">
                {loading && (
                    <div className="absolute inset-0 flex items-center justify-center z-30 bg-canvas/60 backdrop-blur-sm">
                        <div className="flex flex-col items-center gap-3">
                            <Loader2 className="w-8 h-8 text-accent-primary animate-spin" />
                            <p className="text-xs font-medium text-text-muted uppercase tracking-widest">Loading Knowledge Graph</p>
                        </div>
                    </div>
                )}

                <canvas
                    ref={canvasRef}
                    onMouseMove={handleMouseMove}
                    onMouseDown={handleMouseDown}
                    onMouseUp={handleMouseUp}
                    onMouseLeave={handleMouseUp}
                    onClick={handleClick}
                    onDoubleClick={handleDoubleClick}
                    onWheel={handleWheel}
                    className="w-full h-full"
                />

                {/* Legend & Controls - Nested for better layout */}
                <div className="absolute bottom-6 right-6 flex flex-col items-end gap-3 z-30">
                    <div className="bg-surface/80 backdrop-blur-2xl border border-white/5 rounded-2xl p-3 shadow-2xl flex flex-col gap-2.5 min-w-[140px] animate-in fade-in slide-in-from-bottom-2 duration-500">
                        <p className="text-[9px] font-black uppercase tracking-[0.2em] text-text-muted">Relationships</p>
                        <div className="space-y-1.5">
                            {Object.entries(EDGE_COLORS).map(([type, color]) => (
                                <div key={type} className="flex items-center gap-2.5">
                                    <div className="w-3.5 h-1 rounded-full shadow-sm" style={{ backgroundColor: color }} />
                                    <span className="text-[10px] font-bold text-text-secondary capitalize">{EDGE_LABELS[type]}</span>
                                </div>
                            ))}
                        </div>
                        <div className="h-px bg-white/5 my-0.5" />
                        <div className="grid grid-cols-1 gap-1 text-[9px] font-medium text-text-muted/70">
                            <div className="flex items-center gap-2"><div className="w-1 h-1 rounded-full bg-text-muted" /> Click to select</div>
                            <div className="flex items-center gap-2"><div className="w-1 h-1 rounded-full bg-text-muted" /> Double-click focus</div>
                        </div>
                    </div>

                    <div className="flex flex-col gap-1.5">
                        <button onClick={() => setZoom(z => Math.min(3, z * 1.2))} className="w-9 h-9 rounded-xl bg-surface/90 border border-white/5 flex items-center justify-center text-text-muted hover:text-text-primary hover:bg-surface-hover transition-all shadow-lg active:scale-95">
                            <ZoomIn className="w-4 h-4" />
                        </button>
                        <button onClick={() => setZoom(z => Math.max(0.3, z * 0.8))} className="w-9 h-9 rounded-xl bg-surface/90 border border-white/5 flex items-center justify-center text-text-muted hover:text-text-primary hover:bg-surface-hover transition-all shadow-lg active:scale-95">
                            <ZoomOut className="w-4 h-4" />
                        </button>
                        <button onClick={() => setIsFullscreen(f => !f)} className="w-9 h-9 rounded-xl bg-accent-primary/10 border border-accent-primary/20 flex items-center justify-center text-accent-primary hover:bg-accent-primary hover:text-white transition-all shadow-lg active:scale-95">
                            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                        </button>
                    </div>
                </div>
            </div>

            {/* ── Skill Detail Panel ── */}
            {selectedSkill && (
                <div className="absolute top-20 right-4 w-80 max-h-[70vh] bg-surface/95 backdrop-blur-2xl border border-white/8 rounded-2xl shadow-2xl z-30 overflow-hidden animate-in fade-in slide-in-from-right-4 duration-300">
                    <div className="p-5">
                        {/* Header */}
                        <div className="flex items-start justify-between mb-4">
                            <div>
                                <h3 className="text-lg font-bold text-text-primary font-outfit">{selectedSkill.name}</h3>
                                <div className="flex items-center gap-2 mt-1">
                                    <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CATEGORY_COLORS[selectedSkill.category || ''] || '#666' }} />
                                    <span className="text-xs text-text-muted">{selectedSkill.category}</span>
                                    {selectedSkill.trending && (
                                        <span className="flex items-center gap-0.5 text-[10px] font-bold text-emerald-400 bg-emerald-400/10 px-1.5 py-0.5 rounded-full">
                                            <TrendingUp className="w-2.5 h-2.5" /> Trending
                                        </span>
                                    )}
                                </div>
                            </div>
                            <button onClick={() => setSelectedSkill(null)} className="text-text-muted hover:text-text-primary transition-colors">
                                <X className="w-4 h-4" />
                            </button>
                        </div>

                        {selectedSkill.description && (
                            <p className="text-[13px] text-text-secondary leading-relaxed mb-4">{selectedSkill.description}</p>
                        )}

                        {/* Meta pills */}
                        <div className="flex flex-wrap gap-2 mb-5">
                            <div className="px-2.5 py-1 rounded-lg bg-accent-primary/10 text-accent-primary text-[11px] font-medium">
                                Level: {selectedSkill.level_range.join(' → ')}
                            </div>
                            <div className="px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-400 text-[11px] font-medium">
                                Demand: {Math.round(selectedSkill.demand_score * 100)}%
                            </div>
                        </div>

                        {/* Relationships */}
                        <div className="space-y-3 max-h-[40vh] overflow-y-auto pr-1">
                            {selectedSkill.relationships.REQUIRES?.length > 0 && (
                                <RelSection
                                    title="Prerequisites"
                                    icon={<Link2 className="w-3 h-3" />}
                                    color="#f43f5e"
                                    items={selectedSkill.relationships.REQUIRES}
                                    onSelect={selectSearchResult}
                                />
                            )}
                            {selectedSkill.relationships.RELATED_TO?.length > 0 && (
                                <RelSection
                                    title="Related Skills"
                                    icon={<GitMerge className="w-3 h-3" />}
                                    color="#6366f1"
                                    items={selectedSkill.relationships.RELATED_TO}
                                    onSelect={selectSearchResult}
                                />
                            )}
                            {selectedSkill.relationships.LEADS_TO?.length > 0 && (
                                <RelSection
                                    title="Leads To"
                                    icon={<ArrowRight className="w-3 h-3" />}
                                    color="#f59e0b"
                                    items={selectedSkill.relationships.LEADS_TO}
                                    onSelect={selectSearchResult}
                                />
                            )}
                            {selectedSkill.relationships.PART_OF?.length > 0 && (
                                <RelSection
                                    title="Part Of"
                                    icon={<Layers className="w-3 h-3" />}
                                    color="#10b981"
                                    items={selectedSkill.relationships.PART_OF}
                                    onSelect={selectSearchResult}
                                />
                            )}
                            {selectedSkill.required_by?.length > 0 && (
                                <RelSection
                                    title="Required By"
                                    icon={<Info className="w-3 h-3" />}
                                    color="#94a3b8"
                                    items={selectedSkill.required_by}
                                    onSelect={selectSearchResult}
                                />
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );

    // Use portal for fullscreen to escape ArtifactPanel's containing block
    if (isFullscreen) {
        return createPortal(graphContent, document.body);
    }

    return graphContent;
};


// ── Relationship section sub-component ──

interface RelSectionProps {
    title: string;
    icon: React.ReactNode;
    color: string;
    items: string[];
    onSelect: (name: string) => void;
}

const RelSection: React.FC<RelSectionProps> = ({ title, icon, color, items, onSelect }) => (
    <div>
        <div className="flex items-center gap-1.5 mb-1.5">
            <span style={{ color }}>{icon}</span>
            <span className="text-[11px] font-bold uppercase tracking-wider" style={{ color }}>{title}</span>
        </div>
        <div className="flex flex-wrap gap-1">
            {items.map((item, i) => (
                <button
                    key={i}
                    onClick={() => onSelect(item)}
                    className="px-2 py-1 rounded-md bg-white/5 text-[11px] text-text-secondary hover:text-accent-primary hover:bg-accent-primary/10 transition-all"
                >
                    {item}
                </button>
            ))}
        </div>
    </div>
);


export default KnowledgeGraph;
