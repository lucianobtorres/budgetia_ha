import type { Budget } from '../../types/domain';
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
                const isHighlighted = (highlightCategory && budget.Categoria === highlightCategory) || 
                                      (highlightId && budget["ID Orcamento"] === highlightId);
                
                return (
                    <div 
                        key={idx} 
                        ref={el => registerRef(budget.Categoria, el)}
                        className={`transition-colors rounded-xl ${isHighlighted ? 'bg-white/10 ring-1 ring-white/20' : ''}`}
                    >
                        <ProgressListItem
                            title={budget.Categoria}
                            subtitle={budget['Período Orçamento']}
                            color={getCategoryColor(budget.Categoria)}
                            value={budget['Valor Gasto Atual'] || 0}
                            limit={budget['Valor Limite'] || 0}
                            onEdit={() => onEdit(budget)}
                            onDelete={() => budget["ID Orcamento"] && onDelete(budget["ID Orcamento"])}
                        />
                    </div>
                )
            })}
        </div>
    );
}
