import { useState, useEffect } from 'react';
import { fetchAPI } from '../services/api';
import { Bell, Check, Trash2, Mail } from 'lucide-react';
import { cn } from '../utils/cn';

interface Notification {
    id: string;
    titulo: string;
    mensagem: string;
    lida: boolean;
    data_criacao: string;
    tipo: string;
}

export default function Notifications() {
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadNotifications();
    }, []);

    const loadNotifications = async () => {
        try {
            // Fetch all notifications (unread_only=false) to see history
            const data = await fetchAPI('/notifications/?unread_only=false');
            if (data) setNotifications(data);
        } catch (error) {
            console.error("Error loading notifications", error);
        } finally {
            setLoading(false);
        }
    };

    const markAsRead = async (id: string) => {
        try {
            await fetchAPI(`/notifications/${id}/read`, { method: 'POST' });
            setNotifications(prev => prev.map(n => n.id === id ? { ...n, lida: true } : n));
        } catch (error) {
            console.error("Error marking as read", error);
        }
    };

    const deleteNotification = async (id: string) => {
        try {
            await fetchAPI(`/notifications/${id}`, { method: 'DELETE' });
            setNotifications(prev => prev.filter(n => n.id !== id));
        } catch (error) {
            console.error("Error deleting notification", error);
        }
    };

    const markAllRead = async () => {
         try {
            await fetchAPI(`/notifications/read-all`, { method: 'POST' });
            setNotifications(prev => prev.map(n => ({ ...n, lida: true })));
        } catch (error) {
            console.error("Error marking all read", error);
        }
    }

    const unreadCount = notifications.filter(n => !n.lida).length;

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight text-white">Notificações</h2>
                    <p className="text-gray-400">Alertas e avisos importantes.</p>
                </div>
                {unreadCount > 0 && (
                    <button 
                        onClick={markAllRead}
                        className="flex items-center space-x-2 text-sm text-emerald-400 hover:text-emerald-300 transition-colors"
                    >
                        <Check size={16} />
                        <span>Marcar todas como lidas</span>
                    </button>
                )}
            </div>

            <div className="space-y-4">
                {loading ? (
                    <p className="text-gray-400">Carregando...</p>
                ) : notifications.length === 0 ? (
                    <div className="text-center py-12 bg-gray-900/50 rounded-xl border border-gray-800">
                        <Bell size={48} className="mx-auto text-gray-600 mb-4" />
                        <p className="text-gray-400">Você não tem notificações.</p>
                    </div>
                ) : (
                    notifications.map((notif) => (
                        <div 
                            key={notif.id} 
                            className={cn(
                                "flex items-start justify-between p-4 rounded-xl border transition-all",
                                notif.lida 
                                    ? "bg-gray-900/30 border-gray-800 opacity-75" 
                                    : "bg-gray-900/80 border-gray-700 shadow-md transform hover:scale-[1.01]"
                            )}
                        >
                            <div className="flex space-x-4">
                                <div className={cn(
                                    "mt-1 h-8 w-8 rounded-full flex items-center justify-center shrink-0",
                                    notif.lida ? "bg-gray-800 text-gray-500" : "bg-blue-500/20 text-blue-400"
                                )}>
                                    <Mail size={16} />
                                </div>
                                <div>
                                    <h4 className={cn("text-sm font-semibold", notif.lida ? "text-gray-400" : "text-white")}>
                                        {notif.titulo}
                                    </h4>
                                    <p className="text-sm text-gray-400 mt-1">{notif.mensagem}</p>
                                    <p className="text-xs text-gray-600 mt-2">
                                        {new Date(notif.data_criacao).toLocaleString()}
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-center space-x-2">
                                {!notif.lida && (
                                    <button 
                                        onClick={() => markAsRead(notif.id)}
                                        className="p-2 text-gray-400 hover:text-emerald-400 hover:bg-emerald-500/10 rounded-full transition-colors"
                                        title="Marcar como lida"
                                    >
                                        <Check size={16} />
                                    </button>
                                )}
                                <button 
                                    onClick={() => deleteNotification(notif.id)}
                                    className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-full transition-colors"
                                    title="Excluir"
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
