import type { Budget } from '../../domain/models/Budget';
import { ProgressListItem } from '../ui/ProgressListItem';

interface Props {
    budgets: Budget[];
    highlightCategory?: string;
    highlightId?: number;
    getCategoryColor: (category: string) => string;
    onEdit: (budget: Budget) => void;
    onDelete: (id: number) => void;
    registerRef: (key: string, el: HTMLDivElement | null) => void;
}

export function BudgetList({
    budgets,
    highlightCategory,
    highlightId,
    getCategoryColor,
    onEdit,
    onDelete,
    registerRef
}: Props) {
    if (budgets.length === 0) {
        return (
            <div className="text-center py-10 text-text-muted">
                <p>Nenhum orçamento definido.</p>
                <p className="text-sm">Clique em "+" para começar.</p>
            </div>
        );
    }

    return (
        <div className="space-y-2">
            {budgets.map((budget, idx) => {
                const isHighlighted = (highlightCategory && budget.category === highlightCategory) || 
                                      (highlightId && budget.id === highlightId);
                
                return (
                    <div 
                        key={idx} 
                        ref={el => registerRef(budget.category, el)}
                        className={`transition-colors rounded-xl ${isHighlighted ? 'bg-white/10 ring-1 ring-white/20' : ''}`}
                    >
                        <ProgressListItem
                            title={budget.category}
                            subtitle={budget.period}
                            color={getCategoryColor(budget.category)}
                            value={budget.currentSpent || 0}
                            limit={budget.limitValue || 0}
                            onEdit={() => onEdit(budget)}
                            onDelete={() => budget.id && onDelete(budget.id)}
                        />
                    </div>
                )
            })}
        </div>
    );
}
