import type { InputHTMLAttributes } from 'react';
import { forwardRef } from 'react';
import { cn } from '../../utils/cn';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
    icon?: React.ElementType;
}

const Input = forwardRef<HTMLInputElement, InputProps>(({ className, icon: Icon, ...props }, ref) => {
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
                    "flex w-full rounded-xl border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-gray-500 focus-visible:outline-none focus-visible:border-emerald-500 focus-visible:ring-1 focus-visible:ring-emerald-500 disabled:cursor-not-allowed disabled:opacity-50 transition-colors",
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
