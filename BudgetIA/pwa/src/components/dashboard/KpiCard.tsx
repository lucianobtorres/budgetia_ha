import { cn } from '../../utils/cn';

interface KpiCardProps {
    title: string;
    value: number;
    icon: any; // Lucide Icon type is generic
    color: string;
    compact?: boolean;
}

export function KpiCard({ title, value, icon: Icon, color, compact }: KpiCardProps) {
    let gradient = "from-gray-500/10";
    let border = "border-gray-800";
    
    if (color.includes('emerald')) { gradient = "from-emerald-500/10"; border = "border-emerald-500/20"; }
    else if (color.includes('blue')) { gradient = "from-blue-500/10"; border = "border-blue-500/20"; }
    else if (color.includes('red')) { gradient = "from-red-500/10"; border = "border-red-500/20"; }

    return (
        <div className={cn(
            "rounded-xl border bg-gradient-to-br to-transparent shadow-sm transition-all",
            gradient,
            border,
            compact ? "p-3" : "p-6"
        )}>
            <div className={cn("flex flex-row items-center justify-between space-y-0", compact ? "mb-1" : "pb-2")}>
                <div className={cn("font-medium text-gray-400 truncate", compact ? "text-[10px] uppercase tracking-wider" : "text-sm")}>{title}</div>
                <Icon className={cn(color, compact ? "h-3 w-3" : "h-4 w-4")} />
            </div>
            <div className={cn("font-bold text-white truncate", compact ? "text-sm md:text-2xl" : "text-2xl")}>
                {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', notation: compact ? "compact" : "standard" }).format(value)}
            </div>
        </div>
    )
}
