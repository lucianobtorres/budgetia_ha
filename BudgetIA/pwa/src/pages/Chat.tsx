import { useState, useRef, useEffect } from 'react';
import { Send, Trash2, Bot, Loader2 } from 'lucide-react';
import { fetchAPI } from '../services/api';
import { cn } from '../utils/cn';

interface Message {
    role: 'user' | 'assistant';
    content: string;
}

export default function Chat() {
    const [messages, setMessages] = useState<Message[]>([
        { role: 'assistant', content: 'Olá! Sou seu assistente financeiro. Como posso ajudar com suas finanças hoje?' }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const userMsg: Message = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const data = await fetchAPI('/chat/message', {
                method: 'POST',
                body: JSON.stringify({ message: userMsg.content }),
            });

            const botMsg: Message = { role: 'assistant', content: data.response };
            setMessages(prev => [...prev, botMsg]);
        } catch (error) {
            console.error(error);
            setMessages(prev => [...prev, { role: 'assistant', content: 'Desculpe, ocorreu um erro ao processar sua mensagem.' }]);
        } finally {
            setLoading(false);
        }
    };

    const handleClear = async () => {
        if (confirm('Limpar histórico de conversa?')) {
             try {
                await fetchAPI('/chat/history', { method: 'DELETE' });
                setMessages([{ role: 'assistant', content: 'Histórico limpo. Como posso ajudar?' }]);
            } catch (error) {
                console.error(error);
            }
        }
    }

    return (
        <div className="flex flex-col h-[calc(100vh-8rem)] rounded-xl border border-gray-800 bg-gray-900/50 overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-800 bg-gray-900">
                <div className="flex items-center space-x-3">
                    <div className="h-10 w-10 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-400">
                        <Bot size={24} />
                    </div>
                    <div>
                        <h3 className="font-semibold text-white">Assistente Financeiro</h3>
                        <p className="text-xs text-emerald-400 flex items-center">
                            <span className="w-2 h-2 rounded-full bg-emerald-500 mr-2 animate-pulse"></span>
                            Online
                        </p>
                    </div>
                </div>
                <button 
                    onClick={handleClear}
                    className="p-2 text-gray-500 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
                    title="Limpar Histórico"
                >
                    <Trash2 size={20} />
                </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6 bg-gray-950/50">
                {messages.map((msg, idx) => (
                    <div key={idx} className={cn("flex", msg.role === 'user' ? "justify-end" : "justify-start")}>
                        <div className={cn(
                            "flex max-w-[80%] rounded-2xl p-4 shadow-sm",
                            msg.role === 'user' 
                                ? "bg-emerald-600 text-white rounded-tr-sm" 
                                : "bg-gray-800 text-gray-100 rounded-tl-sm"
                        )}>
                            <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                        </div>
                    </div>
                ))}
                {loading && (
                     <div className="flex justify-start">
                        <div className="bg-gray-800 text-gray-100 rounded-2xl rounded-tl-sm p-4 flex items-center space-x-2">
                             <Loader2 size={16} className="animate-spin text-emerald-400" />
                             <span className="text-sm text-gray-400">Digitando...</span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 bg-gray-900 border-t border-gray-800">
                <div className="relative flex items-center">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                        placeholder="Digite sua mensagem..."
                        className="w-full bg-gray-950 border border-gray-700 text-white rounded-xl pl-4 pr-12 py-3 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all placeholder-gray-500"
                        disabled={loading}
                    />
                    <button
                        onClick={handleSend}
                        disabled={loading || !input.trim()}
                        className="absolute right-2 p-2 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 disabled:opacity-50 disabled:hover:bg-emerald-500 transition-colors"
                    >
                        <Send size={18} />
                    </button>
                </div>
            </div>
        </div>
    );
}
