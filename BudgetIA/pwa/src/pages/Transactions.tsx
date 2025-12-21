import { useState, useEffect } from 'react';
import { fetchAPI } from '../services/api';
import { Plus, Search, Filter, Edit2, Trash2, ArrowUpCircle, ArrowDownCircle } from 'lucide-react';
import { cn } from '../utils/cn';
import TransactionModal from '../components/TransactionModal';

interface Transaction {
    "ID Transacao"?: number;
    Data: string;
    Descricao: string;
    Valor: number;
    Tipo: string;
    Categoria: string;
    Status: string;
}

// Interface usada pelo Modal (lowercase)
interface TransactionInput {
    data: string;
    descricao: string;
    valor: number;
    tipo: 'Receita' | 'Despesa';
    categoria: string;
    status: string;
}

export default function Transactions() {
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    
    // Modal State
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingTx, setEditingTx] = useState<Transaction | null>(null);
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        loadTransactions();
    }, []);

    const loadTransactions = async () => {
        try {
            const data = await fetchAPI('/transactions?limit=100');
            if (data) setTransactions(data);
        } catch (error) {
            console.error("Error loading transactions", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async (data: TransactionInput) => {
        setIsSaving(true);
        try {
            if (editingTx && editingTx["ID Transacao"]) {
                // Edit existing
                await fetchAPI(`/transactions/${editingTx["ID Transacao"]}`, {
                    method: 'PUT',
                    body: JSON.stringify(data)
                });
            } else {
                // Create new
                await fetchAPI('/transactions/', {
                    method: 'POST',
                    body: JSON.stringify(data)
                });
            }
            // Reload list
            await loadTransactions();
            setIsModalOpen(false);
            setEditingTx(null);
        } catch (error) {
            console.error("Error saving transaction", error);
            alert("Erro ao salvar transação. Verifique o console.");
        } finally {
            setIsSaving(false);
        }
    };

    const handleDelete = async (id?: number) => {
        if (!id) return;
        if (!confirm("Tem certeza que deseja excluir esta transação?")) return;

        try {
            await fetchAPI(`/transactions/${id}`, { method: 'DELETE' });
            // Optimistic update or reload
            setTransactions(prev => prev.filter(tx => tx["ID Transacao"] !== id));
        } catch (error) {
            console.error("Error deleting transaction", error);
            alert("Erro ao excluir transação.");
        }
    };

    const openNewModal = () => {
        setEditingTx(null);
        setIsModalOpen(true);
    };

    const openEditModal = (tx: Transaction) => {
        setEditingTx(tx);
        setIsModalOpen(true);
    };

    const filteredTransactions = transactions.filter(tx => 
        tx.Descricao.toLowerCase().includes(searchTerm.toLowerCase()) || 
        tx.Categoria.toLowerCase().includes(searchTerm.toLowerCase())
    );

    // Helper to convert Transaction (API) to TransactionInput (Modal)
    const getInitialData = (): TransactionInput | undefined => {
        if (!editingTx) return undefined;
        return {
            data: editingTx.Data ? new Date(editingTx.Data).toISOString().split('T')[0] : '', // Safe conversion
            descricao: editingTx.Descricao,
            valor: editingTx.Valor,
            tipo: editingTx.Tipo as 'Receita' | 'Despesa',
            categoria: editingTx.Categoria,
            status: editingTx.Status
        };
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight text-white">Transações</h2>
                    <p className="text-gray-400">Gerencie suas entradas e saídas.</p>
                </div>
                <button 
                    onClick={openNewModal}
                    className="flex items-center justify-center space-x-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg transition-colors"
                >
                    <Plus size={20} />
                    <span>Nova Transação</span>
                </button>
            </div>

            {/* Filters */}
            <div className="flex items-center space-x-4 bg-gray-900/50 p-4 rounded-xl border border-gray-800">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={20} />
                    <input 
                        type="text" 
                        placeholder="Buscar por descrição ou categoria..." 
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full bg-gray-950 border border-gray-700 text-white rounded-lg pl-10 pr-4 py-2 focus:outline-none focus:border-emerald-500 transition-colors"
                    />
                </div>
                <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
                    <Filter size={20} />
                </button>
            </div>

            {/* Table */}
            <div className="bg-gray-900/50 border border-gray-800 rounded-xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm text-gray-400">
                        <thead className="bg-gray-900 text-gray-200 font-medium uppercase text-xs">
                            <tr>
                                <th className="px-6 py-4">Data</th>
                                <th className="px-6 py-4">Descrição</th>
                                <th className="px-6 py-4">Categoria</th>
                                <th className="px-6 py-4">Valor</th>
                                <th className="px-6 py-4">Status</th>
                                <th className="px-6 py-4 text-right">Ações</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-800">
                             {loading ? (
                                <tr><td colSpan={6} className="text-center py-8">Carregando...</td></tr>
                            ) : filteredTransactions.length === 0 ? (
                                <tr><td colSpan={6} className="text-center py-8">Nenhuma transação encontrada.</td></tr>
                            ) : (
                                filteredTransactions.map((tx, idx) => (
                                    <tr key={idx} className="hover:bg-gray-800/50 transition-colors">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            {tx.Data ? new Date(tx.Data).toLocaleDateString() : '-'}
                                        </td>
                                        <td className="px-6 py-4 font-medium text-white">{tx.Descricao}</td>
                                        <td className="px-6 py-4">
                                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-800 text-gray-300">
                                                {tx.Categoria}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center space-x-2">
                                                 {tx.Tipo === "Receita" ? <ArrowUpCircle size={16} className="text-blue-400" /> : <ArrowDownCircle size={16} className="text-red-400" />}
                                                 <span className={cn("font-bold", tx.Tipo === "Receita" ? "text-blue-400" : "text-red-400")}>
                                                    {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(tx.Valor)}
                                                 </span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={cn(
                                                "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
                                                tx.Status === "Concluído" ? "bg-emerald-500/10 text-emerald-400" : "bg-yellow-500/10 text-yellow-400"
                                            )}>
                                                {tx.Status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="flex items-center justify-end space-x-2">
                                                <button 
                                                    onClick={() => openEditModal(tx)}
                                                    className="p-1 hover:text-emerald-400 transition-colors"
                                                    title="Editar"
                                                >
                                                    <Edit2 size={16} />
                                                </button>
                                                <button 
                                                    onClick={() => handleDelete(tx["ID Transacao"])}
                                                    className="p-1 hover:text-red-400 transition-colors" 
                                                    title="Excluir"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            <TransactionModal 
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSave={handleSave}
                initialData={getInitialData()}
                isLoading={isSaving}
            />
        </div>
    );
}
