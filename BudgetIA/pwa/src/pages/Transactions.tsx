import { useState } from "react";
import { useTransactions, useDeleteTransaction, useCreateTransaction, useUpdateTransaction, type Transaction } from "../hooks/useTransactions";
import { useCategoryColorMap } from "../hooks/useCategoryColorMap";
import { TransactionCard } from "../components/transactions/TransactionCard";
import TransactionModal from "../components/transactions/TransactionFormDrawer";
import { Skeleton } from "../components/ui/Skeleton";
import { Filter, Search, Plus } from "lucide-react";
import { PageHeader } from "../components/ui/PageHeader";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { EmptyState } from "../components/ui/EmptyState";


export default function Transactions() {
    // Current date for default filter
    const now = new Date();
    // Use string to handle "all" option
    const [filterValue, setFilterValue] = useState<string>(`${now.getFullYear()}-${now.getMonth() + 1}`);
    const [searchTerm, setSearchTerm] = useState("");
    
    // Modal State
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingTx, setEditingTx] = useState<Transaction | null>(null);

    // Parse filter value
    const isAll = filterValue === 'all';
    const [selectedYear, selectedMonth] = isAll 
        ? [undefined, undefined] 
        : filterValue.split('-').map(Number);

    const { data: transactions, isLoading } = useTransactions({ 
        month: selectedMonth, 
        year: selectedYear,
        limit: 1000 // Ensure we get enough recent ones if viewing all
    });
    // Fetch global rank-based colors
    const { getCategoryColor } = useCategoryColorMap();

    const { mutate: deleteTransaction } = useDeleteTransaction();
    const { mutateAsync: createTransaction } = useCreateTransaction();
    const { mutateAsync: updateTransaction } = useUpdateTransaction();

    // Category sorting is handled by backend or default, color is now hash-based.
    // No need for complex rank calculation here.

    const filteredTransactions = transactions?.filter(t => 
        t.Descricao.toLowerCase().includes(searchTerm.toLowerCase()) || 
        t.Categoria.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const handleFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setFilterValue(e.target.value);
    };

    const handleSave = async (data: any) => {
        try {
            if (editingTx) {
                 await updateTransaction({ id: editingTx["ID Transacao"], data });
            } else {
                 await createTransaction(data);
            }
            setIsModalOpen(false);
            setEditingTx(null);
        } catch (error) {
            console.error("Erro ao salvar:", error);
        }
    };

    const handleEdit = (tx: Transaction) => {
        setEditingTx(tx);
        setIsModalOpen(true);
    };

    // Generate last 12 months for selector
    const months = Array.from({ length: 12 }, (_, i) => {
        const d = new Date();
        d.setMonth(d.getMonth() - i);
        return {
            value: `${d.getFullYear()}-${d.getMonth() + 1}`,
            label: d.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })
        };
    });

    const initialFormData = editingTx ? {
        data: editingTx.Data,
        descricao: editingTx.Descricao,
        valor: editingTx.Valor,
        tipo: editingTx["Tipo (Receita/Despesa)"],
        categoria: editingTx.Categoria,
        status: editingTx.Status
    } : undefined;

    return (
        <div className="h-full flex flex-col gap-4 overflow-hidden">
            {/* Header - Fixed */}
            <PageHeader
                title="Transações"
                description="Gerencie suas receitas e despesas."
                action={
                    <Button 
                        onClick={() => { setEditingTx(null); setIsModalOpen(true); }}
                        variant="primary"
                        size="icon"
                        className="rounded-xl shadow-lg hover:bg-emerald-600 transition-colors"
                        icon={Plus}
                    />
                }
            />

                {/* Filters Row */}
                <div className="flex items-center gap-2">
                    {/* Month Select */}
                    <div className="relative flex-1 max-w-[180px]">
                        <div className="absolute inset-y-0 left-2 flex items-center pointer-events-none text-gray-400">
                             <Filter size={14} />
                        </div>
                        <select 
                            value={filterValue}
                            onChange={handleFilterChange}
                            className="w-full pl-8 pr-4 py-2 bg-gray-900 border border-gray-800 rounded-xl text-sm text-white appearance-none focus:border-emerald-500 outline-none capitalize transition-colors"
                        >
                            <option value="all">Ver Tudo</option>
                            {months.map(m => (
                                <option key={m.value} value={m.value}>{m.label}</option>
                            ))}
                        </select>
                    </div>

                    {/* Search Input */}
                    <div className="relative flex-1">
                        <Input 
                            type="text" 
                            placeholder="Buscar..." 
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            icon={Search}
                        />
                    </div>
                </div>


            {/* List - Scrollable */}
            <div className="flex-1 overflow-y-auto scrollbar-none pb-20">
                {isLoading ? (
                    <div className="space-y-3">
                         {[1,2,3,4,5].map(i => (
                             <div key={i} className="flex items-center gap-3 p-3 bg-gray-900/30 rounded-xl border border-gray-800/50">
                                 <Skeleton className="h-12 w-12 rounded-lg" />
                                 <div className="flex-1 space-y-1">
                                     <Skeleton className="h-4 w-3/4" />
                                     <Skeleton className="h-3 w-1/4" />
                                 </div>
                             </div>
                         ))}
                    </div>
                ) : (
                    <div className="space-y-1">
                        {filteredTransactions && filteredTransactions.length > 0 ? (
                            filteredTransactions.map(t => (
                                <TransactionCard 
                                    key={t["ID Transacao"]} 
                                    transaction={t} 
                                    categoryColor={getCategoryColor(t.Categoria)}
                                    onDelete={(id) => {
                                        if (window.confirm("Tem certeza que deseja excluir esta transação?")) {
                                            deleteTransaction(id);
                                        }
                                    }} 
                                    onEdit={handleEdit}
                                />
                            ))
                        ) : (
                            <EmptyState 
                                title="Nenhuma transação encontrada"
                                description={searchTerm ? "Nenhum resultado para sua busca." : "Você ainda não possui transações neste período."}
                                icon={Search}
                                className="h-[300px]"
                                actionLabel={!searchTerm ? "Adicionar Transação" : undefined}
                                onAction={!searchTerm ? () => { setEditingTx(null); setIsModalOpen(true); } : undefined}
                            />
                        )}
                    </div>
                )}
            </div>
            
            <TransactionModal 
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSave={handleSave}
                initialData={initialFormData}
            />
        </div>
    );
}
