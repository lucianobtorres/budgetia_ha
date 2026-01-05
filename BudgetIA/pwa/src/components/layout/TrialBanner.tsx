import { useEffect, useState } from 'react';
import { AuthService } from '../../services/auth';
import { Clock, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export function TrialBanner() {
    const [daysRemaining, setDaysRemaining] = useState<number | null>(null);
    const [isVisible, setIsVisible] = useState(true);

    useEffect(() => {
        const checkTrial = () => {
            const mode = AuthService.getDeployMode();
            if (mode !== 'SAAS') return; // Don't show in Self Hosted

            const endDateStr = AuthService.getTrialEndDate();
            if (!endDateStr) return;

            const end = new Date(endDateStr);
            const now = new Date();
            const diffTime = end.getTime() - now.getTime();
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            
            setDaysRemaining(diffDays);
        };

        checkTrial();
        const interval = setInterval(checkTrial, 60000);
        return () => clearInterval(interval);
    }, []);

    if (daysRemaining === null || !isVisible) return null; 

    // Cores baseadas no tempo
    const getStyles = () => {
        if (daysRemaining <= 0) {
            return "bg-red-500 text-white";
        }
        if (daysRemaining <= 3) {
            return "bg-gradient-to-r from-red-500 to-pink-600 text-white";
        }
        return "bg-gradient-to-r from-pink-500 to-purple-600 text-white";
    };

    const getMessage = () => {
        if (daysRemaining <= 0) return "Seu período de teste expirou. Entre em contato para ativar.";
        if (daysRemaining === 1) return "Último dia do seu período de teste!";
        return `Você tem ${daysRemaining} dias restantes no seu período de teste.`;
    };

    return (
        <AnimatePresence>
            <motion.div 
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className={`${getStyles()} relative z-50`}
            >
            <div className="max-w-7xl mx-auto px-4 py-2 relative flex items-center justify-center text-xs md:text-sm font-medium">
                <div className="flex items-center gap-2">
                    <Clock className="w-3 h-3 md:w-4 md:h-4" />
                    <span>{getMessage()}</span>
                    {daysRemaining <= 0 && (
                        <a href="https://wa.me/55..." target="_blank" className="underline ml-2 hover:text-white/80">
                            Falar com Suporte
                        </a>
                    )}
                </div>
                
                <button 
                    onClick={() => setIsVisible(false)}
                    className="absolute right-4 p-1 hover:bg-white/20 rounded-full transition-colors"
                    title="Fechar aviso nesta sessão"
                >
                    <X className="w-3 h-3 md:w-4 md:h-4" />
                </button>
            </div>
            </motion.div>
        </AnimatePresence>
    );
}
