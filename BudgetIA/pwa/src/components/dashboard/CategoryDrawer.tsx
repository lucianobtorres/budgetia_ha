import { useNavigate } from 'react-router-dom';
import { useMemo, useEffect, useRef } from 'react';
import { useCategoryColorMap } from '../../hooks/useCategoryColorMap';
import { useExpenses } from '../../hooks/useDashboard';
import { useBudgetsList } from '../../hooks/useBudgets';
import { useDrawer } from '../../context/DrawerContext';
import { Drawer } from '../ui/Drawer';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { TRANSACTION_CATEGORIES } from '../../utils/constants';
import { ProgressListItem } from '../ui/ProgressListItem';
import { Target, CreditCard } from 'lucide-react';

interface Props {
    isOpen: boolean;
    onClose: () => void;
    highlightCategory?: string;
}

export default function CategoryDrawer({ isOpen, onClose, highlightCategory }: Props) {
    const { getCategoryColor } = useCategoryColorMap();
    const { openDrawer } = useDrawer(); // Global navigation
    const navigate = useNavigate();
    // Fetch top 50 categories 
    const { data: expenses } = useExpenses(50);
    const { data: budgets } = useBudgetsList(); // Fetch budgets to check existence
    
    // Refs for scroll elements
    const itemRefs = useRef<Record<string, HTMLDivElement | null>>({});

    // Scroll to highlightCategory when drawer opens
    useEffect(() => {
        if (isOpen && highlightCategory && itemRefs.current[highlightCategory]) {
            setTimeout(() => {
                itemRefs.current[highlightCategory]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                // Optional: Flash effect
                itemRefs.current[highlightCategory]?.classList.add('bg-white/5');
                setTimeout(() => itemRefs.current[highlightCategory]?.classList.remove('bg-white/5'), 1000);
            }, 300); // Small delay for drawer animation
        }
    }, [isOpen, highlightCategory]);
    
    // Sort logic that includes ALL categories for debugging/verification
    const sortedData = useMemo(() => {
        const activeExpenses = expenses || [];
        const activeNames = new Set(activeExpenses.map(e => e.name));
        
        // Create entries for 0-value categories from the standard list
        const zeroExpenses = TRANSACTION_CATEGORIES
            .filter(cat => !activeNames.has(cat))
            .map(cat => ({ 
                name: cat, 
                value: 0, 
                date: '', 
                type: 'Despesa' as const, 
                amount: 0, 
                id: 0, 
                category: cat 
            }));
            
        // Combine and Sort
        const all = [...activeExpenses, ...zeroExpenses];
        
        // Sort by Value (Desc), then Name (Asc)
        return all.sort((a, b) => {
            if (b.value !== a.value) return b.value - a.value;
            return a.name.localeCompare(b.name);
        });
    }, [expenses]);

    // Helper to check if budget exists
    const getBudgetForCategory = (category: string) => {
        return budgets?.find(b => b.Categoria === category);
    };

    const handleBudgetClick = (category: string) => {
        // Switch to Budget Drawer
        onClose(); // Close current
        setTimeout(() => {
             openDrawer('BUDGETS', { highlightCategory: category });
        }, 150); // Small delay to allow close animation start
    };

    const handleTransactionsClick = (category: string) => {
        navigate('/transactions', { state: { initialCategory: category } });
        onClose();
    };

    // Valid data for Pie Chart (only > 0)
    const pieData = sortedData.filter(c => c.value > 0);
    const totalExpenses = pieData.reduce((acc, c) => acc + c.value, 0);

    return (
        <Drawer 
            isOpen={isOpen} 
            onClose={onClose} 
            title="Despesas por Categoria"
        >
             <div className="flex flex-col md:flex-row h-full bg-transparent gap-4 md:gap-6 pb-4 md:pb-0">
                {/* Left Column: Chart (Desktop) / Top (Mobile) */}
                <div className="w-full md:w-5/12 flex-none flex flex-col gap-4">
                     {pieData.length > 0 ? (
                        <div className="h-[250px] md:h-[350px] w-full bg-surface-card/40 rounded-xl border border-border p-2 flex items-center justify-center">
                             <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={pieData as any[]}
                                        dataKey="value"
                                        nameKey="name"
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={90}
                                        paddingAngle={3}
                                        cornerRadius={4}
                                    >
                                        {pieData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={getCategoryColor(entry.name)} stroke="rgba(0,0,0,0.1)" strokeWidth={1} />
                                        ))}
                                    </Pie>
                                    <Tooltip 
                                        contentStyle={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: '8px', color: 'var(--color-text-primary)' }}
                                        itemStyle={{ color: 'var(--color-text-primary)' }}
                                        formatter={(value: number) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value || 0)}
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    ) : (
                        <div className="h-[250px] w-full bg-surface-card/40 rounded-xl border border-border flex items-center justify-center text-text-muted">
                            Sem dados para exibir
                        </div>
                    )}
                    
                    {/* Desktop Only: Summary Box or Legend could go here */}
                    <div className="hidden md:block p-4 bg-surface-card/40 rounded-xl border border-border">
                        <div className="flex justify-between items-center mb-2">
                            <span className="text-sm text-text-muted">Total Despesas</span>
                            <span className="text-lg font-bold text-text-primary">
                                {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(totalExpenses)}
                            </span>
                        </div>
                        <div className="text-xs text-text-muted">
                            Top {pieData.length} categorias representadas
                        </div>
                    </div>
                </div>

                {/* Right Column: List (Desktop) / Bottom (Mobile) */}
                <div className="flex-1 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-border">
                    <div className="space-y-2">
                        {sortedData.length > 0 ? (
                            sortedData.map((cat) => {
                                const color = getCategoryColor(cat.name);
                                const hasBudget = !!getBudgetForCategory(cat.name);
                                const isHighlighted = highlightCategory === cat.name;
                                
                                return (
                                    <div 
                                        key={cat.name} 
                                        ref={el => { if(itemRefs.current) itemRefs.current[cat.name] = el }}
                                        className={`transition-colors rounded-xl ${isHighlighted ? 'bg-surface-hover ring-1 ring-border-hover' : ''}`}
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
                                                            onClick={() => handleBudgetClick(cat.name)}
                                                            className="p-1.5 text-text-secondary hover:text-primary-light hover:bg-surface-hover rounded-md transition-colors"
                                                            title="Ver Orçamento"
                                                        >
                                                            <Target size={14} />
                                                        </button>
                                                    )}
                                                    {cat.value > 0 && (
                                                        <button
                                                            onClick={() => handleTransactionsClick(cat.name)}
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
                            })
                        ) : (
                            <div className="text-center text-text-muted py-8">
                                Nenhuma categoria encontrada.
                            </div>
                        )}
                    </div>
                </div>
             </div>
        </Drawer>
    );
}
