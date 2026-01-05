import React from 'react';
import { Send, Trash2 } from 'lucide-react';

interface ChatInputProps {
    value: string;
    onChange: (value: string) => void;
    onSend: () => void;
    onClear?: () => void;
    loading?: boolean;
    placeholder?: string;
    showClear?: boolean;
    autoFocus?: boolean;
}

export function ChatInput({ 
    value, 
    onChange, 
    onSend, 
    onClear, 
    loading = false, 
    placeholder = "Digite sua mensagem...",
    showClear = true,
    autoFocus = false
}: ChatInputProps) {
    const inputRef = React.useRef<HTMLInputElement>(null);

    React.useEffect(() => {
        if (!loading) {
            // Re-focus after loading finishes or on mount if autoFocus is true
            if (autoFocus) {
                 setTimeout(() => {
                    inputRef.current?.focus();
                 }, 10);
            }
        }
    }, [loading, autoFocus]);

    return (
        <div className="relative flex items-end gap-2">
            {showClear && onClear && (
                <button
                    onClick={onClear}
                    className="p-3 mb-1 text-gray-500 hover:text-red-400 hover:bg-red-400/10 rounded-full transition-colors flex-none"
                    title="Limpar Histórico"
                    disabled={loading}
                >
                    <Trash2 size={20} />
                </button>
            )}

            <div className="relative flex-1 bg-gray-900/80 border border-gray-700 rounded-2xl focus-within:border-emerald-500/50 focus-within:bg-gray-900 transition-all flex items-center">
                <input
                    ref={inputRef}
                    type="text"
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && onSend()}
                    placeholder={placeholder}
                    className="w-full bg-transparent border-none text-white pl-4 pr-12 py-3 focus:ring-0 outline-none focus:outline-none text-sm placeholder-gray-500 min-h-[48px]"
                    disabled={loading}
                    autoFocus={autoFocus}
                />
                <button
                    onClick={onSend}
                    disabled={loading || !value.trim()}
                    className="absolute right-1.5 p-2 bg-emerald-500 text-white rounded-xl hover:bg-emerald-600 disabled:opacity-50 disabled:hover:bg-emerald-500 transition-colors shadow-lg shadow-emerald-900/20"
                >
                    <Send size={18} />
                </button>
            </div>
        </div>
    );
}
