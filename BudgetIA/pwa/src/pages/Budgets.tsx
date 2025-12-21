import { useState, useEffect } from 'react';
import { fetchAPI } from '../services/api';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { Plus, AlertTriangle, CheckCircle, Edit2, Trash2 } from 'lucide-react';
import BudgetModal from '../components/BudgetModal';

interface Budget {
    "ID Orcamento"?: number;
    Categoria: string;
    'Valor Limite': number;
    'Valor Gasto Atual': number;
    'Status Orçamento': string;
    'Período Orçamento': string;
    'Observações'?: string;
    [key: string]: any;
}

interface BudgetInput {
    categoria: string;
    valor_limite: number;
    periodo: string;
    observacoes: string;
}

const COLORS = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

export default function Budgets() {
    const [budgets, setBudgets] = useState<Budget[]>([]);
    const [loading, setLoading] = useState(true);

    // Modal State
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingBudget, setEditingBudget] = useState<Budget | null>(null);
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        loadBudgets();
    }, []);

    const loadBudgets = async () => {
         try {
            const data = await fetchAPI('/budgets/');
            if (data) setBudgets(data);
        } catch (error) {
            console.error("Error loading budgets", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async (data: BudgetInput) => {
        setIsSaving(true);
        try {
            if (editingBudget && editingBudget["ID Orcamento"]) {
                 // Update
                 await fetchAPI(`/budgets/${editingBudget["ID Orcamento"]}`, {
                    method: 'PUT',
                    body: JSON.stringify(data)
                 });
            } else {
                // Create
                await fetchAPI('/budgets/', {
                    method: 'POST',
                    body: JSON.stringify(data)
                });
            }
            await loadBudgets();
            setIsModalOpen(false);
            setEditingBudget(null);
        } catch (error) {
            console.error("Error saving budget", error);
            alert("Erro ao salvar orçamento.");
        } finally {
            setIsSaving(false);
        }
    };

    const handleDelete = async (id?: number) => {
        if (!id) return;
        if (!confirm("Tem certeza que deseja excluir este orçamento?")) return;

        try {
            await fetchAPI(`/budgets/${id}`, { method: 'DELETE' });
            // Optimistic update
            setBudgets(prev => prev.filter(b => b["ID Orcamento"] !== id));
        } catch (error) {
            console.error("Error deleting budget", error);
            alert("Erro ao excluir orçamento.");
        }
    };

    const openNewModal = () => {
        setEditingBudget(null);
        setIsModalOpen(true);
    };

    const openEditModal = (budget: Budget) => {
        setEditingBudget(budget);
        setIsModalOpen(true);
    };

    const getInitialData = (): BudgetInput | undefined => {
        if (!editingBudget) return undefined;
        return {
            categoria: editingBudget.Categoria,
            valor_limite: editingBudget['Valor Limite'],
            periodo: editingBudget['Período Orçamento'],
            observacoes: editingBudget.Observações || ''
        };
    };

    const calculateProgress = (current: number, limit: number) => {
        if (limit === 0) return 0;
        return Math.min((current / limit) * 100, 100);
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight text-white">Orçamentos</h2>
                    <p className="text-gray-400">Defina limites e acompanhe suas metas.</p>
                </div>
                <button 
                    onClick={openNewModal}
                    className="flex items-center justify-center space-x-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg transition-colors"
                >
                    <Plus size={20} />
                    <span>Novo Orçamento</span>
                </button>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {/* Budget Cards */}
                {loading ? (
                    <p className="text-gray-400">Carregando orçamentos...</p>
                ) : budgets.length === 0 ? (
                    <p className="text-gray-400">Nenhum orçamento ativo encontrado.</p>
                ) : (
                    budgets.map((budget, idx) => {
                        const progress = calculateProgress(budget['Valor Gasto Atual'], budget['Valor Limite']);
                        const isOver = budget['Valor Gasto Atual'] > budget['Valor Limite'];
                        const color = COLORS[idx % COLORS.length];

                        return (
                            <div key={idx} className="rounded-xl border border-gray-800 bg-gray-900/50 p-6 space-y-4 relative group">
                                <div className="absolute top-4 right-4 flex space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button 
                                        onClick={() => openEditModal(budget)}
                                        className="p-1 text-gray-400 hover:text-emerald-400"
                                    >
                                        <Edit2 size={16} />
                                    </button>
                                    <button 
                                        onClick={() => handleDelete(budget["ID Orcamento"])}
                                        className="p-1 text-gray-400 hover:text-red-400"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>

                                <div className="flex items-center justify-between pr-16">
                                    <h3 className="font-semibold text-lg text-white truncate">{budget.Categoria}</h3>
                                    <span className="text-xs font-medium bg-gray-800 text-gray-400 px-2 py-1 rounded-full">{budget['Período Orçamento']}</span>
                                </div>
                                
                                <div className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-gray-400">Gasto: <span className="text-white font-medium">{new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(budget['Valor Gasto Atual'])}</span></span>
                                        <span className="text-gray-400">Limite: <span className="text-white font-medium">{new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(budget['Valor Limite'])}</span></span>
                                    </div>
                                    <div className="h-2 w-full bg-gray-800 rounded-full overflow-hidden">
                                        <div 
                                            className="h-full transition-all duration-500 rounded-full"
                                            style={{ 
                                                width: `${progress}%`,
                                                backgroundColor: isOver ? '#EF4444' : color
                                            }}
                                        />
                                    </div>
                                    <div className="flex justify-end">
                                        {isOver ? (
                                            <span className="text-xs text-red-400 flex items-center font-medium"><AlertTriangle size={12} className="mr-1" /> Excedido</span>
                                        ) : (
                                            <span className="text-xs text-emerald-400 flex items-center font-medium"><CheckCircle size={12} className="mr-1" /> Dentro da meta</span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )
                    })
                )}
            </div>

             {/* Distribution Chart */}
             {!loading && budgets.length > 0 && (
                <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6 min-h-[400px]">
                    <h3 className="text-lg font-semibold text-white mb-6">Distribuição de Metas</h3>
                    <div className="h-[300px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={budgets}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={100}
                                    paddingAngle={5}
                                    dataKey="Valor Limite"
                                    nameKey="Categoria"
                                >
                                    {budgets.map((_entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip 
                                    contentStyle={{ backgroundColor: '#1F2937', border: 'none', borderRadius: '8px', color: '#fff' }}
                                    formatter={(value: any) => {
                                        if (typeof value !== 'number') return [value, "Valor Limite"];
                                        return [new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value), "Valor Limite"];
                                    }}
                                    itemStyle={{ color: '#fff' }}
                                />
                                <Legend />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>
             )}

             <BudgetModal 
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSave={handleSave}
                initialData={getInitialData()}
                isLoading={isSaving}
             />
        </div>
    );
}
