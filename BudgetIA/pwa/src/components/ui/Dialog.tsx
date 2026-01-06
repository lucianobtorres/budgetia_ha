import React, { useEffect } from 'react';
import { X } from 'lucide-react';

interface DialogProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    children: React.ReactNode;
    className?: string;
}

export function Dialog({ isOpen, onClose, title, children, className = '' }: DialogProps) {
    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose();
        };

        if (isOpen) {
            document.addEventListener('keydown', handleEscape);
            document.body.style.overflow = 'hidden';
        }

        return () => {
            document.removeEventListener('keydown', handleEscape);
            document.body.style.overflow = 'unset';
        };
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <div 
                className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200"
                onClick={onClose}
            />
            
            {/* Modal Content */}
            <div className={`
                relative bg-gray-900 border border-gray-800 rounded-2xl shadow-2xl 
                w-full max-h-[90vh] overflow-y-auto flex flex-col
                animate-in fade-in zoom-in-95 duration-200
                ${className}
            `}>
                <div className="flex items-center justify-between p-4 border-b border-gray-800">
                    <h2 className="text-lg font-semibold text-gray-100">{title}</h2>
                    <button 
                        onClick={onClose}
                        className="p-1 hover:bg-gray-800 rounded-lg transition-colors text-gray-400 hover:text-gray-200"
                    >
                        <X size={20} />
                    </button>
                </div>
                
                <div className="p-4">
                    {children}
                </div>
            </div>
        </div>
    );
}
