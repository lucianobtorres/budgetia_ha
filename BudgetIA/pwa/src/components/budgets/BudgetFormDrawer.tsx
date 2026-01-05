import { useState, useEffect } from 'react';
import { FormDrawer } from '../ui/FormDrawer';
import { TRANSACTION_CATEGORIES } from '../../utils/constants';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import { Textarea } from '../ui/Textarea';

interface BudgetInput {
    categoria: string;
    valor_limite: number;
    periodo: string;
    observacoes: string;
}

interface BudgetModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (budget: BudgetInput) => Promise<void>;
    initialData?: BudgetInput;
    isLoading?: boolean;
}



export default function BudgetModal({ isOpen, onClose, onSave, initialData, isLoading }: BudgetModalProps) {
    const [formData, setFormData] = useState<BudgetInput>({
        categoria: 'Outros',
        valor_limite: 0,
        periodo: 'Mensal',
        observacoes: ''
    });

    useEffect(() => {
        if (initialData) {
            setFormData(initialData);
        } else {
             setFormData({
                categoria: 'Outros',
                valor_limite: 0,
                periodo: 'Mensal',
                observacoes: ''
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
            title={initialData ? 'Editar Orçamento' : 'Novo Orçamento'}
            isLoading={isLoading}
            onSubmit={handleSubmit}
            formId="budget-form"
        >
            <div>
                <label className="block text-sm font-medium text-text-secondary mb-1.5">Categoria</label>
                <Select 
                    value={formData.categoria}
                    onChange={(e) => setFormData({...formData, categoria: e.target.value})}
                    options={[
                        { label: "Selecione", value: "" }, 
                        ...TRANSACTION_CATEGORIES.map(cat => ({ label: cat, value: cat }))
                    ]}
                />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1.5">Limite (R$)</label>
                    <Input 
                        type="number" 
                        step="0.01"
                        value={formData.valor_limite}
                        onChange={(e) => setFormData({...formData, valor_limite: parseFloat(e.target.value)})}
                        required
                        placeholder="0,00"
                    />
                </div>
                <div>
                        <label className="block text-sm font-medium text-text-secondary mb-1.5">Período</label>
                    <Select 
                        value={formData.periodo}
                        onChange={(e) => setFormData({...formData, periodo: e.target.value})}
                        options={[
                            { label: "Mensal", value: "Mensal" },
                            { label: "Anual", value: "Anual" },
                            { label: "Semanal", value: "Semanal" }
                        ]}
                    />
                </div>
            </div>

            <div>
                <label className="block text-sm font-medium text-text-secondary mb-1.5">Observações (Opcional)</label>
                <Textarea 
                    value={formData.observacoes}
                    onChange={(e) => setFormData({...formData, observacoes: e.target.value})}
                    rows={3}
                    placeholder="Ex: Meta para economizar..."
                />
            </div>
        </FormDrawer>
    );
}
