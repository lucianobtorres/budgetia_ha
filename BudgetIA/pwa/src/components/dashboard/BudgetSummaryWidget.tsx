import { useBudgetsList } from '../../hooks/useBudgets';
import { Skeleton } from '../ui/Skeleton';
import { cn } from '../../utils/cn';
import { ChevronRight, Target } from 'lucide-react';
import { useDrawer } from '../../context/DrawerContext';

export default function BudgetSummaryWidget() {
    const { data: budgets, isLoading: loading } = useBudgetsList();
    const { openDrawer } = useDrawer();

    if (loading) {
         return (
            <div className="rounded-xl border border-border bg-surface-card/50 p-4">
                 <div className="flex items-center justify-between">
                    <Skeleton className="h-5 w-32" />
                    <Skeleton className="h-4 w-16" />
                 </div>
                 <div className="mt-4 gap-2 flex">
                    <Skeleton className="h-2 w-full rounded-full" />
                 </div>
            </div>
         )
    }

    const safeBudgets = budgets || [];
    
    // Calculate overall health
    const totalLimit = safeBudgets.reduce((acc, b) => acc + (b['Valor Limite'] || 0), 0);
    const totalSpent = safeBudgets.reduce((acc, b) => acc + (b['Valor Gasto Atual'] || 0), 0);
    const overallProgress = totalLimit > 0 ? (totalSpent / totalLimit) * 100 : 0;
    const overBudgetCount = safeBudgets.filter(b => (b['Valor Gasto Atual'] || 0) > (b['Valor Limite'] || 0)).length;

    return (
        <div 
            onClick={() => openDrawer('BUDGETS')}
            className="cursor-pointer group relative overflow-hidden rounded-xl border border-border bg-surface-card/50 p-4 transition-all hover:border-primary/30 hover:bg-surface-card/80"
        >
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                     <div className="p-2 bg-primary/10 rounded-lg">
                        <Target className="w-4 h-4 text-primary-light" />
                     </div>
                     <div>
                         <h3 className="text-sm font-medium text-text-primary">Meus Orçamentos</h3>
                         <p className="text-xs text-text-muted">
                            {safeBudgets.length} categorias • {safeBudgets.length === 0 ? "Definir metas" : overBudgetCount === 0 ? "Tudo sob controle" : `${overBudgetCount} acima do limite`}
                         </p>
                     </div>
                </div>
                <ChevronRight className="w-5 h-5 text-text-muted group-hover:text-primary-light transition-colors" />
            </div>

            {/* Mini Progress Bar for Overall Health */}
            <div className="space-y-1">
                <div className="flex justify-between text-[10px] text-text-muted font-medium uppercase tracking-wider">
                    <span>Geral</span>
                    <span>{overallProgress.toFixed(0)}%</span>
                </div>
                <div className="h-2 w-full bg-surface-hover rounded-full overflow-hidden">
                    <div 
                        className={cn("h-full rounded-full transition-all duration-500", overallProgress > 100 ? "bg-danger" : "bg-primary")}
                        style={{ width: `${Math.min(overallProgress, 100)}%` }}
                    />
                </div>
            </div>
        </div>
    )
}

