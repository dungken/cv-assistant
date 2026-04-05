import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "../../lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-2xl text-sm font-bold ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary/20 disabled:pointer-events-none disabled:opacity-50 active:scale-95",
  {
    variants: {
      variant: {
        default: "bg-accent-primary text-white shadow-lg shadow-accent-primary/20 hover:bg-accent-primary/90 hover:shadow-accent-primary/30",
        primary: "bg-accent-primary text-white shadow-lg shadow-accent-primary/20 hover:bg-accent-primary/90 hover:shadow-accent-primary/30",
        destructive:
          "bg-red-500/10 text-red-500 hover:bg-red-500/20",
        outline:
          "bg-transparent text-text-secondary hover:bg-surface-hover hover:text-text-primary",
        secondary:
          "bg-surface/50 text-text-primary hover:bg-surface-hover shadow-sm",
        ghost: "hover:bg-surface-hover text-text-secondary hover:text-text-primary",
        link: "text-accent-primary underline-offset-4 hover:underline",
        glass: "glass-pill text-text-primary hover:scale-[1.02]",
        pill: "rounded-full bg-surface-hover text-text-primary px-8 hover:bg-accent-primary hover:text-white hover:shadow-lg hover:shadow-accent-primary/20",
      },
      size: {
        default: "h-12 px-6 py-3",
        sm: "h-9 rounded-xl px-3",
        lg: "h-14 rounded-3xl px-10 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
