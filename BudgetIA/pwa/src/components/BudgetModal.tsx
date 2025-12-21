import { useState, useEffect } from 'react';
import { X } from 'lucide-react';

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

const CATEGORIES = [
    'Alimentação', 'Moradia', 'Transporte', 'Lazer', 'Saúde', 
    'Educação', 'Salário', 'Investimentos', 'Outros'
];

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

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        await onSave(formData);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="w-full max-w-md bg-gray-900 border border-gray-800 rounded-xl shadow-2xl overflow-hidden">
                <div className="flex items-center justify-between p-4 border-b border-gray-800 bg-gray-900/50">
                    <h3 className="text-lg font-semibold text-white">
                        {initialData ? 'Editar Orçamento' : 'Novo Orçamento'}
                    </h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
                        <X size={20} />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-4 space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1">Categoria</label>
                        <select 
                            value={formData.categoria}
                            onChange={(e) => setFormData({...formData, categoria: e.target.value})}
                            className="w-full bg-gray-950 border border-gray-700 text-white rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"
                        >
                            <option value="" disabled>Selecione</option>
                            {CATEGORIES.map(cat => (
                                <option key={cat} value={cat}>{cat}</option>
                            ))}
                        </select>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                         <div>
                            <label className="block text-sm font-medium text-gray-400 mb-1">Limite (R$)</label>
                            <input 
                                type="number" 
                                step="0.01"
                                value={formData.valor_limite}
                                onChange={(e) => setFormData({...formData, valor_limite: parseFloat(e.target.value)})}
                                required
                                className="w-full bg-gray-950 border border-gray-700 text-white rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"
                            />
                        </div>
                        <div>
                             <label className="block text-sm font-medium text-gray-400 mb-1">Período</label>
                            <select 
                                value={formData.periodo}
                                onChange={(e) => setFormData({...formData, periodo: e.target.value})}
                                className="w-full bg-gray-950 border border-gray-700 text-white rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"
                            >
                                <option value="Mensal">Mensal</option>
                                <option value="Anual">Anual</option>
                                <option value="Semanal">Semanal</option>
                            </select>
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1">Observações</label>
                        <textarea 
                            value={formData.observacoes}
                            onChange={(e) => setFormData({...formData, observacoes: e.target.value})}
                            rows={3}
                            className="w-full bg-gray-950 border border-gray-700 text-white rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"
                        />
                    </div>

                    <div className="pt-2 flex justify-end space-x-3">
                        <button 
                            type="button" 
                            onClick={onClose}
                            className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                        >
                            Cancelar
                        </button>
                        <button 
                            type="submit" 
                            disabled={isLoading}
                            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                        >
                            {isLoading ? 'Salvando...' : 'Salvar'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
