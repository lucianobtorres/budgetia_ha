import { useState, useMemo } from 'react';
import { Drawer } from '../ui/Drawer';
import { Button } from '../ui/Button';
import { Upload, X, Check, Loader2, AlertCircle } from 'lucide-react';
import { uploadOFX, type ImportedTransaction } from '../../services/importService';
import { useCreateTransactionsBatch } from '../../hooks/useTransactions';
import { Select } from '../../components/ui/Select';
import { useCategories } from '../../services/categoryService';
import { toast } from 'sonner';
import { LoadingOverlay } from '../ui/LoadingOverlay';

interface ImportDrawerProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess?: () => void;
}

export function ImportDrawer({ isOpen, onClose, onSuccess }: ImportDrawerProps) {
    const [step, setStep] = useState<'upload' | 'review'>('upload');
    const [transactions, setTransactions] = useState<ImportedTransaction[]>([]);
    const [loading, setLoading] = useState(false);
    
    // Use the hook for batch creation (Handles invalidation & toast)
    const { mutateAsync: saveBatch } = useCreateTransactionsBatch();
    const [isSaving, setIsSaving] = useState(false);
    const [uploadFeedback, setUploadFeedback] = useState<string | null>(null);
    
    // Fetch categories dynamically
    const { data: categoriesData } = useCategories();


    const categoryOptions = useMemo(() => {
        const dbOptions = categoriesData?.map(c => ({ label: c.name, value: c.name })) || [];
        
        // Also look at transactions for any NEW category suggested by AI that isn't in DB yet
        const importedOptions = transactions
            .map(t => t.categoria)
            .filter(cat => cat && cat !== "A Classificar" && cat !== "Outros") // Ignore basics
            .map(cat => ({ label: cat, value: cat }));

        // Merge and unique
        const allOptions = [...dbOptions, ...importedOptions];
        const uniqueOptions = Array.from(new Map(allOptions.map(item => [item.value, item])).values());
        
        // Ensure "A Classificar" is first
        return [
            { label: "A Classificar", value: "A Classificar" },
            ...uniqueOptions
        ];
    }, [categoriesData, transactions]);

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setLoading(true);
        setUploadFeedback(null); // Clear previous
        try {
            const data = await uploadOFX(file);
            
            if (data.length === 0) {
                setUploadFeedback("Nenhuma transação nova encontrada (todas as transações deste arquivo já existem ou são duplicatas).");
                setTransactions([]);
                e.target.value = ''; // Reset input to allow same file selection again if needed
                return; 
            }

            setTransactions(data.map(item => ({...item, status: 'Pendente'}))); 
            setStep('review');
            
            // Check if any were classified
            const classified = data.filter(i => i.categoria !== 'A Classificar').length;
            if (classified > 0) {
                toast.success(`${classified} transações pré-classificadas pela IA!`);
            }
        } catch (error) {
            console.error(error);
            toast.error("Falha ao ler arquivo OFX.");
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        setIsSaving(true);
        try {
             // Filter output
             const batch = transactions.filter(t => t.status !== 'Concluído').map(t => ({
                data: t.data,
                tipo: t.tipo,
                categoria: t.categoria,
                descricao: t.descricao,
                valor: t.valor,
                status: 'Concluído'
            }));
            
            // Artificial delay for UX + Actual Save
            await Promise.all([
                saveBatch(batch),
                new Promise(resolve => setTimeout(resolve, 800))
            ]);
            
            // Hook handles toast and invalidation.
            if (onSuccess) onSuccess();
            onClose();
            reset();
        } catch (error) {
            console.error(error);
            // Hook handles error toast too
        } finally {
            setIsSaving(false);
        }
    };

    const reset = () => {
        setStep('upload');
        setTransactions([]);
        setLoading(false);
        setUploadFeedback(null);
    };

    const updateCategory = (index: number, category: string) => {
        const updated = [...transactions];
        updated[index].categoria = category;
        setTransactions(updated);
    };

    const removeItem = (index: number) => {
        const updated = [...transactions];
        updated.splice(index, 1);
        setTransactions(updated);
        
        if (updated.length === 0) {
            setStep('upload');
        }
    };

    return (
        <>
        <LoadingOverlay isVisible={isSaving} message="Salvando transações..." />
        <Drawer 
            isOpen={isOpen} 
            onClose={onClose} 
            title={step === 'upload' ? 'Importar Extrato' : 'Revisar Transações'}
            action={step === 'review' && (
                <Button 
                    size="sm" 
                    variant="primary" 
                    onClick={handleSave}
                    disabled={isSaving}
                    icon={isSaving ? Loader2 : Check}
                    className="h-8"
                >
                    {isSaving ? 'Confirmando...' : 'Confirmar'}
                </Button>
            )}
        >
            <div className="flex flex-col h-full gap-4">
                {step === 'upload' ? (
                    <div className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-gray-700/50 rounded-xl bg-gray-900/20 p-8 text-center space-y-4">
                         
                         {uploadFeedback && (
                             <div className="mb-4 bg-blue-500/10 border border-blue-500/20 text-blue-200 px-4 py-3 rounded-lg text-sm max-w-sm mx-auto">
                                 <AlertCircle className="w-5 h-5 mx-auto mb-2 text-blue-400" />
                                 {uploadFeedback}
                             </div>
                         )}

                         <div className="p-4 bg-gray-800 rounded-full inline-block">
                             {loading ? <Loader2 className="w-8 h-8 animate-spin text-emerald-500" /> : <Upload className="w-8 h-8 text-gray-400" />}
                         </div>
                         
                         <div className="space-y-2">
                             <h3 className="font-medium text-lg text-gray-200">
                                 {loading ? 'Processando Arquivo com IA...' : 'Arraste ou Selecione seu arquivo OFX'}
                             </h3>
                             <p className="text-sm text-gray-500 max-w-xs mx-auto">
                                Suportamos arquivos .ofx gerados pela maioria dos bancos brasileiros. A IA tentará categorizar automaticamente.
                             </p>
                         </div>

                         {!loading && (
                             <div className="relative">
                                 <input 
                                    type="file" 
                                    accept=".ofx,.OFX"
                                    onChange={handleFileUpload}
                                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                 />
                                 <Button variant="outline">
                                     Selecionar Arquivo
                                 </Button>
                             </div>
                         )}
                    </div>
                ) : (
                    <div className="flex-1 overflow-hidden flex flex-col">
                        <div className="flex items-center gap-2 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg text-sm text-blue-200 mb-4">
                            <AlertCircle className="w-4 h-4 shrink-0" />
                            <p>Revise as categorias abaixo antes de confirmar.</p>
                        </div>
                        
                        <div className="flex-1 overflow-y-auto space-y-3 pb-20">
                            {transactions.map((tx, i) => (
                                <div key={i} className="p-3 bg-gray-800/30 border border-gray-700/30 rounded-lg flex flex-col gap-3">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <span className="text-xs text-gray-500 block">{tx.data}</span>
                                            <p className="text-sm font-medium text-gray-200 line-clamp-2">{tx.descricao}</p>
                                        </div>
                                        <div className="flex items-center gap-3">
                                             <span className={`text-sm font-bold ${tx.tipo === 'Receita' ? 'text-emerald-400' : 'text-red-400'}`}>
                                                 {tx.tipo === 'Receita' ? '+' : '-'} R$ {tx.valor.toFixed(2)}
                                             </span>
                                             <button onClick={() => removeItem(i)} className="text-gray-500 hover:text-red-400 px-1">
                                                 <X size={16} />
                                             </button>
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <Select 
                                            value={tx.categoria}
                                            onChange={(e) => updateCategory(i, e.target.value)}
                                            options={categoryOptions}
                                            className="h-9 text-xs"
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </Drawer>
        </>
    );
}
