import { WifiOff } from 'lucide-react';
import { useOnlineStatus } from '../../hooks/useOnlineStatus';
import { cn } from '../../utils/cn';

export function OfflineIndicator() {
    const isOnline = useOnlineStatus();

    if (isOnline) return null;

    return (
        <div 
            className={cn(
                "w-full bg-gradient-to-r from-surface/60 via-danger/20 to-surface/60 backdrop-blur-md border-b border-danger text-danger text-xs font-medium flex items-center justify-center gap-2",
                "animate-in slide-in-from-top-full duration-500 shadow-lg shadow-danger/10",
                "pt-safe pb-2 px-4" // Using tailwind-safe-area plugin classes if available, otherwise fallback style
            )}
            style={{ paddingTop: 'max(4px, env(safe-area-inset-top))', paddingBottom: 'max(4px, env(safe-area-inset-bottom, 4px))' }}
        >
            <WifiOff size={14} className="text-danger" />
            <span>Modo Offline - Verificando conexão...</span>
        </div>
    );
}
