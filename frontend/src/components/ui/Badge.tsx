import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "../../lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-1 text-[10px] font-black uppercase tracking-widest transition-all",
  {
    variants: {
      variant: {
        default:
          "bg-accent-primary text-white shadow-sm",
        secondary:
          "bg-surface/80 text-text-secondary hover:bg-surface-hover hover:text-text-primary",
        destructive:
          "bg-rose-500/10 text-rose-500",
        outline: "text-text-secondary bg-overlay/5",
        success: "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20",
        glow: "bg-accent-primary/10 text-accent-primary animate-pulse shadow-[0_0_15px_rgba(var(--accent-primary),0.2)]",
        "action-chip": "action-chip bg-surface/40 hover:bg-surface-hover",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
