import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useSummary, useExpenses } from '../hooks/useDashboard';
import { ArrowUpCircle, ArrowDownCircle, Wallet, ChevronRight } from 'lucide-react';

import Chat from './Chat';
import { Skeleton } from '../components/ui/Skeleton';
import BudgetSummaryWidget from '../components/dashboard/BudgetSummaryWidget';
import { CategoryStackedBar } from '../components/dashboard/CategoryStackedBar';
import CategoryDrawer from '../components/dashboard/CategoryDrawer';
import { NotificationBell } from '../components/layout/NotificationBell';
import { KpiCard } from '../components/dashboard/KpiCard';
import { EmptyState } from '../components/ui/EmptyState';

export default function Dashboard() {
  const [isCategoryDrawerOpen, setCategoryDrawerOpen] = useState(false);
  const queryClient = useQueryClient();
  const { data: summary, isLoading: loadingSummary } = useSummary();
  const { data: expenses, isLoading: loadingExpenses } = useExpenses();

  const loading = loadingSummary || loadingExpenses;

  const handleChatAction = () => {
      // Invalidate all dashboard queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
  };

  if (loading) {
      return (
        <div className="space-y-6">
            <div className="flex gap-4">
                <Skeleton className="h-16 flex-1 rounded-xl" />
                <Skeleton className="h-16 flex-1 rounded-xl" />
                <Skeleton className="h-16 flex-1 rounded-xl" />
            </div>
            
            <Skeleton className="h-32 rounded-xl" />
            
             <div className="grid gap-4 md:grid-cols-1 lg:grid-cols-4">
                <div className="lg:col-span-3">
                     <Skeleton className="h-[200px] rounded-xl" />
                </div>
                 <div className="lg:col-span-1">
                     <Skeleton className="h-[400px] rounded-xl" />
                </div>
            </div>
        </div>
      );
  }

  const hasData = summary && (summary.total_receitas > 0 || summary.total_despesas > 0);

  // If no data (New User), show guidance
  if (!loading && !hasData) {
      return (
        <div className="h-full flex flex-col gap-4 pb-0 md:pb-6 overflow-hidden">
             <div className="flex-none pt-safe pt-4 flex items-start justify-between">
                <div>
                   <h2 className="text-xl md:text-3xl font-bold tracking-tight text-white mb-1 md:mb-2">Bem-vindo(a)!</h2>
                   <p className="text-sm md:text-base text-gray-400">Vamos começar sua jornada financeira.</p>
                </div>
                <NotificationBell />
             </div>
             
             <div className="flex-1 flex flex-col items-center justify-between min-h-0">
                 <div className="flex-1 w-full flex items-center justify-center">
                    <EmptyState 
                        title="Seu Dashboard está vazio"
                        description="Para ver seus indicadores, converse com a IA para adicionar transações ou conecte sua planilha."
                        icon={Wallet}
                        className="h-auto min-h-0"
                    />
                 </div>
                 {/* Chat Widget always available for onboarding instructions - Fixed height at bottom */}
                 <div className="w-full flex-none h-[400px]">
                      <Chat variant="widget" className="h-full w-full" onAction={handleChatAction} />
                 </div>
             </div>
        </div>
      )
  }

  return (
    <div className="h-full flex flex-col gap-4 pb-0 md:pb-6 overflow-hidden">
      {/* Header - Visible on all screens, adaptable size */}
      <div className="flex-none pt-safe flex items-start justify-between">
        <div>
           <h2 className="text-xl md:text-3xl font-bold tracking-tight text-white mb-1 md:mb-2">Visão Geral</h2>
           <p className="text-sm md:text-base text-gray-400">Acompanhe seu desempenho financeiro.</p>
        </div>
        <NotificationBell />
      </div>
      
      {/* Top Section: KPIs & Charts - Scrollable internally, capped height to ensure Chat space */}
      <div className="flex-shrink-0 max-h-[55vh] space-y-4 overflow-y-auto scrollbar-none px-1 pb-2">
         {/* Compact KPI Grid */}
         <div className="grid grid-cols-3 gap-2 md:gap-4 md:grid-cols-3">
            <KpiCard 
                title="Saldo" 
                value={(summary?.total_receitas || 0) - (summary?.total_despesas || 0)} 
                icon={Wallet} 
                color="text-emerald-400"
                compact
            />
            <KpiCard 
                title="Receitas" 
                value={summary?.total_receitas || 0} 
                icon={ArrowUpCircle} 
                color="text-blue-400"
                compact
            />
            <KpiCard 
                title="Despesas" 
                value={summary?.total_despesas || 0} 
                icon={ArrowDownCircle} 
                color="text-red-400"
                compact
            />
         </div>

         {/* Budget Summary Section */}
         <BudgetSummaryWidget />

         {/* iOS Style Chart Section */}
         {/* iOS Style Chart Section - Mimics BudgetSummaryWidget */}
         <div 
            onClick={() => setCategoryDrawerOpen(true)}
            className="cursor-pointer group relative overflow-hidden rounded-xl border border-gray-800 bg-gray-900/50 p-4 transition-all hover:border-blue-500/30 hover:bg-gray-900/80"
         >
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                     <div className="p-2 bg-blue-500/10 rounded-lg">
                        <Wallet className="w-4 h-4 text-blue-400" />
                     </div>
                     <div>
                         <h3 className="text-sm font-medium text-white">Despesas por Categoria</h3>
                         <p className="text-xs text-gray-400">
                            {expenses?.length || 0} categorias ativas
                         </p>
                     </div>
                </div>
                <div className="flex items-center gap-2">
                    <ChevronRight className="w-5 h-5 text-gray-500 group-hover:text-blue-400 transition-colors" />
                </div>
            </div>

            <div className="w-full">
                <CategoryStackedBar 
                    data={expenses || []} 
                />
            </div>
         </div>
      </div>

       {/* Chat Section - Takes remaining height on mobile, full height col on desktop */}
       <div className="flex-1 min-h-0 md:min-h-[400px] md:h-full">
            <Chat variant="widget" className="h-full w-full" onAction={handleChatAction} />
       </div>

       <CategoryDrawer 
            isOpen={isCategoryDrawerOpen} 
            onClose={() => setCategoryDrawerOpen(false)} 
       />
    </div>
  );
}



