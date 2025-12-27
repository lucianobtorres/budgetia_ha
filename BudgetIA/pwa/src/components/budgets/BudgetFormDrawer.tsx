import { useState, useEffect } from 'react';
import { Drawer } from '../ui/Drawer';
import { TRANSACTION_CATEGORIES } from '../../utils/constants';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

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
        <Drawer 
            isOpen={isOpen} 
            onClose={onClose} 
            title={initialData ? 'Editar Orçamento' : 'Novo Orçamento'}
            action={
                <Button 
                    type="submit" 
                    form="budget-form"
                    disabled={isLoading}
                    variant="primary"
                    className="font-semibold px-6"
                >
                    {isLoading ? '...' : 'Salvar'}
                </Button>
            }
        >
            <form id="budget-form" onSubmit={handleSubmit} className="space-y-5 pb-safe pt-2 relative">
                {isLoading && (
                    <div className="absolute inset-0 z-50 bg-gray-950/60 backdrop-blur-[2px] flex items-center justify-center rounded-xl transition-all duration-300">
                        <div className="flex flex-col items-center gap-3">
                             <div className="w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
                             <span className="text-xs font-medium text-emerald-400 animate-pulse">Salvando...</span>
                        </div>
                    </div>
                )}
                
                <div>
                    <label className="block text-sm font-medium text-gray-400 mb-1.5">Categoria</label>
                    <select 
                        value={formData.categoria}
                        onChange={(e) => setFormData({...formData, categoria: e.target.value})}
                        className="w-full bg-gray-950 border border-gray-700 text-white rounded-xl px-4 py-3 focus:outline-none focus:border-emerald-500 transition-colors appearance-none"
                    >
                        <option value="" disabled>Selecione</option>
                        {TRANSACTION_CATEGORIES.map(cat => (
                            <option key={cat} value={cat}>{cat}</option>
                        ))}
                    </select>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1.5">Limite (R$)</label>
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
                            <label className="block text-sm font-medium text-gray-400 mb-1.5">Período</label>
                        <select 
                            value={formData.periodo}
                            onChange={(e) => setFormData({...formData, periodo: e.target.value})}
                            className="w-full bg-gray-950 border border-gray-700 text-white rounded-xl px-4 py-3 focus:outline-none focus:border-emerald-500 transition-colors appearance-none"
                        >
                            <option value="Mensal">Mensal</option>
                            <option value="Anual">Anual</option>
                            <option value="Semanal">Semanal</option>
                        </select>
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-400 mb-1.5">Observações (Opcional)</label>
                    <textarea 
                        value={formData.observacoes}
                        onChange={(e) => setFormData({...formData, observacoes: e.target.value})}
                        rows={3}
                        placeholder="Ex: Meta para economizar..."
                        className="w-full bg-gray-950 border border-gray-700 text-white rounded-xl px-4 py-3 focus:outline-none focus:border-emerald-500 transition-colors"
                    />
                </div>
            </form>
        </Drawer>
    );
}
