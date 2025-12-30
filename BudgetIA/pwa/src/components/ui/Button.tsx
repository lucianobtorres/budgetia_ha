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
        primary: "bg-primary hover:bg-primary-hover text-white shadow-lg shadow-primary/20",
        secondary: "bg-surface-hover hover:bg-border text-text-primary border border-border",
        neutral: "bg-surface-card/50 hover:bg-surface-hover text-text-secondary hover:text-text-primary border border-border",
        danger: "bg-danger/10 hover:bg-danger/20 text-danger border border-danger/30",
        "danger-outline": "border border-danger/30 text-danger hover:bg-danger/10",
        ghost: "hover:bg-surface-hover text-text-secondary hover:text-text-primary",
        outline: "border border-border text-text-secondary hover:text-text-primary hover:bg-surface-hover"
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
                "inline-flex items-center justify-center rounded-xl font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:pointer-events-none disabled:opacity-50",
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
