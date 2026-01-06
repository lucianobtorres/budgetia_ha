import { Target, CreditCard } from 'lucide-react';
import type { ExpenseData } from '../../types/domain';
import { ProgressListItem } from '../ui/ProgressListItem';

interface Props {
  data: ExpenseData[];
  totalExpenses: number;
  highlightCategory?: string;
  getCategoryColor: (category: string) => string;
  checkBudgetExists: (category: string) => boolean;
  onBudgetClick: (category: string) => void;
  onTransactionsClick: (category: string) => void;
  registerRef: (category: string, el: HTMLDivElement | null) => void;
}

export function CategoryList({
  data,
  totalExpenses,
  highlightCategory,
  getCategoryColor,
  checkBudgetExists,
  onBudgetClick,
  onTransactionsClick,
  registerRef
}: Props) {
  if (data.length === 0) {
    return (
      <div className="text-center text-text-muted py-8">
        Nenhuma categoria encontrada.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {data.map((cat) => {
        const color = getCategoryColor(cat.name);
        const hasBudget = checkBudgetExists(cat.name);
        const isHighlighted = highlightCategory === cat.name;

        return (
          <div
            key={cat.name}
            ref={(el) => registerRef(cat.name, el)}
            className={`transition-colors rounded-xl ${
              isHighlighted ? 'bg-surface-hover ring-1 ring-border-hover' : ''
            }`}
          >
            <ProgressListItem
              title={cat.name}
              color={color}
              value={cat.value}
              totalReference={totalExpenses}
              alwaysShowActions={true}
              action={
                <div className="flex items-center gap-1">
                  {hasBudget && (
                    <button
                      onClick={() => onBudgetClick(cat.name)}
                      className="p-1.5 text-text-secondary hover:text-primary-light hover:bg-surface-hover rounded-md transition-colors"
                      title="Ver Orçamento"
                    >
                      <Target size={14} />
                    </button>
                  )}
                  {cat.value > 0 && (
                    <button
                      onClick={() => onTransactionsClick(cat.name)}
                      className="p-1.5 text-text-secondary hover:text-primary-light hover:bg-surface-hover rounded-md transition-colors"
                      title="Ver Transações"
                    >
                      <CreditCard size={14} />
                    </button>
                  )}
                </div>
              }
            />
          </div>
        );
      })}
    </div>
  );
}
