import { useState, useEffect } from 'react';
import { FormDrawer } from '../ui/FormDrawer';
import { useCategories } from '../../hooks/useCategories';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import { DatePicker } from '../ui/DatePicker';

interface TransactionInput {
    data: string;
    descricao: string;
    valor: number;
    tipo: 'Receita' | 'Despesa';
    categoria: string;
    status: string;
}

interface TransactionModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (transaction: TransactionInput) => Promise<void>;
    initialData?: TransactionInput;
    isLoading?: boolean;
}

export default function TransactionModal({ isOpen, onClose, onSave, initialData, isLoading }: TransactionModalProps) {
    const { categories } = useCategories();
    
    // Sort categories alphabetically
    const sortedCategories = [...categories].sort((a, b) => a.name.localeCompare(b.name));

    const [formData, setFormData] = useState<TransactionInput>({
        data: new Date().toISOString().split('T')[0],
        descricao: '',
        valor: 0,
        tipo: 'Despesa',
        categoria: 'Outros',
        status: 'Concluído'
    });

    useEffect(() => {
        if (initialData) {
            setFormData(initialData);
        } else {
            setFormData({
                data: new Date().toISOString().split('T')[0],
                descricao: '',
                valor: 0,
                tipo: 'Despesa',
                categoria: 'Outros',
                status: 'Concluído'
            });
        }
    }, [initialData, isOpen]);

    const [isInstallment, setIsInstallment] = useState(false);
    const [installmentsCount, setInstallmentsCount] = useState(2);

    useEffect(() => {
        if (!isOpen) {
            // Reset state on close
            setIsInstallment(false);
            setInstallmentsCount(2);
        }
    }, [isOpen]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const payload = { ...formData };
        if (isInstallment && installmentsCount > 1) {
             (payload as any).parcelas = installmentsCount;
        }
        await onSave(payload);
    };

    const estimatedTotal = isInstallment ? formData.valor * installmentsCount : formData.valor;

    return (
        <FormDrawer 
            isOpen={isOpen} 
            onClose={onClose} 
            title={initialData ? 'Editar Transação' : 'Nova Transação'}
            isLoading={isLoading}
            onSubmit={handleSubmit}
            formId="transaction-form"
        >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1.5">Tipo</label>
                    <Select 
                        value={formData.tipo}
                        onChange={(e) => setFormData({...formData, tipo: e.target.value as 'Receita' | 'Despesa'})}
                        options={[
                            { label: "Despesa", value: "Despesa" },
                            { label: "Receita", value: "Receita" }
                        ]}
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1.5">Data</label>
                    <DatePicker 
                        value={formData.data}
                        onChange={(e) => setFormData({...formData, data: e.target.value})}
                        required
                    />
                </div>
            </div>

            <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1.5">Descrição</label>
                <Input 
                    type="text" 
                    value={formData.descricao}
                    onChange={(e) => setFormData({...formData, descricao: e.target.value})}
                    required
                    placeholder="Ex: Supermercado"
                />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1.5">Valor (Parcela)</label>
                    <Input 
                        type="number" 
                        step="0.01"
                        value={formData.valor}
                        onChange={(e) => setFormData({...formData, valor: parseFloat(e.target.value)})}
                        required
                        placeholder="0,00"
                    />
                </div>
                    <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1.5">Categoria</label>
                    <Select 
                        value={formData.categoria}
                        onChange={(e) => setFormData({...formData, categoria: e.target.value})}
                        options={[
                            ...sortedCategories.map(cat => ({ label: cat.name, value: cat.name }))
                        ]}
                    />
                </div>
            </div>

            {/* Installments Section */}
            {!initialData && formData.tipo === 'Despesa' && (
                <div className="bg-gray-800/30 p-3 rounded-lg border border-gray-700/50 space-y-3">
                    <div className="flex items-center gap-3">
                         <input 
                            type="checkbox" 
                            id="is_installment"
                            checked={isInstallment}
                            onChange={(e) => setIsInstallment(e.target.checked)}
                            className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-emerald-500 focus:ring-emerald-500/20"
                         />
                         <label htmlFor="is_installment" className="text-sm font-medium text-gray-200 select-none cursor-pointer">
                             Compra Parcelada?
                         </label>
                    </div>

                    {isInstallment && (
                        <div className="animate-in fade-in slide-in-from-top-1 duration-200">
                             <label className="block text-sm font-medium text-text-secondary mb-1.5">Número de Parcelas</label>
                             <Input 
                                type="number" 
                                min={2}
                                max={99}
                                value={installmentsCount}
                                onChange={(e) => setInstallmentsCount(parseInt(e.target.value))}
                             />
                             {formData.valor > 0 && (
                                 <p className="text-xs text-text-secondary mt-2">
                                     Total Estimado: <span className="font-bold text-emerald-400">R$ {(formData.valor * installmentsCount).toFixed(2).replace('.', ',')}</span>
                                 </p>
                             )}
                        </div>
                    )}
                </div>
            )}

                <div>
                <label className="block text-sm font-medium text-text-secondary mb-1.5">Status</label>
                <Select 
                    value={formData.status}
                    onChange={(e) => setFormData({...formData, status: e.target.value})}
                    options={[
                        { label: "Concluído", value: "Concluído" },
                        { label: "Pendente", value: "Pendente" }
                    ]}
                />
            </div>
        </FormDrawer>
    );
}
