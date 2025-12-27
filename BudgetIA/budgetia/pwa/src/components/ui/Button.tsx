import type { ButtonHTMLAttributes } from 'react';
import { forwardRef } from 'react';
import { cn } from '../../utils/cn';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'neutral' | 'danger' | 'danger-outline' | 'ghost' | 'outline';
    size?: 'sm' | 'md' | 'lg' | 'icon';
    isLoading?: boolean;
    icon?: React.ElementType;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(({ 
    className, 
    variant = 'primary', 
    size = 'md', 
    isLoading, 
    icon: Icon,
    children, 
    disabled,
    ...props 
}, ref) => {
    const variants = {
        primary: "bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg shadow-emerald-900/10",
        secondary: "bg-gray-800 hover:bg-gray-700 text-white border border-gray-700",
        neutral: "bg-gray-800/50 hover:bg-gray-800 text-gray-400 hover:text-white border border-gray-800",
        danger: "bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-900/30",
        "danger-outline": "border border-red-900/30 text-red-400 hover:bg-red-900/10",
        ghost: "hover:bg-gray-800 text-gray-400 hover:text-white",
        outline: "border border-gray-700 text-gray-300 hover:text-white hover:bg-gray-800"
    };

    const sizes = {
        sm: "h-8 px-3 text-xs",
        md: "h-10 px-4 py-2",
        lg: "h-12 px-6 text-lg",
        icon: "h-10 w-10 p-2.5"
    };

    return (
        <button
            ref={ref}
            disabled={disabled || isLoading}
            className={cn(
                "inline-flex items-center justify-center rounded-xl font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 disabled:pointer-events-none disabled:opacity-50",
                variants[variant],
                sizes[size],
                className
            )}
            {...props}
        >
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {!isLoading && Icon && <Icon className={cn("h-4 w-4", children ? "mr-2" : "")} />}
            {children}
        </button>
    );
});

Button.displayName = "Button";

export { Button };
