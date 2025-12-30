import { useQueryClient } from '@tanstack/react-query';
import { useSummary, useExpenses } from '../hooks/useDashboard';
import { ArrowUpCircle, ArrowDownCircle, Wallet, ChevronRight } from 'lucide-react';

import Chat from './Chat';
import { Skeleton } from '../components/ui/Skeleton';
import BudgetSummaryWidget from '../components/dashboard/BudgetSummaryWidget';
import { CategoryStackedBar } from '../components/dashboard/CategoryStackedBar';
import { NotificationBell } from '../components/layout/NotificationBell';
import { KpiCard } from '../components/dashboard/KpiCard';
import { EmptyState } from '../components/ui/EmptyState';
import { useDrawer } from '../context/DrawerContext';
import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { telemetry } from '../services/telemetry';
import { useTour } from '../context/TourContext';
import { PageHeader } from '../components/ui/PageHeader';

export default function Dashboard() {
  const { openDrawer } = useDrawer();
  const location = useLocation();
  const queryClient = useQueryClient();
  const { data: summary, isLoading: loadingSummary } = useSummary();
  const { data: expenses, isLoading: loadingExpenses } = useExpenses(50);
  const { startTour } = useTour(); // Hook do Tour

  const loading = loadingSummary || loadingExpenses;
  const hasData = summary && (summary.total_receitas > 0 || summary.total_despesas > 0);

  // Telemetria & Tour
  useEffect(() => {
      telemetry.logAction('view_dashboard');
      
      if (!loading) {
         // Lógica Adaptativa: Se tem dados => Tour Avançado, senão => Onboarding
         const tourName = hasData ? 'dashboard_full' : 'dashboard_empty';
         
         // Check if we should restart tour from Profile
         const shouldRestart = location.state?.restartTour;

         if (shouldRestart) {
             // Delay to ensure UI is ready
             setTimeout(() => {
                 startTour(tourName as any, true);
                 // Clear state to prevent loop on refresh? (React router state persists on refresh usually, but logic here is safe enough if hasData doesn't change wildly)
                 // Ideally we clear it, but modifying history stack is complex.
                 // Since 'true' forces it, it's fine.
             }, 800);
         } else {
             // Normal flow (checks localStorage internally)
             // Pequeno delay para garantir que o DOM renderizou
             setTimeout(() => {
                startTour(tourName as any);
             }, 1000);
         }
      }
  }, [loading, hasData, location]);

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

  // If no data (New User), show guidance
  if (!loading && !hasData) {
      return (
        <div className="h-full flex flex-col gap-4 pb-0 md:pb-6 overflow-hidden">
             <div id="welcome-header" className="flex-none">
                <PageHeader 
                   title="Bem-vindo(a)!" 
                   description="Vamos começar sua jornada financeira."
                   action={<NotificationBell />}
                />
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
                 <div id="chat-widget" className="w-full flex-none h-[400px]">
                      <Chat variant="widget" className="h-full w-full" onAction={handleChatAction} />
                 </div>
             </div>
        </div>
      )
  }

  return (
    <div className="h-full flex flex-col gap-4 pb-0 md:pb-6 overflow-hidden">
      {/* Header - Visible on all screens, adaptable size */}
      {/* Header - Visible on all screens, adaptable size */}
      <div id="welcome-header" className="flex-none">
        <PageHeader 
            title="Visão Geral" 
            description="Acompanhe seu desempenho financeiro."
            action={<NotificationBell />}
        />
      </div>
      
      {/* Top Section: KPIs & Charts - Scrollable internally, capped height to ensure Chat space */}
      <div className="flex-shrink-0 max-h-[55vh] space-y-4 overflow-y-auto scrollbar-none px-1 pb-2">
         {/* Compact KPI Grid */}
         <div id="kpi-grid" className="grid grid-cols-3 gap-2 md:gap-4 md:grid-cols-3">
            <KpiCard 
                id="kpi-saldo"
                title="Saldo" 
                value={(summary?.total_receitas || 0) - (summary?.total_despesas || 0)} 
                icon={Wallet} 
                color="text-primary"
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
                color="text-danger"
                compact
            />
         </div>

         {/* Budget Summary Section */}
         <div id="budget-widget">
            <BudgetSummaryWidget />
         </div>

         {/* iOS Style Chart Section */}
         {/* iOS Style Chart Section - Mimics BudgetSummaryWidget */}
         <div 
            id="category-chart"
            onClick={() => openDrawer('CATEGORY_EXPENSES')}
            className="cursor-pointer group relative overflow-hidden rounded-xl border border-gray-800 bg-gray-900/50 p-4 transition-all hover:border-blue-500/30 hover:bg-gray-900/80"
         >
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                     <div className="p-2 bg-blue-500/10 rounded-lg">
                        <Wallet className="w-4 h-4 text-blue-400" />
                     </div>
                     <div>
                         <h3 className="text-sm font-medium text-text-primary">Despesas por Categoria</h3>
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
                    data={expenses?.slice(0, 5) || []} 
                />
            </div>
         </div>
      </div>

       {/* Chat Section - Takes remaining height on mobile, full height col on desktop */}
       <div id="chat-widget" className="flex-1 min-h-0 md:min-h-[400px] md:h-full">
            <Chat variant="widget" className="h-full w-full" onAction={handleChatAction} />
       </div>
    </div>
  );
}



