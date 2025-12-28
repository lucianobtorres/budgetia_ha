import { cn } from "../../utils/cn";

export type CardVariant = 'default' | 'emerald' | 'violet' | 'orange' | 'blue' | 'red';

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
    hoverEffect?: boolean;
    variant?: CardVariant;
}

const HOVER_STYLES = {
    default: "hover:border-gray-700 hover:shadow-gray-900/10",
    emerald: "hover:border-emerald-500/30 hover:shadow-emerald-900/10",
    violet: "hover:border-violet-500/30 hover:shadow-violet-900/10",
    orange: "hover:border-orange-500/30 hover:shadow-orange-900/10",
    blue: "hover:border-blue-500/30 hover:shadow-blue-900/10",
    red: "hover:border-red-500/30 hover:shadow-red-900/10",
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
                "bg-gray-950/50 backdrop-blur-sm border border-gray-800 rounded-xl transition-all",
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
