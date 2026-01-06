import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '../../utils/cn';

interface LoadingOverlayProps {
    isVisible: boolean;
    message?: string;
    className?: string;
}

export function LoadingOverlay({ 
    isVisible, 
    message = "Carregando...",
    className 
}: LoadingOverlayProps) {
    if (!isVisible) return null;

    return (
        <div className={cn(
            "fixed inset-0 z-[200] flex flex-col items-center justify-center bg-black/60 backdrop-blur-sm transition-all duration-300",
            className
        )}>
            <div className="flex flex-col items-center p-6 bg-gray-900/80 border border-gray-700 rounded-2xl shadow-2xl animate-in fade-in zoom-in duration-300">
                <Loader2 className="w-10 h-10 text-primary animate-spin mb-4" />
                <span className="text-white font-medium text-lg tracking-wide">{message}</span>
            </div>
        </div>
    );
}
