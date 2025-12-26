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
}

export function ProgressListItem({ 
    title, 
    subtitle, 
    color, 
    value, 
    limit, 
    totalReference,
    onEdit, 
    onDelete 
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

    return (
        <div className="group relative rounded-xl border border-gray-800 bg-gray-900/40 p-4 transition-all hover:bg-gray-900/60 hover:border-gray-700">
            {/* Actions (Absolute) - Only if handlers provided */}
            {(onEdit || onDelete) && (
                <div className="absolute top-3 right-3 flex space-x-1 opacity-100 md:opacity-0 group-hover:opacity-100 transition-opacity bg-gray-900/80 rounded-lg p-1 z-10">
                    {onEdit && (
                        <button 
                            onClick={(e) => { e.stopPropagation(); onEdit(); }}
                            className="p-1.5 text-gray-400 hover:text-emerald-400 rounded-md hover:bg-gray-800"
                            title="Editar"
                        >
                            <Edit2 size={14} />
                        </button>
                    )}
                    {onDelete && (
                        <button 
                            onClick={(e) => { e.stopPropagation(); onDelete(); }}
                            className="p-1.5 text-gray-400 hover:text-red-400 rounded-md hover:bg-gray-800"
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
                        <span className="font-semibold text-white truncate text-base">{title}</span>
                    </div>
                    {subtitle && (
                        <span className="text-[10px] text-gray-500 uppercase tracking-wider pl-4">{subtitle}</span>
                    )}
                </div>
            </div>

            {/* Content */}
            <div className="space-y-2 mt-3 pl-4">
                <div className="flex justify-between text-xs text-gray-400">
                    <span>Gasto: <span className="text-white font-medium">{new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)}</span></span>
                    
                    {/* Show Meta only in Budget Mode */}
                    {isBudgetMode && (
                        <span>Meta: <span className="text-white font-medium">{new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(limit || 0)}</span></span>
                    )}
                </div>
                
                {/* Progress Bar */}
                <div className="relative h-2.5 w-full bg-gray-800 rounded-full overflow-hidden">
                    <div 
                        className={cn("h-full rounded-full transition-all duration-500 relative", isOver ? "bg-red-500" : "")}
                        style={{ 
                            width: `${percentage}%`,
                            backgroundColor: isOver ? undefined : color
                        }}
                    >
                        {/* Shine effect */}
                        <div className="absolute inset-0 bg-white/10" />
                    </div>
                </div>

                {/* Footer Text */}
                <div className="flex justify-between items-center text-[10px]">
                    <div className={cn("font-medium", isOver ? "text-red-400" : "text-emerald-400")}>
                       <span style={isBudgetMode && !isOver ? { color } : {}}>
                            {percentage.toFixed(isBudgetMode ? 0 : 1)}% {isBudgetMode ? "utilizado" : "do total"}
                       </span>
                    </div>
                    {isOver && (
                        <span className="text-red-400 flex items-center font-bold bg-red-950/30 px-2 py-0.5 rounded-full">
                            <AlertTriangle size={10} className="mr-1" /> EXCEDIDO
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
}
