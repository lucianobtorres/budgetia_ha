import { useState, useRef, useEffect } from 'react';
import { useBudgetsList, useCreateBudget, useUpdateBudget, useDeleteBudget, type Budget } from '../../hooks/useBudgets';
import { useCategoryColorMap } from '../../hooks/useCategoryColorMap';
import { Plus } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import BudgetModal from './BudgetFormDrawer';
import { Button } from '../ui/Button';
import { Drawer } from '../ui/Drawer';
import { ProgressListItem } from '../ui/ProgressListItem';

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

    const getInitialData = () => {
        if (!editingBudget) return undefined;
        return {
            categoria: editingBudget.Categoria,
            valor_limite: editingBudget['Valor Limite'],
            periodo: editingBudget['Período Orçamento'],
            observacoes: editingBudget.Observações || ''
        };
    };

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
                     {totalBudgets > 0 ? (
                        <div className="h-[250px] md:h-[350px] w-full bg-surface-card/40 rounded-xl border border-border p-2 flex items-center justify-center">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={budgets}
                                        dataKey="Valor Gasto Atual"
                                        nameKey="Categoria"
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={90}
                                        paddingAngle={3}
                                        cornerRadius={4}
                                    >
                                        {budgets.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={getCategoryColor(entry.Categoria)} stroke="rgba(0,0,0,0.1)" strokeWidth={1} />
                                        ))}
                                    </Pie>
                                    <Tooltip 
                                        contentStyle={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: '8px', color: 'var(--color-text-primary)' }}
                                        itemStyle={{ color: 'var(--color-text-primary)' }}
                                        formatter={(value: any) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)}
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    ) : (
                        <div className="h-[250px] w-full bg-surface-card/40 rounded-xl border border-border flex items-center justify-center text-text-muted">
                             Nenhum orçamento definido
                        </div>
                    )}
                    
                    {/* Desktop Only: Summary Box */}
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
                    <div className="space-y-2">
                        {budgets.length === 0 ? (
                            <div className="text-center py-10 text-text-muted">
                                <p>Nenhum orçamento definido.</p>
                                <p className="text-sm">Clique em "+" para começar.</p>
                            </div>
                        ) : (
                            budgets.map((budget, idx) => {
                                const isHighlighted = (highlightCategory && budget.Categoria === highlightCategory) || 
                                                      (highlightId && budget["ID Orcamento"] === highlightId);
                                
                                return (
                                    <div 
                                        key={idx} 
                                        ref={el => { itemRefs.current[budget.Categoria] = el; }}
                                        className={`transition-colors rounded-xl ${isHighlighted ? 'bg-white/10 ring-1 ring-white/20' : ''}`}
                                    >
                                        <ProgressListItem
                                            title={budget.Categoria}
                                            subtitle={budget['Período Orçamento']}
                                            color={getCategoryColor(budget.Categoria)}
                                            value={budget['Valor Gasto Atual'] || 0}
                                            limit={budget['Valor Limite'] || 0}
                                            onEdit={() => { setEditingBudget(budget as Budget); setIsModalOpen(true); }}
                                            onDelete={() => handleDelete(budget["ID Orcamento"])}
                                        />
                                    </div>
                                )
                            })
                        )}
                    </div>
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
