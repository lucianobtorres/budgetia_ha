import { useState, useEffect } from 'react';
import { User, Brain, ShieldAlert, Download, Save, Trash2, FileSpreadsheet, CheckCircle, XCircle, Settings, HardDrive, LogOut } from 'lucide-react';
import { fetchAPI } from '../services/api';

import { toast } from 'sonner';
import { STORAGE_KEYS, DEFAULT_USER_FALLBACK } from '../utils/constants';
import { GlassCard } from '../components/ui/GlassCard';
import { GradientBanner } from '../components/ui/GradientBanner';
import { PageHeader } from '../components/ui/PageHeader';
import { SegmentedControl } from '../components/ui/SegmentedControl';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { PushNotificationCard } from '../components/profile/PushNotificationCard';

interface ProfileItem {
    Campo: string;
    Valor: string;
    Observações?: string;
    [key: string]: any;
}

interface MemoryFact {
    content: string;
    created_at: string;
    source: string;
}

interface WatchdogRule {
    id: string;
    category: string;
    threshold: number;
    period: string;
    custom_message?: string;
}

interface DriveStatus {
    has_credentials: boolean;
    backend_consent: boolean;
    is_google_sheet: boolean;
    planilha_path: string;
}

export default function Profile() {
    const [userId, setUserId] = useState('');
    const [activeTab, setActiveTab] = useState<'profile' | 'memory' | 'rules' | 'settings'>('profile');
    
    // Data States
    const [profileData, setProfileData] = useState<ProfileItem[]>([]);
    const [memoryFacts, setMemoryFacts] = useState<MemoryFact[]>([]);
    const [rules, setRules] = useState<WatchdogRule[]>([]);
    const [driveStatus, setDriveStatus] = useState<DriveStatus | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        setUserId(localStorage.getItem(STORAGE_KEYS.USER_ID) || DEFAULT_USER_FALLBACK);
        loadAllData();
    }, []);

    const loadAllData = async () => {
        setLoading(true);
        try {
            const [prof, mem, rul, drive] = await Promise.all([
                fetchAPI('/profile/'),
                fetchAPI('/profile/memory'),
                fetchAPI('/profile/rules'),
                fetchAPI('/profile/settings/google-drive')
            ]);
            if (prof) setProfileData(prof);
            if (mem) setMemoryFacts(mem);
            if (rul) setRules(rul);
            if (drive) setDriveStatus(drive);
        } catch (error) {
            console.error("Erro ao carregar dados do perfil", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSaveUserId = () => {
        localStorage.setItem(STORAGE_KEYS.USER_ID, userId);
        toast.success("Conta conectada!");
        window.location.href = '/';
    };

    const handleProfileEdit = (index: number, field: keyof ProfileItem, value: string) => {
        const newData = [...profileData];
        newData[index] = { ...newData[index], [field]: value };
        setProfileData(newData);
    };

    const saveProfile = async () => {
        try {
            await fetchAPI('/profile/bulk', {
                method: 'PUT',
                body: JSON.stringify(profileData)
            });
            toast.success('Perfil atualizado com sucesso!');
        } catch (error) {
            toast.error('Erro ao salvar perfil.');
        }
    };

    const deleteMemory = async (content: string) => {
        if(!confirm("Esquecer este fato?")) return;
        try {
            await fetchAPI(`/profile/memory/${encodeURIComponent(content)}`, { method: 'DELETE' });
            setMemoryFacts(prev => prev.filter(f => f.content !== content));
        } catch (error) {
            toast.error('Erro ao esquecer fato.');
        }
    };

    const deleteRule = async (id: string) => {
        if(!confirm("Remover esta regra?")) return;
        try {
            await fetchAPI(`/profile/rules/${id}`, { method: 'DELETE' });
            setRules(prev => prev.filter(r => r.id !== id));
        } catch (error) {
            toast.error('Erro ao remover regra.');
        }
    };

    const handleExport = async () => {
        try {
            const response = await fetch('/api/dashboard/export', { 
                headers: { 'X-User-ID': userId }
            });
            if (!response.ok) throw new Error('Falha no download');
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'budgetia_export.xlsx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            toast.error('Erro ao exportar arquivo.');
            console.error(error);
        }
    };

    const handleDriveShare = async () => {
        try {
            const apiRes = await fetchAPI('/profile/settings/google-drive/share', { method: 'POST' });
            toast.success(apiRes.message);
            const drive = await fetchAPI('/profile/settings/google-drive');
            if (drive) setDriveStatus(drive);
        } catch (error) {
            toast.error('Erro ao habilitar Google Drive.');
        }
    };

    const handleDriveRevoke = async () => {
        if(!confirm("Tem certeza? O Agente não poderá mais atualizar a planilha em segundo plano.")) return;
        try {
            const apiRes = await fetchAPI('/profile/settings/google-drive/revoke', { method: 'POST' });
            toast.success(apiRes.message);
            const drive = await fetchAPI('/profile/settings/google-drive');
            if (drive) setDriveStatus(drive);
        } catch (error) {
            toast.error('Erro ao desabilitar Google Drive.');
        }
    };

    const tabs = [
        { id: 'profile', label: 'Dados', icon: User, color: 'text-emerald-400' },
        { id: 'memory', label: 'Memória', icon: Brain, color: 'text-violet-400' },
        { id: 'rules', label: 'Regras', icon: ShieldAlert, color: 'text-orange-400' },
        { id: 'settings', label: 'Conta', icon: Settings, color: 'text-blue-400' }
    ] as const;



    return (
        <div className="h-full flex flex-col gap-6 overflow-hidden">
            {/* Fixed Header */}
             <div className="flex-none pt-safe space-y-4">
                <PageHeader 
                    title="Seu Perfil" 
                    description="Gerencie seus dados e a IA."
                    className="pt-0 !space-y-0" // Reset padding since we are inside a container
                    action={
                        <div className="flex space-x-2">
                             <Button 
                                 onClick={handleExport}
                                 variant="neutral"
                                 title="Backup Excel"
                                 icon={Download}
                             >
                                 <span className="hidden md:inline">Backup</span>
                             </Button>
                        </div>
                    }
                />

                
                {/* Tabs - Connections Style */}
                <SegmentedControl 
                    options={tabs.map(t => ({ id: t.id, label: t.label, icon: t.icon, activeColor: t.color }))}
                    value={activeTab}
                    onChange={(val) => setActiveTab(val as any)}
                />
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto pb-20 scrollbar-thin scrollbar-thumb-gray-800">
                <div className="bg-gray-900/30 border border-gray-800/50 rounded-2xl p-6 min-h-[300px]">
                    {loading ? (
                        <div className="flex items-center justify-center h-40 text-gray-400 gap-2">
                            <span className="w-1 h-1 bg-gray-400 rounded-full animate-bounce"></span>
                            <span className="w-1 h-1 bg-gray-400 rounded-full animate-bounce delay-100"></span>
                            <span className="w-1 h-1 bg-gray-400 rounded-full animate-bounce delay-200"></span>
                        </div>
                    ) : (
                        <div className="max-w-2xl mx-auto animate-in fade-in slide-in-from-bottom-2 duration-300">
                            
                            {/* PROFILE EDITOR */}
                            {activeTab === 'profile' && (
                                <div className="space-y-6">
                                    <GradientBanner 
                                        icon={User}
                                        title="Dados Pessoais"
                                        description="Informações que a IA usa para personalizar o atendimento."
                                        variant="emerald"
                                    />

                                    <GlassCard variant="emerald" className="divide-y divide-gray-800 overflow-hidden" hoverEffect={false}>
                                        {profileData.map((item, idx) => (
                                            <div key={idx} className="p-4 hover:bg-gray-900/80 transition-colors flex flex-col md:flex-row md:items-center gap-2">
                                                <div className="md:w-1/3">
                                                    <span className="text-sm font-medium text-gray-400">{item.Campo}</span>
                                                </div>
                                                <div className="md:w-2/3">
                                                    <Input 
                                                        value={item.Valor}
                                                        onChange={(e) => handleProfileEdit(idx, 'Valor', e.target.value)}
                                                        className="bg-transparent focus:bg-gray-900/50 border-b border-transparent border-t-0 border-l-0 border-r-0 focus:border-b-emerald-500 rounded-none w-full text-white px-2 py-1 focus:outline-none transition-all focus:ring-0"
                                                        placeholder="Valor..."
                                                    />
                                                </div>
                                            </div>
                                        ))}
                                        {profileData.length === 0 && (
                                             <div className="p-8 text-center text-gray-500">Nenhum dado de perfil encontrado.</div>
                                        )}
                                    </GlassCard>

                                    <div className="flex justify-end pt-2">
                                        <Button 
                                            onClick={saveProfile}
                                            variant="primary"
                                            icon={Save}
                                            className="w-full md:w-auto md:px-8"
                                            isLoading={loading}
                                        >
                                            Salvar Dados
                                        </Button>
                                    </div>
                                </div>
                            )}

                            {/* MEMORY VIEWER */}
                            {activeTab === 'memory' && (
                                <div className="space-y-6">
                                    <GradientBanner 
                                        icon={Brain}
                                        title="Memória da IA"
                                        description="Fatos aprendidos sobre você durante as conversas."
                                        variant="violet"
                                    />

                                    <div className="grid gap-4 md:grid-cols-2">
                                        {memoryFacts.length === 0 ? (
                                            <div className="col-span-2 text-center py-10 bg-gray-900/30 rounded-xl border border-gray-800 border-dashed">
                                                <Brain size={48} className="mx-auto text-gray-700 mb-2" />
                                                <p className="text-gray-500">O cérebro da IA está vazio.</p>
                                            </div>
                                        ) : (
                                            memoryFacts.map((fact, idx) => (
                                                <GlassCard 
                                                    key={idx} 
                                                    variant="violet" 
                                                    className="p-5 flex justify-between items-start group"
                                                >
                                                    <div className="flex-1 pr-4">
                                                        <p className="text-white font-medium text-sm leading-relaxed mb-2">{fact.content}</p>
                                                        <div className="flex items-center gap-2 text-[10px] text-gray-500 uppercase tracking-wider font-semibold">
                                                            <span>{fact.source}</span>
                                                            <span className="w-1 h-1 rounded-full bg-gray-700"></span>
                                                            <span>{fact.created_at}</span>
                                                        </div>
                                                    </div>
                                                    <button 
                                                        onClick={() => deleteMemory(fact.content)}
                                                        className="text-gray-600 hover:text-red-400 p-2 hover:bg-red-500/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                                                        title="Esquecer"
                                                    >
                                                        <Trash2 size={16} />
                                                    </button>
                                                </GlassCard>
                                            ))
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* RULES VIEWER */}
                            {activeTab === 'rules' && (
                                <div className="space-y-6">
                                    <GradientBanner 
                                        icon={ShieldAlert}
                                        title="Regras de Monitoramento"
                                        description="Alertas automáticos para gastos excessivos."
                                        variant="orange"
                                    />

                                    <div className="grid gap-4 md:grid-cols-2">
                                        {rules.length === 0 ? (
                                            <div className="col-span-2 text-center py-10 bg-gray-900/30 rounded-xl border border-gray-800 border-dashed">
                                                <ShieldAlert size={48} className="mx-auto text-gray-700 mb-2" />
                                                <p className="text-gray-500">Nenhuma regra ativa.</p>
                                            </div>
                                        ) : (
                                            rules.map((rule) => (
                                                <GlassCard 
                                                    key={rule.id} 
                                                    variant="orange" 
                                                    className="p-5 flex justify-between items-start group"
                                                >
                                                    <div>
                                                        <div className="flex items-center space-x-2 mb-3">
                                                            <span className="text-orange-400 font-bold bg-orange-950/30 px-2 py-1 rounded text-sm">{rule.category}</span>
                                                            <span className="text-gray-500 text-[10px] uppercase font-bold bg-gray-900 px-2 py-1 rounded border border-gray-800">
                                                                {rule.period === 'monthly' ? 'Mensal' : 'Semanal'}
                                                            </span>
                                                        </div>
                                                        <p className="text-gray-400 text-sm mb-2">Limite: <span className="text-white font-mono font-bold text-lg">R$ {rule.threshold}</span></p>
                                                        {rule.custom_message && (
                                                            <div className="text-xs text-gray-500 italic bg-gray-900/50 p-2 rounded border border-gray-800/50">
                                                                "{rule.custom_message}"
                                                            </div>
                                                        )}
                                                    </div>
                                                    <button 
                                                        onClick={() => deleteRule(rule.id)}
                                                        className="text-gray-600 hover:text-red-400 p-2 hover:bg-red-500/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                                                        title="Remover Regra"
                                                    >
                                                        <Trash2 size={16} />
                                                    </button>
                                                </GlassCard>
                                            ))
                                        )}
                                    </div>
                                </div>
                            )}

                            {activeTab === 'settings' && (
                                <div className="space-y-6">
                                    <GradientBanner 
                                        icon={Settings}
                                        title="Configurações da Conta"
                                        description="Gerencie seu acesso e integrações."
                                        variant="blue"
                                    />
                                    
                                    <PushNotificationCard />

                                    <GlassCard variant="blue" className="p-6">
                                        <div className="space-y-4">
                                            <div>
                                                <label className="block text-sm font-medium text-gray-400 mb-2">ID de Usuário (Login)</label>
                                                <div className="flex gap-2">
                                                    <Input 
                                                        value={userId}
                                                        onChange={(e) => setUserId(e.target.value)}
                                                        placeholder="Digite seu ID..."
                                                    />
                                                    <Button 
                                                        onClick={handleSaveUserId}
                                                        className="shadow-lg shadow-emerald-900/10"
                                                    >
                                                        Salvar
                                                    </Button>
                                                </div>
                                                <p className="text-xs text-gray-600 mt-2 ml-1">
                                                    Este ID é usado para identificar sua planilha e sessões.
                                                </p>
                                            </div>

                                            <div className="pt-6 mt-6 border-t border-gray-800">
                                                <Button 
                                                    onClick={() => {
                                                        if(confirm("Deseja sair da conta?")) {
                                                            localStorage.removeItem(STORAGE_KEYS.USER_ID);
                                                            window.location.reload();
                                                        }
                                                    }}
                                                    variant="danger-outline"
                                                    className="w-full h-12"
                                                    icon={LogOut}
                                                >
                                                    Sair da Conta
                                                </Button>
                                            </div>
                                        </div>
                                    </GlassCard>

                                    {driveStatus && driveStatus.is_google_sheet && (
                                        <GlassCard className="p-6">
                                            <div className="flex items-center space-x-3 mb-6">
                                                <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-500">
                                                    <FileSpreadsheet size={24} />
                                                </div>
                                                <div>
                                                     <h3 className="text-lg font-bold text-white">Google Drive</h3>
                                                     <p className="text-xs text-gray-500">Conexão Backend</p>
                                                </div>
                                            </div>
                                            
                                            <div className="bg-gray-900/50 p-4 rounded-xl border border-gray-800 mb-6 text-sm text-gray-300 leading-relaxed">
                                                Para que o Agendador de Tarefas e o Bot do Telegram funcionem quando você não está com o app aberto, é necessário autorizar o acesso backend à planilha.
                                            </div>

                                            <div className="flex items-center justify-between bg-gray-900 p-4 rounded-xl border border-gray-800 mb-6">
                                                <span className="text-sm font-medium text-white">Status</span>
                                                {driveStatus.backend_consent ? (
                                                    <div className="flex items-center space-x-2 text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-lg border border-emerald-500/20">
                                                        <CheckCircle size={16} />
                                                        <span className="text-xs uppercase font-bold">Ativo</span>
                                                    </div>
                                                ) : (
                                                    <div className="flex items-center space-x-2 text-gray-500 bg-gray-800 px-3 py-1 rounded-lg border border-gray-700">
                                                        <XCircle size={16} />
                                                        <span className="text-xs uppercase font-bold">Inativo</span>
                                                    </div>
                                                )}
                                            </div>

                                            {!driveStatus.has_credentials ? (
                                                 <div className="text-sm text-yellow-500 bg-yellow-900/20 p-4 rounded-xl border border-yellow-900/50 mb-4 flex gap-3 items-start">
                                                    <ShieldAlert className="shrink-0 mt-0.5" size={16} />
                                                    <span>Você precisa fazer login com Google para habilitar este recurso.</span>
                                                 </div>
                                            ) : (
                                                driveStatus.backend_consent ? (
                                                    <Button
                                                        onClick={handleDriveRevoke}
                                                        variant="outline"
                                                        className="w-full"
                                                    >
                                                        Revogar Acesso Backend
                                                    </Button>
                                                ) : (
                                                    <Button
                                                        onClick={handleDriveShare}
                                                        variant="primary"
                                                        className="w-full shadow-lg shadow-emerald-900/20"
                                                    >
                                                        Autorizar Acesso Backend
                                                    </Button>
                                                )
                                            )}
                                        </GlassCard>
                                    )}

                                    <div className="bg-red-950/10 border border-red-900/30 rounded-xl p-6">
                                         <h3 className="text-lg font-bold text-red-400 mb-2 flex items-center gap-2">
                                            <HardDrive size={20} />
                                            Zona de Perigo
                                         </h3>
                                         <p className="text-sm text-red-200/50 mb-6">Ações irreversíveis.</p>
                                         
                                         <div className="grid grid-cols-1 gap-3">
                                            <button 
                                                onClick={async () => {
                                                    if(confirm("ATENÇÃO: Isso apagará TODOS os dados e reiniciará o tutorial. Continuar?")) {
                                                        try {
                                                            await fetchAPI('/profile/reset', { 
                                                                method: 'POST',
                                                                body: JSON.stringify({ fast_track: false })
                                                            });
                                                            localStorage.clear();
                                                            window.location.reload();
                                                        } catch (e) {
                                                            alert('Erro ao resetar.');
                                                        }
                                                    }
                                                }}
                                                className="w-full text-red-400 hover:text-red-300 text-sm font-medium border border-red-900/50 p-3 rounded-xl hover:bg-red-900/20 transition-colors text-left flex items-center gap-3"
                                            >
                                                <span className="text-lg">💥</span>
                                                <div className="flex-1">
                                                    <div className="font-bold">Reset Completo</div>
                                                    <div className="text-xs opacity-70">Apaga tudo e reinicia tutorial</div>
                                                </div>
                                            </button>

                                            <button 
                                                onClick={async () => {
                                                    if(confirm("Reiniciar configuração (Fast Track)?")) {
                                                        try {
                                                            await fetchAPI('/profile/reset', { 
                                                                method: 'POST', 
                                                                body: JSON.stringify({ fast_track: true }) 
                                                            });
                                                            localStorage.clear();
                                                            window.location.reload();
                                                        } catch (e) {
                                                            alert('Erro ao resetar.');
                                                        }
                                                    }
                                                }}
                                                className="w-full text-orange-400 hover:text-orange-300 text-sm font-medium border border-orange-900/50 p-3 rounded-xl hover:bg-orange-900/20 transition-colors text-left flex items-center gap-3"
                                            >
                                                <span className="text-lg">🚀</span>
                                                <div className="flex-1">
                                                    <div className="font-bold">Reset Rápido</div>
                                                    <div className="text-xs opacity-70">Reinicia sem tutorial</div>
                                                </div>
                                            </button>
                                         </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
