import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Clock, Search, UserCheck, Eye, Trash2, Ban, CheckCircle } from 'lucide-react';
import { fetchAPI } from '../services/api';
import { AuthService } from '../services/auth';
import { Button } from '../components/ui/Button';
import { toast } from 'sonner';

interface UserSummary {
    username: string;
    email: string;
    name: string;
    role: string;
    created_at: string;
    last_login?: string;
    trial_ends_at: string;
    status: 'ACTIVE' |'BLOCKED' | 'EXPIRED' | 'TRIAL_ENDING' | 'TRIAL_ACTIVE' | 'UNKNOWN' | 'LEGACY_ACTIVE' | 'ADMIN_USER';
}

export default function Admin() {
    const navigate = useNavigate();
    const [users, setUsers] = useState<UserSummary[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [filter, setFilter] = useState('');

    useEffect(() => {
        const role = AuthService.getUserRole();
        if (role !== 'admin') {
            toast.error("Acesso Negado. Área restrita.");
            navigate('/');
            return;
        }
        loadUsers();
    }, []);

    const loadUsers = async () => {
        try {
            setIsLoading(true);
            const data = await fetchAPI('/admin/users');
            setUsers(data);
        } catch (error) {
            toast.error("Erro ao carregar usuários");
        } finally {
            setIsLoading(false);
        }
    };

    const handleExtendTrial = async (username: string, days: number = 30) => {
        try {
            await fetchAPI(`/admin/users/${username}/extend-trial`, {
                method: 'POST',
                body: JSON.stringify({ days })
            });
            toast.success(`Trial de ${username} estendido por +${days} dias!`);
            loadUsers(); // Refresh
        } catch (error) {
            toast.error("Erro ao estender trial");
        }
    };

    const handleResetTrial = async (username: string) => {
        try {
            await fetchAPI(`/admin/users/${username}/reset-trial`, {
                 method: 'POST'
            });
            toast.success(`Trial de ${username} restaurado para 14 dias.`);
            loadUsers();
        } catch (error) {
            toast.error("Erro ao restaurar trial");
        }
    };

    const handleImpersonate = async (username: string) => {
        try {
            const data = await fetchAPI(`/admin/impersonate/${username}`, {
                method: 'POST'
            });
            
            // Login as target user
            AuthService.setSession(data.access_token, data.user);
            toast.success(`Logado como ${username}`);
            // Force reload to apply new user context
            window.location.href = '/';
        } catch (error) {
            toast.error("Erro ao impersonar usuário");
        }
    };

    const handleDelete = async (username: string) => {
        if (!confirm(`Tem certeza que deseja EXCLUIR PERMANENTEMENTE o usuário ${username}? Esta ação não pode ser desfeita.`)) return;

        try {
            await fetchAPI(`/admin/users/${username}`, { method: 'DELETE' });
            toast.success(`Usuário ${username} deletado.`);
            loadUsers();
        } catch (error) {
            toast.error("Erro ao deletar usuário");
        }
    };

    const handleToggleBlock = async (username: string) => {
        try {
            await fetchAPI(`/admin/users/${username}/toggle-block`, { method: 'POST' });
            toast.success(`Status de ${username} atualizado.`);
            loadUsers();
        } catch (error) {
            toast.error("Erro ao atualizar status");
        }
    };

    const filteredUsers = users.filter(u => 
        u.name.toLowerCase().includes(filter.toLowerCase()) || 
        u.email.toLowerCase().includes(filter.toLowerCase()) ||
        u.username.toLowerCase().includes(filter.toLowerCase())
    );

    const getStatusColor = (status: string) => {
        switch(status) {
            case 'BLOCKED': return 'text-red-500 bg-red-500/20 border-red-500/30';
            case 'TRIAL_ACTIVE': return 'text-green-400 bg-green-400/10 border-green-400/20';
            case 'TRIAL_ENDING': return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20';
            case 'EXPIRED': return 'text-red-400 bg-red-400/10 border-red-400/20';
            case 'ACTIVE': return 'text-blue-400 bg-blue-400/10 border-blue-400/20';
            case 'ADMIN_USER': return 'text-purple-400 bg-purple-400/10 border-purple-400/20';
            case 'LEGACY_ACTIVE': return 'text-gray-400 bg-white/5 border-white/10';
            default: return 'text-gray-400 bg-gray-400/10 border-gray-400/20';
        }
    };

    const formatDate = (iso: string) => {
        if (!iso) return '-';
        return new Date(iso).toLocaleDateString('pt-BR');
    };
    
    const formatDateTime = (iso?: string) => {
        if (!iso) return '-';
        return new Date(iso).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
    };

    const isNewUser = (createdAt: string, username: string) => {
        // Don't show "NEW" for myself
        const current = AuthService.getSessionUser();
        if (current === username) return false;

        if (!createdAt) return false;
        const diff = Date.now() - new Date(createdAt).getTime();
        return diff < 48 * 60 * 60 * 1000; // 48h
    };

    // Sort by created_at desc by default
    const sortedUsers = [...filteredUsers].sort((a, b) => {
        return new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime();
    });

    const [showBroadcast, setShowBroadcast] = useState(false);
    const [broadcastMsg, setBroadcastMsg] = useState("");
    const [broadcastMode, setBroadcastMode] = useState<'all' | 'select'>('all');
    const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
    const [userSearch, setUserSearch] = useState("");
    const [sendNotification, setSendNotification] = useState(true);
    const [sendEmail, setSendEmail] = useState(false);
    const [isBanner, setIsBanner] = useState(false);

    const handleBroadcast = async () => {
        if (!broadcastMsg) return;
        
        let targets: string[] = [];
        if (broadcastMode === 'select') {
             if (selectedUsers.length === 0) {
                 toast.error("Selecione pelo menos um usuário.");
                 return;
             }
             targets = selectedUsers;
        }

        try {
            await fetchAPI('/admin/broadcast', {
                method: 'POST',
                body: JSON.stringify({
                    message: broadcastMsg,
                    target_usernames: targets.length > 0 ? targets : null, // Backend expects null for ALL
                    title: "Mensagem Administrativa",
                    priority: "high",
                    send_notification: sendNotification,
                    send_email: sendEmail,
                    is_system_banner: isBanner
                })
            });
            toast.success("Mensagem enviada com sucesso!");
            setShowBroadcast(false);
            setBroadcastMsg("");
            setSelectedUsers([]);
            setBroadcastMode('all');
            setSendNotification(true);
            setSendEmail(false);
            setIsBanner(false);
        } catch (error) {
            toast.error("Erro ao enviar mensagem");
        }
    };

    const toggleUserSelection = (username: string) => {
        if (selectedUsers.includes(username)) {
            setSelectedUsers(selectedUsers.filter(u => u !== username));
        } else {
            setSelectedUsers([...selectedUsers, username]);
        }
    };

    if (isLoading) return <div className="p-8 text-center text-gray-500">Carregando painel administrativo...</div>;

    return (
        <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
            {/* Header */}
            <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <Shield className="w-6 h-6 text-purple-500" />
                        Admin CRM
                    </h1>
                    <p className="text-gray-400">Gestão de usuários, assinaturas e suporte.</p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                        <input 
                            type="text" 
                            placeholder="Buscar usuário..." 
                            className="bg-surface-card border border-border rounded-lg pl-9 pr-4 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-purple-500 w-64"
                            value={filter}
                            onChange={(e) => setFilter(e.target.value)}
                        />
                    </div>
                    
                    <Button variant="outline" size="sm" onClick={() => setShowBroadcast(true)} className="gap-2 border-purple-500/30 text-purple-400 hover:bg-purple-500/10">
                        <span className="text-lg">📢</span> Comunicado
                    </Button>

                    <Button variant="outline" size="sm" onClick={loadUsers}>
                        Atualizar
                    </Button>
                </div>
            </header>

            {/* Metrics Row */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl bg-surface-card border border-border">
                    <div className="text-gray-500 text-sm mb-1">Total de Usuários</div>
                    <div className="text-2xl font-bold">{users.length}</div>
                </div>
                <div className="p-4 rounded-xl bg-surface-card border border-border">
                    <div className="text-gray-500 text-sm mb-1">Trials Ativos</div>
                    <div className="text-2xl font-bold text-green-400">
                        {users.filter(u => u.status === 'TRIAL_ACTIVE' || u.status === 'TRIAL_ENDING').length}
                    </div>
                </div>
                <div className="p-4 rounded-xl bg-surface-card border border-border">
                    <div className="text-gray-500 text-sm mb-1">Logados Recentemente</div>
                    <div className="text-2xl font-bold text-blue-400">
                         {/* Considera logado recentemente quem logou nas últimas 24h - Simplificação visual apenas */}
                        {users.filter(u => u.last_login && new Date(u.last_login) > new Date(Date.now() - 86400000)).length}
                    </div>
                </div>
                <div className="p-4 rounded-xl bg-surface-card border border-border">
                    <div className="text-gray-500 text-sm mb-1">Novos (Hoje)</div>
                    <div className="text-2xl font-bold text-violet-400">
                        {users.filter(u => u.created_at?.startsWith(new Date().toISOString().split('T')[0])).length}
                    </div>
                </div>
            </div>

            {/* Users Table */}
            <div className="rounded-xl border border-border bg-surface-card overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-surface-hover/30 text-gray-400">
                            <tr>
                                <th className="p-4 font-medium">Usuário</th>
                                <th className="p-4 font-medium">Status / Plano</th>
                                <th className="p-4 font-medium">Último Login</th>
                                <th className="p-4 font-medium">Fim do Trial</th>
                                <th className="p-4 font-medium text-right">Ações CRM</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                            {sortedUsers.map(user => (
                                <tr key={user.username} className="hover:bg-white/5 transition-colors">
                                    <td className="p-4">
                                        <div className="flex items-center gap-2">
                                            <div className="font-medium text-white">{user.name}</div>
                                            {isNewUser(user.created_at, user.username) && (
                                                <span className="px-1.5 py-0.5 rounded text-[10px] bg-violet-500 text-white font-bold">NOVO</span>
                                            )}
                                        </div>
                                        <div className="text-xs text-gray-500 flex items-center gap-1">
                                            {user.email}
                                            {user.role === 'admin' && <Shield className="w-3 h-3 text-purple-400" />}
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getStatusColor(user.status)}`}>
                                            {user.status === 'ADMIN_USER' ? 'ADMIN' : user.status}
                                        </span>
                                    </td>
                                    <td className="p-4 text-gray-400 font-mono text-xs">
                                        {formatDateTime(user.last_login)}
                                    </td>
                                    <td className="p-4 text-gray-400 font-mono text-xs">
                                        <div className="flex items-center gap-2">
                                            <Clock className="w-3 h-3" />
                                            {formatDate(user.trial_ends_at)}
                                        </div>
                                    </td>
                                    <td className="p-4 text-right">
                                        <div className="flex items-center justify-end gap-2">
                                            {/* Não permitir impersonar outro admin */}
                                            {user.role !== 'admin' && (
                                                <Button
                                                    size="sm"
                                                    variant="outline"
                                                    onClick={() => handleImpersonate(user.username)}
                                                    className="h-8 w-8 p-0 border-blue-500/30 text-blue-400 hover:bg-blue-500/10"
                                                    title="Logar como usuário (Impersonate)"
                                                >
                                                    <Eye className="w-4 h-4" />
                                                </Button>
                                            )}

                                            {/* Only show CRM actions for non-admin users */}
                                            {user.role !== 'admin' && (
                                                <>
                                                    <Button 
                                                        size="sm" 
                                                        variant="outline"
                                                        className={`h-8 w-8 p-0 border-opacity-30 hover:bg-opacity-10 ${user.status === 'BLOCKED' ? 'border-green-500 text-green-400 hover:bg-green-500' : 'border-orange-500 text-orange-400 hover:bg-orange-500'}`}
                                                        onClick={() => handleToggleBlock(user.username)}
                                                        title={user.status === 'BLOCKED' ? "Desbloquear" : "Bloquear"}
                                                    >
                                                        {user.status === 'BLOCKED' ? <CheckCircle className="w-4 h-4" /> : <Ban className="w-4 h-4" />}
                                                    </Button>

                                                    <Button 
                                                        size="sm" 
                                                        variant="outline"
                                                        className="h-8 px-2 text-xs border-green-500/30 text-green-400 hover:bg-green-500/10"
                                                        onClick={() => handleExtendTrial(user.username, 14)}
                                                        title="Estender Trial por 14 dias"
                                                    >
                                                        +14d
                                                    </Button>
                                                    
                                                    <Button 
                                                        size="sm" 
                                                        variant="outline"
                                                        className="h-8 w-8 p-0 border-blue-500/30 text-blue-400 hover:bg-blue-500/10"
                                                        title="Estender Indefinidamente (VIP)"
                                                        onClick={() => handleExtendTrial(user.username, 3650)}
                                                    >
                                                        ∞
                                                    </Button>

                                                    <Button 
                                                        size="sm" 
                                                        variant="outline"
                                                        className="h-8 w-8 p-0 border-blue-500/30 text-blue-400 hover:bg-blue-500/10"
                                                        title="Restaurar Trial (Reset)"
                                                        onClick={() => handleResetTrial(user.username)}
                                                    >
                                                        <Clock className="w-4 h-4" />
                                                    </Button>
                                                    
                                                    <Button 
                                                        size="sm" 
                                                        variant="outline"
                                                        className="h-8 w-8 p-0 border-red-800/30 text-red-500 hover:bg-red-500/10"
                                                        title="Excluir Usuário e Dados"
                                                        onClick={() => handleDelete(user.username)}
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                    </Button>
                                                </>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Broadcast Modal */}
            {showBroadcast && (
                 <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                     <div className="bg-surface-card border border-border rounded-xl p-6 w-full max-w-lg shadow-2xl animate-in zoom-in-95 duration-200 lg:max-w-xl">
                         <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                             <span>📢</span> Enviar Comunicado
                         </h3>
                         
                         <div className="space-y-4">
                            {/* Target Selection Mode */}
                             <div className="flex bg-black/20 p-1 rounded-lg">
                                <button 
                                    className={`flex-1 py-1.5 text-sm rounded-md transition-all ${broadcastMode === 'all' ? 'bg-purple-500/20 text-purple-300' : 'text-gray-400 hover:bg-white/5'}`}
                                    onClick={() => setBroadcastMode('all')}
                                >
                                    Todos os Usuários
                                </button>
                                <button 
                                    className={`flex-1 py-1.5 text-sm rounded-md transition-all ${broadcastMode === 'select' ? 'bg-purple-500/20 text-purple-300' : 'text-gray-400 hover:bg-white/5'}`}
                                    onClick={() => setBroadcastMode('select')}
                                >
                                    Selecionar Usuários {selectedUsers.length > 0 && `(${selectedUsers.length})`}
                                </button>
                             </div>

                             {/* Multi-Select List */}
                            {broadcastMode === 'select' && (
                                <div className="border border-white/10 rounded-lg p-3 bg-black/20">
                                    <input 
                                        type="text"
                                        placeholder="Filtrar por nome..."
                                        className="w-full bg-transparent border-b border-white/10 pb-2 mb-2 text-sm focus:outline-none focus:border-purple-500/50"
                                        value={userSearch}
                                        onChange={(e) => setUserSearch(e.target.value)}
                                    />
                                    <div className="h-40 overflow-y-auto space-y-1 custom-scrollbar">
                                        {users.filter(u => u.role !== 'admin' && u.name.toLowerCase().includes(userSearch.toLowerCase())).map(u => (
                                            <div 
                                                key={u.username} 
                                                className={`flex items-center gap-3 p-2 rounded-md cursor-pointer text-sm transition-colors ${selectedUsers.includes(u.username) ? 'bg-purple-500/20' : 'hover:bg-white/5'}`}
                                                onClick={() => toggleUserSelection(u.username)}
                                            >
                                                <div className={`w-4 h-4 rounded border flex items-center justify-center ${selectedUsers.includes(u.username) ? 'bg-purple-500 border-purple-500' : 'border-gray-600'}`}>
                                                    {selectedUsers.includes(u.username) && <CheckCircle size={12} className="text-white" />}
                                                </div>
                                                <div className="flex-1">
                                                    <div className="text-white">{u.name}</div>
                                                    <div className="text-xs text-gray-500">{u.email}</div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                             <div>
                                 <label className="block text-sm text-gray-400 mb-1">Mensagem</label>
                                 <textarea
                                     className="w-full bg-black/20 border border-white/10 rounded-lg p-3 text-sm h-32 resize-none focus:outline-none focus:border-purple-500/50"
                                     placeholder="Digite a mensagem para os usuários..."
                                     value={broadcastMsg}
                                     onChange={(e) => setBroadcastMsg(e.target.value)}
                                 />
                             </div>
                             
                             <div className="flex gap-4">
                               <label className="flex items-center gap-2 cursor-pointer group">
                                   <input 
                                       type="checkbox" 
                                       className="w-4 h-4 rounded border-gray-600 bg-black/20 text-purple-500 focus:ring-purple-500/50"
                                       checked={sendNotification}
                                       onChange={(e) => setSendNotification(e.target.checked)}
                                   />
                                   <span className="text-sm text-gray-400 group-hover:text-gray-300">Notificação (Sininho)</span>
                               </label>
                               
                               <label className="flex items-center gap-2 cursor-pointer group">
                                   <input 
                                       type="checkbox" 
                                       className="w-4 h-4 rounded border-gray-600 bg-black/20 text-purple-500 focus:ring-purple-500/50"
                                       checked={sendEmail}
                                       onChange={(e) => setSendEmail(e.target.checked)}
                                   />
                                   <span className="text-sm text-gray-400 group-hover:text-gray-300">Enviar por E-mail</span>
                               </label>
                               
                               <label className="flex items-center gap-2 cursor-pointer group">
                                   <input 
                                       type="checkbox" 
                                       className="w-4 h-4 rounded border-gray-600 bg-black/20 text-purple-500 focus:ring-purple-500/50"
                                       checked={isBanner}
                                       onChange={(e) => setIsBanner(e.target.checked)}
                                   />
                                   <span className="text-sm text-gray-400 group-hover:text-gray-300">Definir como Banner Global</span>
                               </label>
                             </div>

                             <div className="flex justify-end gap-3 pt-2">
                                 <Button variant="ghost" onClick={() => setShowBroadcast(false)}>
                                     Cancelar
                                 </Button>
                                 <Button onClick={handleBroadcast} disabled={!broadcastMsg || (!sendNotification && !sendEmail && !isBanner)}>
                                     Enviar {broadcastMode === 'select' && selectedUsers.length > 0 ? `(${selectedUsers.length})` : ''}
                                 </Button>
                             </div>
                         </div>
                     </div>
                 </div>
            )}
        </div>
    );
}
