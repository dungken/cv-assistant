import { cn } from '../../lib/utils';

/** Shimmer skeleton block — dùng để placeholder cho content đang load. */
export function Skeleton({ className, style }: { className?: string; style?: React.CSSProperties }) {
    return (
        <div
            className={cn(
                'rounded-md bg-white/5 animate-pulse',
                className,
            )}
            style={style}
        />
    );
}

/** Gauge skeleton — radial chart placeholder cho FreshnessGauge. */
export function GaugeSkeleton() {
    return (
        <div className="h-64 flex flex-col items-center justify-center gap-4">
            <div className="relative w-44 h-44">
                <Skeleton className="absolute inset-0 rounded-full" />
                <div className="absolute inset-6 rounded-full bg-canvas" />
                <Skeleton className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-8 w-20" />
            </div>
            <Skeleton className="h-3 w-32" />
        </div>
    );
}

/** Time-series skeleton — line chart placeholder. */
export function ChartSkeleton({ height = 200 }: { height?: number }) {
    return (
        <div className="flex flex-col gap-3" style={{ height }}>
            <div className="flex-1 flex items-end gap-2">
                {[40, 60, 35, 70, 55, 80, 65].map((h, i) => (
                    <Skeleton
                        key={i}
                        className="flex-1"
                        style={{ height: `${h}%` }}
                    />
                ))}
            </div>
            <div className="flex justify-between">
                {[1, 2, 3, 4, 5].map((i) => (
                    <Skeleton key={i} className="h-2 w-8" />
                ))}
            </div>
        </div>
    );
}

/** List item skeleton — cho Alerts/Opportunity list. */
export function ListSkeleton({ rows = 3 }: { rows?: number }) {
    return (
        <ul className="space-y-3">
            {Array.from({ length: rows }).map((_, i) => (
                <li
                    key={i}
                    className="flex flex-col gap-2 p-4 rounded-xl bg-white/[0.02] border border-white/5"
                >
                    <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 space-y-2">
                            <Skeleton className="h-4 w-3/4" />
                            <Skeleton className="h-3 w-1/2" />
                        </div>
                        <Skeleton className="h-5 w-12 shrink-0 rounded-full" />
                    </div>
                </li>
            ))}
        </ul>
    );
}
