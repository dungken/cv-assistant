import * as React from "react"
import { cn } from "../../lib/utils"

interface DialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  children: React.ReactNode
}

export function Dialog({ open, onOpenChange, children }: DialogProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-[1000] flex items-center justify-center p-4">
      <div 
        className="absolute inset-0 bg-black/80 backdrop-blur-[6px] animate-in fade-in duration-300"
        onClick={() => onOpenChange(false)}
      />
      
      {/* Modal Container */}
      <div className="relative w-full max-w-md animate-in zoom-in-95 fade-in duration-300">
        {children}
      </div>
    </div>
  )
}

export function DialogContent({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={cn(
      "relative bg-surface shadow-[0_32px_64px_-16px_rgba(0,0,0,0.6)] rounded-[2.5rem] overflow-hidden border border-white/10 backdrop-blur-xl transition-all duration-300", 
      "ring-1 ring-white/5",
      className
    )}>
      {children}
    </div>
  )
}

export function DialogHeader({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={cn("p-8 pb-4 space-y-2", className)}>
      {children}
    </div>
  )
}

export function DialogTitle({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <h2 className={cn("text-2xl font-black font-outfit tracking-tight text-text-primary", className)}>
      {children}
    </h2>
  )
}

export function DialogDescription({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <p className={cn("text-sm text-text-secondary font-medium leading-relaxed", className)}>
      {children}
    </p>
  )
}

export function DialogFooter({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={cn("p-8 pt-4 flex items-center justify-end gap-3", className)}>
      {children}
    </div>
  )
}
