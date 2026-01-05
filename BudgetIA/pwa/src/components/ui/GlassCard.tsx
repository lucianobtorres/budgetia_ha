import { cn } from "../../utils/cn";

export type CardVariant = 'default' | 'emerald' | 'violet' | 'orange' | 'blue' | 'red' | 'pink';

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
    hoverEffect?: boolean;
    variant?: CardVariant;
}

const HOVER_STYLES = {
    default: "hover:border-border-hover hover:shadow-surface/20",
    emerald: "hover:border-primary/50 hover:shadow-primary/10",
    violet: "hover:border-violet-500/50 hover:shadow-violet-900/10",
    orange: "hover:border-orange-500/50 hover:shadow-orange-900/10",
    blue: "hover:border-blue-500/50 hover:shadow-blue-900/10",
    red: "hover:border-danger/50 hover:shadow-danger/10",
    pink: "hover:border-pink-500/50 hover:shadow-pink-900/10",
};

export function GlassCard({ 
    children, 
    className, 
    hoverEffect = true, 
    variant = 'default',
    ...props 
}: GlassCardProps) {
    return (
        <div 
            className={cn(
                "bg-surface-card/50 backdrop-blur-sm border border-border rounded-xl transition-all",
                hoverEffect && [
                    "hover:scale-[1.01] hover:shadow-lg cursor-default",
                    HOVER_STYLES[variant] || HOVER_STYLES.default
                ],
                className
            )}
            {...props}
        >
            {children}
        </div>
    )
}
