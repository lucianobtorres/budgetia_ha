import { cn } from '../../utils/cn';

interface KpiCardProps {
    id?: string;
    title: string;
    value: number;
    icon: any; // Lucide Icon type is generic
    color: string;
    compact?: boolean;
}

export function KpiCard({ id, title, value, icon: Icon, color, compact }: KpiCardProps) {
    let gradient = "from-surface-hover/10";
    let border = "border-border";
    let iconClass = color; // Default to passing class through
    
    // Semantic Mapping Logic
    if (color.includes('primary') || color.includes('emerald')) { 
        gradient = "from-primary/10"; 
        border = "border-primary/20";
        iconClass = "text-emerald-500";
    }
    else if (color.includes('blue')) { 
        gradient = "from-blue-500/10"; 
        border = "border-blue-500/20"; 
        // iconClass remains as passed (e.g., text-blue-400)
    }
    else if (color.includes('danger') || color.includes('red')) { 
        gradient = "from-danger/10"; 
        border = "border-danger/20"; 
        iconClass = "text-danger";
    }

    return (
        <div id={id} className={cn(
            "rounded-xl border bg-gradient-to-br to-transparent shadow-sm transition-all",
            gradient,
            border,
            compact ? "p-3" : "p-6"
        )}>
            <div className={cn("flex flex-row items-center justify-between space-y-0", compact ? "mb-1" : "pb-2")}>
                <div className={cn("font-medium text-text-muted truncate", compact ? "text-[10px] uppercase tracking-wider" : "text-sm")}>{title}</div>
                <Icon className={cn(iconClass, compact ? "h-3 w-3" : "h-4 w-4")} />
            </div>
            <div className={cn("font-bold text-text-primary truncate", compact ? "text-sm md:text-2xl" : "text-2xl")}>
                {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', notation: compact ? "compact" : "standard" }).format(value)}
            </div>
        </div>
    )
}
