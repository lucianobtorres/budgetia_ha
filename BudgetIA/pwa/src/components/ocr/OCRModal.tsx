import { useState, useRef } from 'react';
import { Dialog } from '../ui/Dialog';
import { Button } from '../ui/Button';
import { Camera, Upload, X, Loader2, Check } from 'lucide-react';
import { fetchAPI } from '../../services/api';
import { toast } from 'sonner';

interface OCRModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: (data: any) => void;
}

export function OCRModal({ isOpen, onClose, onSuccess }: OCRModalProps) {
    const [imagePreview, setImagePreview] = useState<string | null>(null);
    const [file, setFile] = useState<File | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0];
        if (selectedFile) {
            setFile(selectedFile);
            setImagePreview(URL.createObjectURL(selectedFile));
        }
    };

    const handleAnalyze = async () => {
        if (!file) return;

        setIsLoading(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            // Using fetchAPI which handles Auth and FormData content-type automatically
            const data = await fetchAPI('/ocr/analyze', {
                method: 'POST',
                body: formData
            });
            
            toast.success("Leitura concluída!");
            
            // Map OCR format to TransactionForm format
            const formattedData = {
                data: data.data || new Date().toISOString().split('T')[0],
                descricao: data.estabelecimento || "Compra OCR",
                valor: data.total || 0,
                tipo: 'Despesa',
                categoria: data.categoria_sugerida || 'Outros',
                status: 'Concluído'
            };
            
            onSuccess(formattedData);
            handleClose();

        } catch (error) {
            console.error(error);
            toast.error("Erro ao ler cupom. Tente novamente.");
        } finally {
            setIsLoading(false);
        }
    };

    const handleClose = () => {
        setFile(null);
        setImagePreview(null);
        onClose();
    };

    return (
        <Dialog 
            isOpen={isOpen} 
            onClose={handleClose}
            title="Digitalizar Cupom"
            className="max-w-md"
        >
            <div className="space-y-4">
                {/* Upload Area */}
                <div 
                    onClick={() => fileInputRef.current?.click()}
                    className={`
                        border-2 border-dashed rounded-xl p-8 
                        flex flex-col items-center justify-center gap-3
                        cursor-pointer transition-colors
                        ${imagePreview ? 'border-emerald-500/50 bg-emerald-500/5' : 'border-gray-700 hover:border-gray-600 hover:bg-gray-800/50'}
                    `}
                >
                    {imagePreview ? (
                        <div className="relative w-full aspect-[3/4] max-h-[300px]">
                            <img 
                                src={imagePreview} 
                                alt="Preview" 
                                className="w-full h-full object-contain rounded-lg" 
                            />
                            <button 
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setFile(null);
                                    setImagePreview(null);
                                }}
                                className="absolute top-2 right-2 p-1 bg-black/50 text-white rounded-full hover:bg-red-500 transition-colors"
                            >
                                <X size={16} />
                            </button>
                        </div>
                    ) : (
                        <>
                            <div className="p-4 bg-gray-800 rounded-full">
                                <Camera className="w-8 h-8 text-emerald-400" />
                            </div>
                            <div className="text-center">
                                <p className="font-medium text-gray-200">Tirar foto ou escolher</p>
                                <p className="text-sm text-gray-400">Suporta JPG, PNG</p>
                            </div>
                        </>
                    )}
                    
                    <input 
                        ref={fileInputRef}
                        type="file" 
                        accept="image/*" 
                        capture="environment"
                        className="hidden"
                        onChange={handleFileChange}
                    />
                </div>

                {/* Actions */}
                <div className="flex gap-3">
                    <Button 
                        variant="secondary" 
                        onClick={handleClose} 
                        className="flex-1"
                        disabled={isLoading}
                    >
                        Cancelar
                    </Button>
                    <Button 
                        variant="primary" 
                        onClick={handleAnalyze} 
                        className="flex-1"
                        disabled={!file || isLoading}
                        icon={isLoading ? Loader2 : Check}
                    >
                        {isLoading ? 'Lendo...' : 'Analisar'}
                    </Button>
                </div>
            </div>
        </Dialog>
    );
}
