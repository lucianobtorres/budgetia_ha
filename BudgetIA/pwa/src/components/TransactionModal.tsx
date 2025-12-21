import { useState, useEffect } from 'react';
import { X } from 'lucide-react';

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

const CATEGORIES = [
    'Alimentação', 'Moradia', 'Transporte', 'Lazer', 'Saúde', 
    'Educação', 'Salário', 'Investimentos', 'Outros'
];

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
                        {initialData ? 'Editar Transação' : 'Nova Transação'}
                    </h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
                        <X size={20} />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-4 space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-400 mb-1">Tipo</label>
                            <select 
                                value={formData.tipo}
                                onChange={(e) => setFormData({...formData, tipo: e.target.value as 'Receita' | 'Despesa'})}
                                className="w-full bg-gray-950 border border-gray-700 text-white rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"
                            >
                                <option value="Despesa">Despesa</option>
                                <option value="Receita">Receita</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-400 mb-1">Data</label>
                            <input 
                                type="date" 
                                value={formData.data}
                                onChange={(e) => setFormData({...formData, data: e.target.value})}
                                required
                                className="w-full bg-gray-950 border border-gray-700 text-white rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"
                            />
                        </div>
                    </div>

                    <div>
                         <label className="block text-sm font-medium text-gray-400 mb-1">Descrição</label>
                        <input 
                            type="text" 
                            value={formData.descricao}
                            onChange={(e) => setFormData({...formData, descricao: e.target.value})}
                            required
                            placeholder="Ex: Supermercado"
                            className="w-full bg-gray-950 border border-gray-700 text-white rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                         <div>
                            <label className="block text-sm font-medium text-gray-400 mb-1">Valor</label>
                            <input 
                                type="number" 
                                step="0.01"
                                value={formData.valor}
                                onChange={(e) => setFormData({...formData, valor: parseFloat(e.target.value)})}
                                required
                                className="w-full bg-gray-950 border border-gray-700 text-white rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"
                            />
                        </div>
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
                    </div>

                     <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1">Status</label>
                        <select 
                            value={formData.status}
                            onChange={(e) => setFormData({...formData, status: e.target.value})}
                            className="w-full bg-gray-950 border border-gray-700 text-white rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"
                        >
                            <option value="Concluído">Concluído</option>
                            <option value="Pendente">Pendente</option>
                        </select>
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
