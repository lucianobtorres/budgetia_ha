import { WifiOff } from 'lucide-react';
import { useOnlineStatus } from '../../hooks/useOnlineStatus';
import { cn } from '../../utils/cn';

export function OfflineIndicator() {
    const isOnline = useOnlineStatus();

    if (isOnline) return null;

    return (
        <div 
            className={cn(
                "w-full bg-gradient-to-r from-black/60 via-red-900/60 to-black/60 backdrop-blur-md border-b border-red-500 text-red-100 text-xs font-medium flex items-center justify-center gap-2",
                "animate-in slide-in-from-top-full duration-500 shadow-lg shadow-red-900/20",
                "pt-safe pb-2 px-4" // Using tailwind-safe-area plugin classes if available, otherwise fallback style
            )}
            style={{ paddingTop: 'max(4px, env(safe-area-inset-top))', paddingBottom: 'max(4px, env(safe-area-inset-bottom, 4px))' }}
        >
            <WifiOff size={14} className="text-red-400" />
            <span>Modo Offline - Verificando conexão...</span>
        </div>
    );
}
