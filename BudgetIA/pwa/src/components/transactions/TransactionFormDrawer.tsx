import { useState, useEffect } from 'react';
import { FormDrawer } from '../ui/FormDrawer';
import { TRANSACTION_CATEGORIES } from '../../utils/constants';
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

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        await onSave(formData);
    };

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
                    <label className="block text-sm font-medium text-text-secondary mb-1.5">Valor (R$)</label>
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
                            { label: "Selecione", value: "" }, // disabled handling not natively in options prop yet, but works as placeholder
                            ...TRANSACTION_CATEGORIES.map(cat => ({ label: cat, value: cat }))
                        ]}
                    />
                </div>
            </div>

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
