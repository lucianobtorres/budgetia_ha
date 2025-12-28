import { useState, useEffect } from 'react';
import { Drawer } from '../ui/Drawer';
import { TRANSACTION_CATEGORIES } from '../../utils/constants';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

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
        <Drawer 
            isOpen={isOpen} 
            onClose={onClose} 
            title={initialData ? 'Editar Transação' : 'Nova Transação'}
            action={
                <Button 
                    type="submit" 
                    form="transaction-form"
                    disabled={isLoading}
                    variant="primary"
                    className="font-semibold px-6"
                >
                    {isLoading ? '...' : 'Salvar'}
                </Button>
            }
        >
            <form id="transaction-form" onSubmit={handleSubmit} className="space-y-5 pb-safe pt-2 relative">
                {isLoading && (
                    <div className="absolute inset-0 z-50 bg-gray-950/60 backdrop-blur-[2px] flex items-center justify-center rounded-xl transition-all duration-300">
                        <div className="flex flex-col items-center gap-3">
                             <div className="w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
                             <span className="text-xs font-medium text-emerald-400 animate-pulse">Salvando...</span>
                        </div>
                    </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1.5">Tipo</label>
                        <select 
                            value={formData.tipo}
                            onChange={(e) => setFormData({...formData, tipo: e.target.value as 'Receita' | 'Despesa'})}
                            className="w-full bg-gray-950 border border-gray-700 text-white rounded-xl px-4 py-3 focus:outline-none focus:border-emerald-500 transition-colors appearance-none"
                        >
                            <option value="Despesa">Despesa</option>
                            <option value="Receita">Receita</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1.5">Data</label>
                        <Input 
                            type="date" 
                            value={formData.data}
                            onChange={(e) => setFormData({...formData, data: e.target.value})}
                            required
                            className="min-h-[48px]"
                        />
                    </div>
                </div>

                <div>
                     <label className="block text-sm font-medium text-gray-400 mb-1.5">Descrição</label>
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
                        <label className="block text-sm font-medium text-gray-400 mb-1.5">Valor (R$)</label>
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
                </div>

                 <div>
                    <label className="block text-sm font-medium text-gray-400 mb-1.5">Status</label>
                    <select 
                        value={formData.status}
                        onChange={(e) => setFormData({...formData, status: e.target.value})}
                        className="w-full bg-gray-950 border border-gray-700 text-white rounded-xl px-4 py-3 focus:outline-none focus:border-emerald-500 transition-colors appearance-none"
                    >
                        <option value="Concluído">Concluído</option>
                        <option value="Pendente">Pendente</option>
                    </select>
                </div>
            </form>
        </Drawer>
    );
}
