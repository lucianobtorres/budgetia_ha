import { useState, useRef, useEffect } from 'react';
import { Bot, Loader2 } from 'lucide-react';
import { MessageBubble } from '../components/chat/MessageBubble';
import { ChatInput } from '../components/chat/ChatInput';
import { fetchAPI } from '../services/api';
import { cn } from '../utils/cn';
import { toast } from 'sonner';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    steps?: {
        tool: string;
        tool_input: any;
        log: string;
        observation: string;
    }[];
}

interface ChatProps {
    className?: string;
    variant?: 'full' | 'widget';
    onAction?: () => void;
}

export default function Chat({ className, variant = 'full', onAction }: ChatProps) {
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
        loadHistory();
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const loadHistory = async () => {
        try {
            const history = await fetchAPI('/chat/history');
            if (history && Array.isArray(history) && history.length > 0) {
                 // Prepend welcome message locally so it persists visually
                 const welcomeMsg: Message = { role: 'assistant', content: 'Olá! Sou seu assistente financeiro. Como posso ajudar com suas finanças hoje?' };
                 setMessages([welcomeMsg, ...history]);
            }
        } catch (error) {
            console.error("Failed to load chat history", error);
            toast.error("Falha ao carregar histórico");
        }
    };

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

            const botMsg: Message = { 
                role: 'assistant', 
                content: data.response,
                steps: data.intermediate_steps 
            };
            setMessages(prev => [...prev, botMsg]);
            
            // Notify parent to refresh data
            if (onAction) {
                onAction();
            }
        } catch (error) {
            console.error(error);
            setMessages(prev => [...prev, { role: 'assistant', content: 'Desculpe, ocorreu um erro ao processar sua mensagem.' }]);
            toast.error("Erro ao enviar mensagem");
        } finally {
            setLoading(false);
        }
    };

    const handleClear = async () => {
        // Simple confirm for now, maybe replace with a better UI dialog later
        if (confirm('Limpar histórico de conversa?')) {
             try {
                await fetchAPI('/chat/history', { method: 'DELETE' });
                setMessages([{ role: 'assistant', content: 'Histórico limpo. Como posso ajudar?' }]);
                toast.success("Histórico limpo com sucesso");
            } catch (error) {
                console.error(error);
                toast.error("Falha ao limpar histórico");
            }
        }
    }

    return (
        <div className={cn(
            "flex flex-col overflow-hidden",
            variant === 'full' ? "h-[calc(100vh-8rem)]" : "h-full",
            className
        )}>
            {/* Messages Area with Top Fade Mask */}
            <div className="flex-1 overflow-y-auto px-2 py-4 space-y-6 [mask-image:linear-gradient(to_bottom,transparent,black_10%)] scrollbar-none">
                {messages.length === 0 && (
                    <div className="h-full flex flex-col items-center justify-center text-gray-500 opacity-50">
                        <Bot size={48} className="mb-2" />
                        <p>Assistente pronto</p>
                    </div>
                )}
                
                {messages.map((msg, idx) => (
                    <div key={idx}>
                         {/* Adapter for MessageBubble since we defined MessageProps slightly differently in local state before */}
                        <MessageBubble message={msg as any} /> 
                    </div>
                ))}
                {loading && (
                     <div className="flex justify-start">
                        <div className="bg-gray-800/80 text-gray-100 rounded-2xl rounded-tl-sm p-4 flex items-center space-x-2 border border-gray-700/50">
                             <Loader2 size={16} className="animate-spin text-emerald-400" />
                             <span className="text-sm text-gray-400">Pensando...</span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Combined Input Row */}
            <div className="p-2 pt-0">
                <ChatInput 
                    value={input}
                    onChange={setInput}
                    onSend={handleSend}
                    onClear={handleClear}
                    loading={loading}
                    showClear={true}
                    autoFocus={true}
                />
            </div>
        </div>
    );
}
