import { useMemo } from 'react';
import { useCategoryColorMap } from '../../hooks/useCategoryColorMap';
import { useExpenses } from '../../hooks/useDashboard';
import { Drawer } from '../ui/Drawer';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { TRANSACTION_CATEGORIES } from '../../utils/constants';
import { ProgressListItem } from '../ui/ProgressListItem';

interface Props {
    isOpen: boolean;
    onClose: () => void;
}

export default function CategoryDrawer({ isOpen, onClose }: Props) {
    const { getCategoryColor } = useCategoryColorMap();
    // Fetch top 50 categories 
    const { data: expenses } = useExpenses(50);
    
    // Sort logic that includes ALL categories for debugging/verification
    const sortedData = useMemo(() => {
        const activeExpenses = expenses || [];
        const activeNames = new Set(activeExpenses.map(e => e.name));
        
        // Create entries for 0-value categories from the standard list
        const zeroExpenses = TRANSACTION_CATEGORIES
            .filter(cat => !activeNames.has(cat))
            .map(cat => ({ name: cat, value: 0 }));
            
        // Combine and Sort
        const all = [...activeExpenses, ...zeroExpenses];
        
        // Sort by Value (Desc), then Name (Asc)
        return all.sort((a, b) => {
            if (b.value !== a.value) return b.value - a.value;
            return a.name.localeCompare(b.name);
        });
    }, [expenses]);

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
                        <div className="h-[250px] md:h-[350px] w-full bg-gray-900/40 rounded-xl border border-gray-800 p-2 flex items-center justify-center">
                             <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={pieData}
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
                                        contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '8px', color: '#F3F4F6' }}
                                        itemStyle={{ color: '#F3F4F6' }}
                                        formatter={(value: any) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)}
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    ) : (
                        <div className="h-[250px] w-full bg-gray-900/40 rounded-xl border border-gray-800 flex items-center justify-center text-gray-500">
                            Sem dados para exibir
                        </div>
                    )}
                    
                    {/* Desktop Only: Summary Box or Legend could go here */}
                    <div className="hidden md:block p-4 bg-gray-900/40 rounded-xl border border-gray-800">
                        <div className="flex justify-between items-center mb-2">
                            <span className="text-sm text-gray-400">Total Despesas</span>
                            <span className="text-lg font-bold text-white">
                                {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(totalExpenses)}
                            </span>
                        </div>
                        <div className="text-xs text-gray-500">
                            Top {pieData.length} categorias representadas
                        </div>
                    </div>
                </div>

                {/* Right Column: List (Desktop) / Bottom (Mobile) */}
                <div className="flex-1 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-800">
                    <div className="space-y-2">
                        {sortedData.length > 0 ? (
                            sortedData.map((cat, idx) => {
                                const color = getCategoryColor(cat.name);
                                
                                return (
                                    <ProgressListItem
                                        key={cat.name}
                                        title={cat.name}
                                        color={color}
                                        value={cat.value}
                                        totalReference={totalExpenses}
                                    />
                                );
                            })
                        ) : (
                            <div className="text-center text-gray-500 py-8">
                                Nenhuma categoria encontrada.
                            </div>
                        )}
                    </div>
                </div>
             </div>
        </Drawer>
    );
}
