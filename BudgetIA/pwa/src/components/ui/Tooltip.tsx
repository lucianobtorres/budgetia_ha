import * as React from "react"
import { cn } from "../../utils/cn"

const TooltipProvider = ({ children, className, style }: { children: React.ReactNode, className?: string, style?: React.CSSProperties }) => (
    <div className={cn("relative group", className)} style={style}>{children}</div>
)

const Tooltip = ({ children }: { children: React.ReactNode }) => <>{children}</>

const TooltipTrigger = ({ children, className, style }: { children: React.ReactNode, className?: string, style?: React.CSSProperties }) => {
    return (
        <div className={cn("trigger-wrapper w-full h-full", className)} style={style}>
             {children}
        </div>
    )
}

const TooltipContent = ({ children, className }: { children: React.ReactNode, className?: string }) => (
  <div className={cn(
    "absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-max px-2 py-1 text-xs text-white bg-gray-900 border border-gray-800 rounded shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50",
    className
  )}>
    {children}
  </div>
)

export { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider }
