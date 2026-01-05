import type { InputHTMLAttributes } from 'react';
import { forwardRef } from 'react';
import { cn } from '../../utils/cn';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
    icon?: React.ElementType;
    variant?: 'default' | 'glass';
}

const Input = forwardRef<HTMLInputElement, InputProps>(({ className, icon: Icon, variant = 'default', ...props }, ref) => {
    
    const variants = {
        default: "bg-surface-input border-border focus-visible:border-primary focus-visible:ring-primary",
        glass: "bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus-visible:border-emerald-500 focus-visible:ring-emerald-500/20"
    };

    return (
        <div className="relative flex-1">
            {Icon && (
                <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none text-gray-400">
                    <Icon size={16} />
                </div>
            )}
            <input
                ref={ref}
                className={cn(
                    "flex w-full rounded-xl border px-3 py-2 text-sm transition-all outline-none focus-visible:ring-1 disabled:cursor-not-allowed disabled:opacity-50 h-11",
                     // Base styles that are safe to override
                    "file:border-0 file:bg-transparent file:text-sm file:font-medium",
                    variants[variant],
                    Icon && "pl-10",
                    className
                )}
                {...props}
            />
        </div>
    );
});

Input.displayName = "Input";

export { Input };
