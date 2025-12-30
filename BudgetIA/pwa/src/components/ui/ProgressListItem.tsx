import { AlertTriangle, Edit2, Trash2 } from 'lucide-react';
import { cn } from '../../utils/cn';

interface Props {
    title: string;
    subtitle?: string; // e.g., "MENSAL"
    color: string;
    value: number;
    
    // Mode A: Budget (has a hard limit)
    limit?: number; 
    
    // Mode B: Relative (percentage of a total)
    totalReference?: number;
    
    // Interactions
    onEdit?: () => void;
    onDelete?: () => void;
    action?: React.ReactNode;
    alwaysShowActions?: boolean;
}

export function ProgressListItem({ 
    title, 
    subtitle, 
    color, 
    value, 
    limit, 
    totalReference,
    onEdit, 
    onDelete,
    action,
    alwaysShowActions = false
}: Props) {
    const isBudgetMode = limit !== undefined;
    
    let percentage = 0;
    let isOver = false;

    if (isBudgetMode) {
        const safeLimit = limit || 1;
        percentage = Math.min((value / safeLimit) * 100, 100);
        isOver = value > safeLimit;
    } else if (totalReference) {
        percentage = (value / (totalReference || 1)) * 100;
    }

    const actionOpacityClass = alwaysShowActions 
        ? "opacity-100" 
        : "opacity-100 md:opacity-0 group-hover:opacity-100";

    return (
        <div className="group relative rounded-xl border border-border bg-surface-card/40 p-4 transition-all hover:bg-surface-card/60 hover:border-border-hover">
            {/* Actions (Absolute) - Only if handlers provided */}
            {(onEdit || onDelete || action) && (
                <div className={`absolute top-3 right-3 flex items-center space-x-1 ${actionOpacityClass} transition-opacity bg-surface-card/80 rounded-lg p-1 z-10`}>
                    {action}
                    {onEdit && (
                        <button 
                            onClick={(e) => { e.stopPropagation(); onEdit(); }}
                            className="p-1.5 text-text-secondary hover:text-primary-light rounded-md hover:bg-surface-hover"
                            title="Editar"
                        >
                            <Edit2 size={14} />
                        </button>
                    )}
                    {onDelete && (
                        <button 
                            onClick={(e) => { e.stopPropagation(); onDelete(); }}
                            className="p-1.5 text-text-secondary hover:text-danger rounded-md hover:bg-surface-hover"
                            title="Excluir"
                        >
                            <Trash2 size={14} />
                        </button>
                    )}
                </div>
            )}

            {/* Header */}
            <div className="flex justify-between items-center mb-2 pr-16">
                <div className="flex flex-col">
                    <div className="flex items-center gap-2">
                        {/* Color Dot Indicator */}
                        <div 
                            className="w-2 h-2 rounded-full" 
                            style={{ backgroundColor: color }}
                        />
                        <span className="font-semibold text-text-primary truncate text-base">{title}</span>
                    </div>
                    {subtitle && (
                        <span className="text-[10px] text-text-muted uppercase tracking-wider pl-4">{subtitle}</span>
                    )}
                </div>
            </div>

            {/* Content */}
            <div className="space-y-2 mt-3 pl-4">
                <div className="flex justify-between text-xs text-text-secondary">
                    <span>Gasto: <span className="text-text-primary font-medium">{new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)}</span></span>
                    
                    {/* Show Meta only in Budget Mode */}
                    {isBudgetMode && (
                        <span>Meta: <span className="text-text-primary font-medium">{new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(limit || 0)}</span></span>
                    )}
                </div>
                
                {/* Progress Bar */}
                <div className="relative h-2.5 w-full bg-surface-hover rounded-full overflow-hidden">
                    <div 
                        className={cn("h-full rounded-full transition-all duration-500 relative", isOver ? "bg-danger" : "")}
                        style={{ 
                            width: `${percentage}%`,
                            backgroundColor: isOver ? undefined : color
                        }}
                    >
                        {/* Shine effect */}
                        <div className="absolute inset-0 bg-text-primary/10" />
                    </div>
                </div>

                {/* Footer Text */}
                <div className="flex justify-between items-center text-[10px]">
                    <div className={cn("font-medium", isOver ? "text-danger" : "text-primary-light")}>
                       <span style={isBudgetMode && !isOver ? { color } : {}}>
                            {percentage.toFixed(isBudgetMode ? 0 : 1)}% {isBudgetMode ? "utilizado" : "do total"}
                       </span>
                    </div>
                    {isOver && (
                        <span className="text-danger flex items-center font-bold bg-danger/10 px-2 py-0.5 rounded-full">
                            <AlertTriangle size={10} className="mr-1" /> EXCEDIDO
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
}
