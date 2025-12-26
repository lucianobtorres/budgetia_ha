import { WifiOff, RefreshCcw } from 'lucide-react';
import { Button } from '../components/ui/Button';

interface ConnectionErrorPageProps {
    onRetry: () => void;
}

export default function ConnectionErrorPage({ onRetry }: ConnectionErrorPageProps) {
    return (
        <div className="min-h-screen bg-gray-950 flex items-center justify-center p-6">
            <div className="max-w-md w-full text-center space-y-6">
                <div className="w-20 h-20 bg-red-900/20 rounded-full flex items-center justify-center mx-auto ring-1 ring-red-500/20">
                    <WifiOff className="text-red-500 w-10 h-10" />
                </div>
                
                <div className="space-y-2">
                    <h1 className="text-2xl font-bold text-white">Sem Conexão com o Servidor</h1>
                    <p className="text-gray-400">
                        Não foi possível conectar ao backend do BudgetIA. Verifique se o servidor está rodando ou se sua internet está estável.
                    </p>
                </div>

                <div className="pt-4">
                    <Button 
                        onClick={onRetry} 
                        className="w-full justify-center py-6 text-lg"
                        icon={RefreshCcw}
                    >
                        Tentar Novamente
                    </Button>
                </div>
            </div>
        </div>
    );
}
