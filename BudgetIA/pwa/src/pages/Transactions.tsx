import { useState, useEffect, useRef } from "react";
import { useTransactions, useDeleteTransaction, useCreateTransaction, useUpdateTransaction } from "../hooks/useTransactions";
import type { Transaction } from "../domain/models/Transaction";
import { usePageTour } from "../hooks/usePageTour";
import { useCategoryColorMap } from "../hooks/useCategoryColorMap";
import { TransactionCard } from "../components/transactions/TransactionCard";
import TransactionModal from "../components/transactions/TransactionFormDrawer";
import { Skeleton } from "../components/ui/Skeleton";
import { Filter, Search, Plus, Camera, UploadCloud } from "lucide-react";
import { useLocation } from "react-router-dom";
import { PageHeader } from "../components/ui/PageHeader";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Select } from "../components/ui/Select";
import type { SelectChangeEvent } from "../components/ui/Select";
import { EmptyState } from "../components/ui/EmptyState";
import { OCRModal } from "../components/ocr/OCRModal";

import { useDrawer } from "../hooks/useDrawer";
import { ImportDrawer } from "../components/transactions/ImportDrawer";
import { LoadingOverlay } from "../components/ui/LoadingOverlay";
import { fetchAPI } from "../services/api";
import type { TransactionCreate } from "../types/api";

export default function Transactions() {
    const { openDrawer } = useDrawer();
    const location = useLocation();

    // Current date for default filter
    const now = new Date();
    // Use string to handle "all" option
    const [filterValue, setFilterValue] = useState<string>(`${now.getFullYear()}-${now.getMonth() + 1}`);
    const [searchTerm, setSearchTerm] = useState("");

    // Initial Category from navigation state
    const [categoryFilter, setCategoryFilter] = useState<string>(location.state?.initialCategory || 'all');
    
    // Standardized Tour Hook
    usePageTour('transactions_walkthrough');

    // Parse filter value
    const isAll = filterValue === 'all';
    const [selectedYear, selectedMonth] = isAll 
        ? [undefined, undefined] 
        : filterValue.split('-').map(Number);

    const { data: transactions, isLoading } = useTransactions({ 
        month: selectedMonth, 
        year: selectedYear,
        limit: 1000
    });
    
    const { getCategoryColor } = useCategoryColorMap();

    const { mutate: deleteTransaction, isPending: isDeleting } = useDeleteTransaction();
    const { mutateAsync: createTransaction, isPending: isCreating } = useCreateTransaction();
    const { mutateAsync: updateTransaction, isPending: isUpdating } = useUpdateTransaction();

    // Modal State
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isImportOpen, setIsImportOpen] = useState(false);
    const [isOCROpen, setIsOCROpen] = useState(false);
    const [editingTx, setEditingTx] = useState<Transaction | null>(null);
    const [ocrData, setOcrData] = useState<TransactionCreate | null>(null);
    const [ocrAvailable, setOcrAvailable] = useState(false); // Check availability
    
    // Check OCR Availability
    useEffect(() => {
        fetchAPI<{ available: boolean }>('/ocr/status')
            .then(res => setOcrAvailable(res?.available ?? false))
            .catch(() => setOcrAvailable(false));
    }, []);

    const uniqueCategories = Array.from(new Set(transactions?.map(t => t.category) || [])).sort();

    // Smart Navigation Handler
    const navHandledRef = useRef(false);
    useEffect(() => {
        const initialCategory = location.state?.initialCategory;
        if (!navHandledRef.current && initialCategory) {
            if (initialCategory !== categoryFilter) {
                // eslint-disable-next-line react-hooks/set-state-in-effect
                setCategoryFilter(initialCategory);
            }
            
            // If category is not in current view (e.g. filtered by month), switch to 'all'
            if (transactions && filterValue !== 'all') {
                const hasCategory = transactions.some(t => t.category === initialCategory);
                if (!hasCategory) {
                    setFilterValue('all');
                }
            }
            navHandledRef.current = true;
        }
    }, [location.state, transactions, filterValue, categoryFilter]);

    const filteredTransactions = transactions?.filter(t => {
        const matchesSearch = t.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                              t.category.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesCategory = categoryFilter === 'all' || t.category === categoryFilter;
        return matchesSearch && matchesCategory;
    });

    const handleFilterChange = (e: SelectChangeEvent) => {
        setFilterValue(e.target.value);
    };

    const handleEdit = (tx: Transaction) => {
        setEditingTx(tx);
        setOcrData(null);
        setIsModalOpen(true);
    };

    const handleCategoryClick = (category: string) => {
        openDrawer('CATEGORY_EXPENSES', { highlightCategory: category });
    };

    const handleSave = async (data: TransactionCreate) => {
        try {
            if (editingTx) {
                 await updateTransaction({ id: editingTx.id, data });
            } else {
                 await createTransaction(data);
            }
            setIsModalOpen(false);
            setEditingTx(null);
            setOcrData(null);
        } catch (err: unknown) {
            console.error("Erro ao salvar:", err);
        }
    };

    const handleOCRSuccess = (data: TransactionCreate) => {
        setOcrData(data);
        setEditingTx(null); // Ensure we are not in edit mode
        setIsOCROpen(false); // Close OCR modal
        setIsModalOpen(true); // Open Transaction Form
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
        data: editingTx.date,
        descricao: editingTx.description,
        valor: editingTx.value,
        tipo: editingTx.type,
        categoria: editingTx.category,
        status: editingTx.status
    } : ocrData; // Use OCR data if available

    return (
        <div className="h-full flex flex-col gap-4 overflow-hidden">
            <LoadingOverlay isVisible={isDeleting} message="Excluindo transação..." />

            {/* Header - Fixed */}
            <div id="tx-header">
                <PageHeader
                    title="Transações"
                    description="Gerencie suas receitas e despesas."
                    action={
                        <div className="flex gap-2">
                             <Button 
                                onClick={() => setIsOCROpen(true)}
                                variant="outline" 
                                size="icon"
                                disabled={!ocrAvailable}
                                className={`rounded-xl shadow-lg border-emerald-500/20 transition-colors ${
                                    ocrAvailable 
                                    ? "hover:bg-emerald-500/10 hover:text-emerald-400 text-emerald-500" 
                                    : "opacity-50 cursor-not-allowed text-gray-500"
                                }`}
                                icon={Camera}
                                title={ocrAvailable ? "Ler Cupom (OCR)" : "OCR Indisponível (Requer modelo Vision)"}
                            />
                             <Button 
                                onClick={() => setIsImportOpen(true)}
                                variant="outline" 
                                size="icon"
                                className="rounded-xl shadow-lg hover:bg-gray-700 transition-colors"
                                icon={UploadCloud}
                                title="Importar Extrato (OFX)"
                            />
                            <Button 
                                id="tx-add-btn"
                                onClick={() => { setEditingTx(null); setOcrData(null); setIsModalOpen(true); }}
                                variant="primary"
                                size="icon"
                                className="rounded-xl shadow-lg hover:bg-emerald-600 transition-colors"
                                icon={Plus}
                            />
                        </div>
                    }
                />
            </div>
                {/* Filters Row */}
                <div id="tx-filters" className="flex flex-col md:flex-row gap-3">
                    <div className="flex flex-wrap gap-2 w-full md:w-auto">
                        {/* Month Select */}
                        <div className="relative flex-1 min-w-[140px] md:flex-none">
                            <Select 
                                icon={Filter}
                                value={filterValue}
                                onChange={handleFilterChange}
                                variant="glass"
                                options={[
                                    { label: "Todo o Período", value: "all" },
                                    ...months.map(m => ({ label: m.label, value: m.value }))
                                ]}
                                className="bg-gray-900 border-gray-800 focus-visible:border-emerald-500" 
                            />
                        </div>

                        {/* Category Select */}
                        <div className="relative flex-1 min-w-[140px] md:flex-none">
                            <Select 
                                value={categoryFilter}
                                onChange={(e) => setCategoryFilter(e.target.value)}
                                variant="glass"
                                options={[
                                    { label: "Todas as Categorias", value: "all" },
                                    ...uniqueCategories.map(cat => ({ label: cat, value: cat }))
                                ]}
                                className="bg-gray-900 border-gray-800 focus-visible:border-emerald-500"
                            />
                        </div>
                    </div>

                    {/* Search Input */}
                    <div className="relative w-full md:flex-1">
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
            <div id="tx-list" className="flex-1 overflow-y-auto scrollbar-none pb-20">
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
                                    key={t.id} 
                                    transaction={t} 
                                    categoryColor={getCategoryColor(t.category)}
                                    onDelete={(id) => {
                                        if (window.confirm("Tem certeza que deseja excluir esta transação?")) {
                                            deleteTransaction(id);
                                        }
                                    }} 
                                    onEdit={handleEdit}
                                    onCategoryClick={handleCategoryClick}
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
                key={`modal-${editingTx?.id || 'new'}-${ocrData?.descricao || ''}`}
                isOpen={isModalOpen}
                onClose={() => { setIsModalOpen(false); setOcrData(null); }}
                onSave={handleSave}
                initialData={initialFormData}
                isLoading={isCreating || isUpdating}
            />

            <ImportDrawer 
                isOpen={isImportOpen} 
                onClose={() => setIsImportOpen(false)} 
            />
            
            <OCRModal 
                isOpen={isOCROpen}
                onClose={() => setIsOCROpen(false)}
                onSuccess={handleOCRSuccess}
            />
        </div>
    );
}
