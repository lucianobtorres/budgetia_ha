import { type Transaction } from "../../hooks/useTransactions";
import { cn } from "../../utils/cn";
import { getCategoryColor } from "../../utils/colors";
import { Edit2, Trash2 } from "lucide-react";

interface TransactionCardProps {
    transaction: Transaction;
    onDelete: (id: number) => void;
    onEdit?: (transaction: Transaction) => void;
    onCategoryClick?: (category: string) => void;
    categoryColor?: string;
}

export function TransactionCard({ transaction, onDelete, onEdit, onCategoryClick, categoryColor }: TransactionCardProps) {
    const isExpense = transaction["Tipo (Receita/Despesa)"] === "Despesa";
    const dateObj = new Date(transaction.Data);
    const day = dateObj.getDate();
    const month = dateObj.toLocaleDateString('pt-BR', { month: 'short' }).replace('.', '');
    const year = dateObj.getFullYear();
    const isCurrentYear = year === new Date().getFullYear();
    
    // Use passed consistent color, or fallback to hash-based for non-expense/orphan items
    // (Note: The parent now passes consistent rank-based color for all items)
    const displayColor = categoryColor || getCategoryColor(transaction.Categoria);
    
    return (
        <div className="flex items-center justify-between p-3 bg-surface-card/50 border border-border rounded-xl mb-2 hover:bg-surface-hover/50 transition-colors group">
            <div className="flex items-center gap-3 overflow-hidden">
                {/* Date Box */}
                <div className="flex flex-col items-center justify-center p-2 bg-surface-hover rounded-lg min-w-[3.5rem] h-[3.5rem]">
                    <span className={cn("text-sm font-bold text-text-primary", !isCurrentYear && "text-xs")}>{day}</span>
                    <span className="text-[10px] uppercase text-text-muted font-medium leading-none">{month}</span>
                    {!isCurrentYear && (
                        <span className="text-[9px] text-text-secondary font-medium leading-tight">{year}</span>
                    )}
                </div>

                {/* Info */}
                <div className="flex flex-col min-w-0">
                    <span className="text-sm font-medium text-text-primary truncate">{transaction.Descricao}</span>
                    <div className="flex items-center gap-2 mt-1">
                        {/* Chip using Global Colors - Clickable */}
                        <button 
                            onClick={(e) => {
                                e.stopPropagation();
                                onCategoryClick?.(transaction.Categoria);
                            }}
                            className={cn(
                                "px-2 py-0.5 rounded-full text-[10px] font-semibold text-white/90 shadow-sm transition-transform hover:scale-105 active:scale-95",
                                onCategoryClick ? "cursor-pointer hover:brightness-110" : "cursor-default"
                            )}
                            style={{ backgroundColor: displayColor }}
                        >
                           {transaction.Categoria}
                        </button>
                    </div>
                </div>
            </div>

            {/* Value & Actions */}
            <div className="flex flex-col items-end gap-1 flex-shrink-0 ml-2">
                 <span className={cn(
                    "text-sm font-bold font-mono",
                    isExpense ? "text-danger" : "text-primary-light"
                )}>
                    {isExpense ? '-' : '+'}{new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(transaction.Valor)}
                </span>
                
                {/* Actions (Visible on hover/focus on desktop, always there or swipe on mobile? Let's show icons small) */}
                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity md:opacity-0 md:group-hover:opacity-100 opacity-100">
                    <button 
                         onClick={() => onDelete(transaction["ID Transacao"])}
                         className="p-1.5 text-text-secondary hover:text-danger bg-surface-hover hover:bg-surface-card rounded-lg"
                    >
                        <Trash2 size={14} />
                    </button>
                    {onEdit && (
                        <button 
                            onClick={() => onEdit(transaction)}
                            className="p-1.5 text-text-secondary hover:text-primary-light bg-surface-hover hover:bg-surface-card rounded-lg"
                        >
                            <Edit2 size={14} />
                        </button>
                    )}
                </div>
            </div>
        </div>
    )
} 
// NOTE: I am refining the chip style in the actual tool call below to better match user request "chip background color".
