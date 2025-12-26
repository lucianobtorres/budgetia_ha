import { useState } from 'react';
import { useBudgetsList } from '../../hooks/useBudgets';
import { Skeleton } from '../ui/Skeleton';
import { cn } from '../../utils/cn';
import { ChevronRight, Target } from 'lucide-react';
import BudgetDrawerContent from '../budgets/BudgetDrawerContent';

export default function BudgetSummaryWidget() {
    const { data: budgets, isLoading: loading } = useBudgetsList();
    const [isDrawerOpen, setIsDrawerOpen] = useState(false);

    if (loading) {
         return (
            <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-4">
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
        <>
            {/* Compact Summary Card - Triggers Drawer */}
            <div 
                onClick={() => setIsDrawerOpen(true)}
                className="cursor-pointer group relative overflow-hidden rounded-xl border border-gray-800 bg-gray-900/50 p-4 transition-all hover:border-emerald-500/30 hover:bg-gray-900/80"
            >
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                         <div className="p-2 bg-emerald-500/10 rounded-lg">
                            <Target className="w-4 h-4 text-emerald-400" />
                         </div>
                         <div>
                             <h3 className="text-sm font-medium text-white">Meus Orçamentos</h3>
                             <p className="text-xs text-gray-400">
                                {safeBudgets.length} categorias • {safeBudgets.length === 0 ? "Definir metas" : overBudgetCount === 0 ? "Tudo sob controle" : `${overBudgetCount} acima do limite`}
                             </p>
                         </div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-500 group-hover:text-emerald-400 transition-colors" />
                </div>

                {/* Mini Progress Bar for Overall Health */}
                <div className="space-y-1">
                    <div className="flex justify-between text-[10px] text-gray-400 font-medium uppercase tracking-wider">
                        <span>Geral</span>
                        <span>{overallProgress.toFixed(0)}%</span>
                    </div>
                    <div className="h-2 w-full bg-gray-800 rounded-full overflow-hidden">
                        <div 
                            className={cn("h-full rounded-full transition-all duration-500", overallProgress > 100 ? "bg-red-500" : "bg-emerald-500")}
                            style={{ width: `${Math.min(overallProgress, 100)}%` }}
                        />
                    </div>
                </div>
            </div>

            {/* The Full Detail Drawer */}
            <BudgetDrawerContent 
                isOpen={isDrawerOpen} 
                onClose={() => setIsDrawerOpen(false)}
            />
        </>
    )
}

