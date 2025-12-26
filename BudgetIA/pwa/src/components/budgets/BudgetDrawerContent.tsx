import { useState } from 'react';
import { useBudgetsList, useCreateBudget, useUpdateBudget, useDeleteBudget, type Budget } from '../../hooks/useBudgets';
import { useCategoryColorMap } from '../../hooks/useCategoryColorMap';
import { Plus, Edit2, Trash2, AlertTriangle } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import BudgetModal from './BudgetFormDrawer';
import { Button } from '../ui/Button';
import { Drawer } from '../ui/Drawer';
import { ProgressListItem } from '../ui/ProgressListItem';

interface Props {
    isOpen: boolean;
    onClose: () => void;
}

export default function BudgetDrawer({ isOpen, onClose }: Props) {
    const { data: rawBudgets } = useBudgetsList();
    const { mutate: deleteBudget } = useDeleteBudget();
    const { mutateAsync: createBudget } = useCreateBudget();
    const { mutateAsync: updateBudget } = useUpdateBudget();
    const { getCategoryColor } = useCategoryColorMap();

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingBudget, setEditingBudget] = useState<Budget | null>(null);

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
                        <div className="h-[250px] md:h-[350px] w-full bg-gray-900/40 rounded-xl border border-gray-800 p-2 flex items-center justify-center">
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
                                        contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '8px', color: '#F3F4F6' }}
                                        itemStyle={{ color: '#F3F4F6' }}
                                        formatter={(value: any) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)}
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    ) : (
                        <div className="h-[250px] w-full bg-gray-900/40 rounded-xl border border-gray-800 flex items-center justify-center text-gray-500">
                             Nenhum orçamento definido
                        </div>
                    )}
                    
                    {/* Desktop Only: Summary Box */}
                    <div className="hidden md:block p-4 bg-gray-900/40 rounded-xl border border-gray-800">
                         {(() => {
                            const totalLimit = budgets.reduce((acc, b) => acc + (b['Valor Limite'] || 0), 0);
                            const totalSpent = budgets.reduce((acc, b) => acc + (b['Valor Gasto Atual'] || 0), 0);
                            const progress = totalLimit > 0 ? (totalSpent / totalLimit) * 100 : 0;
                            
                            return (
                                <>
                                    <div className="flex justify-between items-center mb-2">
                                        <span className="text-sm text-gray-400">Total Comprometido</span>
                                        <span className="text-lg font-bold text-white">
                                            {progress.toFixed(0)}%
                                        </span>
                                    </div>
                                    <div className="w-full bg-gray-800 rounded-full h-2 mb-2">
                                        <div 
                                            className={`h-full rounded-full transition-all duration-500 ${progress > 100 ? 'bg-red-500' : 'bg-emerald-500'}`}
                                            style={{ width: `${Math.min(progress, 100)}%` }}
                                        />
                                    </div>
                                    <div className="flex justify-between text-xs text-gray-500">
                                        <span>Gasto: {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', notation: "compact" }).format(totalSpent)}</span>
                                        <span>Meta: {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', notation: "compact" }).format(totalLimit)}</span>
                                    </div>
                                </>
                            );
                        })()}
                    </div>
                </div>

                {/* Right Column: List (Desktop) / Bottom (Mobile) */}
                <div className="flex-1 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-800">
                    <div className="space-y-2">
                        {budgets.length === 0 ? (
                            <div className="text-center py-10 text-gray-400">
                                <p>Nenhum orçamento definido.</p>
                                <p className="text-sm">Clique em "+" para começar.</p>
                            </div>
                        ) : (
                            budgets.map((budget, idx) => {
                                return (
                                    <ProgressListItem
                                        key={idx}
                                        title={budget.Categoria}
                                        subtitle={budget['Período Orçamento']}
                                        color={getCategoryColor(budget.Categoria)}
                                        value={budget['Valor Gasto Atual'] || 0}
                                        limit={budget['Valor Limite'] || 0}
                                        onEdit={() => { setEditingBudget(budget as Budget); setIsModalOpen(true); }}
                                        onDelete={() => handleDelete(budget["ID Orcamento"])}
                                    />
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
                />
            </div>
        </Drawer>
    );
}
