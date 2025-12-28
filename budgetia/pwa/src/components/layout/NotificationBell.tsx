import { useState, useEffect } from 'react';
import { Bell, Check, Trash2 } from 'lucide-react';
import { fetchAPI } from '../../services/api';
import { cn } from '../../utils/cn';
import { toast } from 'sonner';
import { Drawer } from '../ui/Drawer';
import { Button } from '../ui/Button';
import { telemetry } from '../../services/telemetry';

interface Notification {
    id: string;
    // Backend API fields
    timestamp?: string;
    message?: string;
    category?: string;
    read?: boolean;
    priority?: string;
     // Legacy/Fallback fields
    titulo?: string;
    mensagem?: string;
    lida?: boolean;
    data_criacao?: string;
}

const getCategoryTitle = (category?: string) => {
    if (!category) return 'Notificação';
    switch(category) {
        case 'financial_reminder': return 'Lembrete Financeiro';
        case 'financial_alert': return 'Alerta Financeiro';
        case 'budget_exceeded': return 'Orçamento Excedido';
        case 'insight': return 'Insight Financeiro';
        default: return 'Notificação'; // Fallback for unknown categories
    }
};

export function NotificationBell() {
    const [isOpen, setIsOpen] = useState(false);
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [loading, setLoading] = useState(true);

    // Initial Load
    useEffect(() => {
        loadNotifications();
        // Periodically refresh (e.g. every 60s)
        const interval = setInterval(loadNotifications, 60000);
        return () => clearInterval(interval);
    }, []);

    const loadNotifications = async () => {
        try {
            const data = await fetchAPI('/notifications/?unread_only=false');
            if (data) setNotifications(data);
        } catch (error) {
            console.error("Error loading notifications", error);
        } finally {
            setLoading(false);
        }
    };

    const markAsRead = async (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            await fetchAPI(`/notifications/${id}/read`, { method: 'POST' });
            // Handle both field conventions in local state update
            
            // TELEMETRY: Positive feedback (Clicked/Read)
            // Localiza a notificação para pegar a categoria/regra
            const notif = notifications.find(n => n.id === id);
            if (notif && notif.category) {
                 // Assumindo que o nome da regra está na categoria ou mensagem se for estruturada
                 // Como simplificação, usaremos a categoria como proxy do rule_name por enquanto
                 telemetry.logFeedback(notif.category, 'positive');
            }

            setNotifications(prev => prev.map(n => 
                n.id === id ? { ...n, read: true, lida: true } : n
            ));
        } catch (error) {
            console.error(error);
        }
    };

    const deleteNotification = async (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            await fetchAPI(`/notifications/${id}`, { method: 'DELETE' });
            
            // TELEMETRY: Dismissed feedback
            const notif = notifications.find(n => n.id === id);
            if (notif && notif.category) {
                 const isRead = notif.read || notif.lida;
                 // Se deletou sem ler = Ignored/Dismissed
                 // Se deletou lido = Neutral/Cleanup (não logamos negativo)
                 if (!isRead) {
                    telemetry.logFeedback(notif.category, 'dismissed');
                 }
            }

            setNotifications(prev => prev.filter(n => n.id !== id));
            toast.success("Notificação removida");
        } catch (error) {
            console.error(error);
        }
    };

    const markAllRead = async () => {
         try {
            await fetchAPI(`/notifications/read-all`, { method: 'POST' });
            setNotifications(prev => prev.map(n => ({ ...n, read: true, lida: true })));
            toast.success("Todas marcadas como lidas");
        } catch (error) {
            console.error(error);
        }
    }

    const unreadCount = notifications.filter(n => {
        // Check both 'read' and 'lida' for safety
        const isRead = n.read === true || n.lida === true;
        return !isRead;
    }).length;

    return (
        <>
            <Button
                onClick={() => setIsOpen(true)}
                variant="ghost"
                size="icon"
                className="relative border border-gray-800 bg-gray-800/50 hover:bg-gray-800 hover:text-white"
            >
                <Bell size={20} />
                {unreadCount > 0 && (
                    <span className="absolute top-2 right-2 flex h-2.5 w-2.5">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500"></span>
                    </span>
                )}
            </Button>

            <Drawer isOpen={isOpen} onClose={() => setIsOpen(false)} title="Notificações">
                 <div className="flex flex-col h-full">
                    {unreadCount > 0 && (
                         <div className="flex justify-end mb-4 flex-none">
                             <button 
                                onClick={markAllRead} 
                                className="text-sm text-emerald-400 hover:text-emerald-300 flex items-center gap-1 bg-emerald-500/10 px-3 py-1.5 rounded-full border border-emerald-500/20"
                            >
                                <Check size={14} />
                                Marcar todas como lidas
                            </button>
                         </div>
                    )}

                    <div className="flex-1 overflow-y-auto space-y-3 pb-safe">
                        {loading ? (
                            <div className="p-8 text-center text-gray-500">
                                <span className="animate-pulse">Carregando...</span>
                            </div>
                        ) : notifications.length === 0 ? (
                            <div className="p-8 text-center flex flex-col items-center justify-center opacity-50">
                                <Bell className="h-12 w-12 text-gray-600 mb-4" />
                                <p className="text-gray-400 text-lg">Tudo limpo por aqui.</p>
                                <p className="text-sm text-gray-600">Nenhuma notificação nova.</p>
                            </div>
                        ) : (
                             notifications.map((notif) => {
                                // Robust Field Resolution
                                const isRead = notif.read === true || notif.lida === true;
                                
                                const categoryTitle = getCategoryTitle(notif.category);
                                const fallbackTitle = notif.titulo || "Notificação";
                                // Prefer Category Title over Fallback unless category is missing
                                const title = notif.category ? categoryTitle : fallbackTitle;

                                const message = notif.message || notif.mensagem || "";
                                
                                const dateStr = notif.timestamp || notif.data_criacao;
                                const dateDisplay = dateStr ? new Date(dateStr).toLocaleString() : "";

                                return (
                                <div 
                                    key={notif.id} 
                                    className={cn(
                                        "p-4 rounded-xl border transition-all flex gap-3 relative overflow-hidden",
                                        isRead 
                                            ? "bg-gray-900/30 border-gray-800 opacity-75" 
                                            : "bg-gray-800/40 border-gray-700 shadow-sm"
                                    )}
                                >
                                    {/* Indicator */}
                                    <div className={cn(
                                        "mt-1.5 h-2.5 w-2.5 rounded-full flex-shrink-0",
                                        isRead ? "bg-transparent" : "bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]"
                                    )} />
                                    
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-start justify-between gap-2">
                                            <h4 className={cn("text-base font-semibold truncate pr-8", isRead ? "text-gray-400" : "text-white")}>
                                                {title}
                                            </h4>
                                        </div>
                                        {/* Allow whitespace-pre-wrap to handle newlines in message if any */}
                                        <p className="text-sm text-gray-400 mt-1 leading-relaxed whitespace-pre-wrap line-clamp-3">
                                            {message.replace(/\*\*/g, '')} {/* Simple strip markdown bold */}
                                        </p>
                                        <p className="text-xs text-gray-600 mt-2 font-medium">
                                            {dateDisplay}
                                        </p>
                                    </div>
                                    
                                    {/* Quick Actions */}
                                    <div className="flex flex-col gap-2 pl-2 border-l border-gray-800/50">
                                        {!isRead && (
                                            <button 
                                                onClick={(e) => markAsRead(notif.id, e)}
                                                className="p-2 text-gray-500 hover:text-emerald-400 hover:bg-emerald-500/10 rounded-lg transition-colors"
                                                title="Marcar lida"
                                            >
                                                <Check size={18} />
                                            </button>
                                        )}
                                            <button 
                                            onClick={(e) => deleteNotification(notif.id, e)}
                                            className="p-2 text-gray-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                                            title="Excluir"
                                        >
                                            <Trash2 size={18} />
                                        </button>
                                    </div>
                                </div>
                            )})
                        )}
                    </div>
                </div>
            </Drawer>
        </>
    );
}
