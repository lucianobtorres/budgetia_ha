import { useState, useRef, useEffect } from 'react';
import { useBudgetsList, useCreateBudget, useUpdateBudget, useDeleteBudget } from '../../hooks/useBudgets';
import type { Budget } from '../../types/domain';
import { useCategoryColorMap } from '../../hooks/useCategoryColorMap';
import { Plus } from 'lucide-react';
import BudgetModal from './BudgetFormDrawer';
import { Button } from '../ui/Button';
import { Drawer } from '../ui/Drawer';
import { DistributionPieChart } from '../dashboard/DistributionPieChart';
import { BudgetList } from './BudgetList';

interface Props {
    isOpen: boolean;
    onClose: () => void;
    highlightCategory?: string;
    highlightId?: number;
}

export default function BudgetDrawer({ isOpen, onClose, highlightCategory, highlightId }: Props) {
    const { data: rawBudgets } = useBudgetsList();
    const { mutate: deleteBudget } = useDeleteBudget();
    const { mutateAsync: createBudget, isPending: isCreating } = useCreateBudget();
    const { mutateAsync: updateBudget, isPending: isUpdating } = useUpdateBudget();
    const { getCategoryColor } = useCategoryColorMap();

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingBudget, setEditingBudget] = useState<Budget | null>(null);
    
    // Refs for scroll elements
    const itemRefs = useRef<Record<string, HTMLDivElement | null>>({});

    // Scroll to highlight when drawer opens
    useEffect(() => {
        if (isOpen && rawBudgets) {
            let targetKey: string | undefined;

            if (highlightCategory) {
                // Find budget with this category
                const target = rawBudgets.find(b => b.Categoria === highlightCategory);
                if (target) targetKey = target.Categoria;
            } else if (highlightId) {
                const target = rawBudgets.find(b => b["ID Orcamento"] === highlightId);
                if (target) targetKey = target.Categoria;
            }

            if (targetKey && itemRefs.current[targetKey]) {
                 setTimeout(() => {
                    itemRefs.current[targetKey!]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    // Flash effect
                    itemRefs.current[targetKey!]?.classList.add('bg-white/5');
                    setTimeout(() => itemRefs.current[targetKey!]?.classList.remove('bg-white/5'), 1000);
                }, 300);
            }
        }
    }, [isOpen, highlightCategory, highlightId, rawBudgets]);

    // Sort budgets by Spent Amount (Descending) for color ranking
    const budgets = rawBudgets ? [...rawBudgets].sort((a, b) => (b['Valor Gasto Atual'] || 0) - (a['Valor Gasto Atual'] || 0)) : [];
    const totalBudgets = budgets.length;

    const handleSave = async (data: any) => {
        try {
            if (editingBudget && editingBudget["ID Orcamento"]) {
                await updateBudget({ id: editingBudget["ID Orcamento"], data });
            } else {
                await createBudget(data);
            }
            setIsModalOpen(false);
            setEditingBudget(null);
        } catch (error) {
            console.error(error);
        }
    };

    const handleDelete = (id?: number) => {
        if (!id) return;
        if (confirm("Tem certeza que deseja excluir este orçamento?")) {
            deleteBudget(id);
        }
    };

    const openNewModal = () => {
        setEditingBudget(null);
        setIsModalOpen(true);
    };

    const registerRef = (key: string, el: HTMLDivElement | null) => {
        itemRefs.current[key] = el;
    };

    const getInitialData = () => {
        if (!editingBudget) return undefined;
        return {
            categoria: editingBudget.Categoria,
            valor_limite: editingBudget['Valor Limite'],
            periodo: editingBudget['Período Orçamento'],
            observacoes: editingBudget.Observações || ''
        };
    };

    // Prepare data for Chart
    const chartData = budgets.map(b => ({
        name: b.Categoria,
        value: b['Valor Gasto Atual'] || 0
    }));

    return (
        <Drawer 
            isOpen={isOpen} 
            onClose={onClose} 
            title="Orçamentos"
            action={
                <Button 
                   onClick={openNewModal}
                   variant="primary"
                   size="icon"
                   title="Novo Orçamento"
                   icon={Plus}
               />
            }
        >
            <div className="flex flex-col md:flex-row h-full bg-transparent gap-4 md:gap-6 pb-4 md:pb-0">
                {/* Left Column: Chart (Desktop) / Top (Mobile) */}
                <div className="w-full md:w-5/12 flex-none flex flex-col gap-4">
                     {/* Reusing the Distribution Chart */}
                     <DistributionPieChart 
                        data={chartData} 
                        getCategoryColor={getCategoryColor} 
                     />
                    
                    {/* Desktop Only: Summary Box (Keep specific logic here as it differs from CategoryDrawer) */}
                    <div className="hidden md:block p-4 bg-surface-card/40 rounded-xl border border-border">
                         {(() => {
                            const totalLimit = budgets.reduce((acc, b) => acc + (b['Valor Limite'] || 0), 0);
                            const totalSpent = budgets.reduce((acc, b) => acc + (b['Valor Gasto Atual'] || 0), 0);
                            const progress = totalLimit > 0 ? (totalSpent / totalLimit) * 100 : 0;
                            
                            return (
                                <>
                                    <div className="flex justify-between items-center mb-2">
                                        <span className="text-sm text-text-muted">Total Comprometido</span>
                                        <span className="text-lg font-bold text-text-primary">
                                            {progress.toFixed(0)}%
                                        </span>
                                    </div>
                                    <div className="w-full bg-surface-hover rounded-full h-2 mb-2">
                                        <div 
                                            className={`h-full rounded-full transition-all duration-500 ${progress > 100 ? 'bg-danger' : 'bg-primary'}`}
                                            style={{ width: `${Math.min(progress, 100)}%` }}
                                        />
                                    </div>
                                    <div className="flex justify-between text-xs text-text-secondary">
                                        <span>Gasto: {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', notation: "compact" }).format(totalSpent)}</span>
                                        <span>Meta: {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', notation: "compact" }).format(totalLimit)}</span>
                                    </div>
                                </>
                            );
                        })()}
                    </div>
                </div>

                {/* Right Column: List (Desktop) / Bottom (Mobile) */}
                <div className="flex-1 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-border">
                    <BudgetList 
                        budgets={budgets}
                        highlightCategory={highlightCategory}
                        highlightId={highlightId}
                        getCategoryColor={getCategoryColor}
                        onEdit={(b) => { setEditingBudget(b); setIsModalOpen(true); }}
                        onDelete={handleDelete}
                        registerRef={registerRef}
                    />
                </div>

                <BudgetModal 
                    isOpen={isModalOpen}
                    onClose={() => setIsModalOpen(false)}
                    onSave={handleSave}
                    initialData={getInitialData()}
                    isLoading={isCreating || isUpdating}
                />
            </div>
        </Drawer>
    );
}
