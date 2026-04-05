import * as React from "react"
import { cn } from "../../lib/utils"

const DropdownMenu = ({ children }: { children: React.ReactNode }) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const containerRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative inline-block text-left" ref={containerRef}>
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          if (child.type === DropdownMenuTrigger) {
            return React.cloneElement(child as React.ReactElement<any>, { 
              onClick: () => setIsOpen(!isOpen) 
            });
          }
          if (child.type === DropdownMenuContent) {
            return isOpen ? child : null;
          }
        }
        return child;
      })}
    </div>
  );
};

const DropdownMenuTrigger = ({ children, asChild, onClick }: { children: React.ReactNode, asChild?: boolean, onClick?: () => void }) => {
    return <div onClick={onClick} className="cursor-pointer">{children}</div>;
};

const DropdownMenuContent = ({ children, align = "end", className }: { children: React.ReactNode, align?: "start" | "end", className?: string }) => {
    const alignmentClasses = align === "start" ? "left-0" : "right-0";
    return (
        <div className={cn("absolute z-50 mt-2 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md", alignmentClasses, className)}>
            {children}
        </div>
    );
};

const DropdownMenuItem = ({ children, onClick, className }: { children: React.ReactNode, onClick?: () => void, className?: string }) => {
    return (
        <div
            onClick={onClick}
            className={cn(
                "relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50 hover:bg-white/5",
                className
            )}
        >
            {children}
        </div>
    );
};

export { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem }
