import { type TextareaHTMLAttributes, forwardRef } from 'react';
import { cn } from '../../utils/cn';

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
    variant?: 'default' | 'glass';
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(({ className, variant = 'default', ...props }, ref) => {
    
    const variants = {
        default: "bg-surface-input border-border focus-visible:border-primary focus-visible:ring-primary",
        glass: "bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus-visible:border-emerald-500 focus-visible:ring-emerald-500/20"
    };

    return (
        <textarea
            ref={ref}
            className={cn(
                "flex w-full rounded-xl border px-3 py-2 text-sm transition-all outline-none focus-visible:ring-1 disabled:cursor-not-allowed disabled:opacity-50 min-h-[80px]",
                // Base styles
                "placeholder:text-text-muted text-text-primary",
                variants[variant],
                className
            )}
            {...props}
        />
    );
});

Textarea.displayName = "Textarea";

export { Textarea };
