import { useState, useEffect } from 'react';
import { User, Brain, ShieldAlert, Download, Save, Trash2 } from 'lucide-react';
import { fetchAPI } from '../services/api';

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

export default function Profile() {
    const [userId, setUserId] = useState('');
    const [activeTab, setActiveTab] = useState<'profile' | 'memory' | 'rules' | 'settings'>('profile');
    
    // Data States
    const [profileData, setProfileData] = useState<ProfileItem[]>([]);
    const [memoryFacts, setMemoryFacts] = useState<MemoryFact[]>([]);
    const [rules, setRules] = useState<WatchdogRule[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        setUserId(localStorage.getItem('budgetia_user_id') || 'jsmith');
        loadAllData();
    }, []);

    const loadAllData = async () => {
        setLoading(true);
        try {
            const [prof, mem, rul] = await Promise.all([
                fetchAPI('/profile/'),
                fetchAPI('/profile/memory'),
                fetchAPI('/profile/rules')
            ]);
            if (prof) setProfileData(prof);
            if (mem) setMemoryFacts(mem);
            if (rul) setRules(rul);
        } catch (error) {
            console.error("Erro ao carregar dados do perfil", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSaveUserId = () => {
        localStorage.setItem('budgetia_user_id', userId);
        alert('Usuário atualizado! Recarregue a página para aplicar.');
        window.location.reload();
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
            alert('Perfil atualizado com sucesso!');
        } catch (error) {
            alert('Erro ao salvar perfil.');
        }
    };

    const deleteMemory = async (content: string) => {
        if(!confirm("Esquecer este fato?")) return;
        try {
            // Encode content for URL safety
            await fetchAPI(`/profile/memory/${encodeURIComponent(content)}`, { method: 'DELETE' });
            setMemoryFacts(prev => prev.filter(f => f.content !== content));
        } catch (error) {
            alert('Erro ao esquecer fato.');
        }
    };

    const deleteRule = async (id: string) => {
        if(!confirm("Remover esta regra?")) return;
        try {
            await fetchAPI(`/profile/rules/${id}`, { method: 'DELETE' });
            setRules(prev => prev.filter(r => r.id !== id));
        } catch (error) {
            alert('Erro ao remover regra.');
        }
    };

    const handleExport = async () => {
        try {
            // Diretamente abrindo a URL para iniciar download
            // Nota: Se a API exigir auth header, precisaríamos usar fetch + blob
            // Mas nossa API Client fetchAPI injeta headers.
            // Vamos usar uma abordagem de fetch blob para garantir headers
            const response = await fetch('http://localhost:8000/dashboard/export', {
                headers: {
                    'X-User-ID': userId
                }
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
            alert('Erro ao exportar arquivo.');
            console.error(error);
        }
    };

    return (
        <div className="space-y-6">
             <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight text-white">Seu Perfil</h2>
                    <p className="text-gray-400">Gerencie seus dados, memória da IA e regras.</p>
                </div>
                <div className="flex space-x-2">
                    <button 
                        onClick={handleExport}
                        className="flex items-center space-x-2 bg-gray-800 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors border border-gray-700"
                    >
                        <Download size={18} />
                        <span>Backup Excel</span>
                    </button>
                    <button 
                         onClick={saveProfile}
                         className="flex items-center space-x-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg transition-colors"
                    >
                        <Save size={18} />
                        <span>Salvar Tudo</span>
                    </button>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex space-x-1 bg-gray-900/50 p-1 rounded-xl border border-gray-800 w-fit">
                {[
                    { id: 'profile', label: 'Dados Pessoais', icon: User },
                    { id: 'memory', label: 'Memória (IA)', icon: Brain },
                    { id: 'rules', label: 'Regras (Watchdog)', icon: ShieldAlert },
                    { id: 'settings', label: 'Configurações', icon: User }
                ].map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as any)}
                        className={`
                            flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
                            ${activeTab === tab.id 
                                ? 'bg-gray-800 text-white shadow-sm' 
                                : 'text-gray-400 hover:text-white hover:bg-gray-800/50'}
                        `}
                    >
                        <tab.icon size={16} />
                        <span>{tab.label}</span>
                    </button>
                ))}
            </div>

            {/* Content */}
            <div className="min-h-[400px]">
                {loading ? (
                    <p className="text-gray-400">Carregando dados...</p>
                ) : (
                    <>
                        {/* PROFILE EDITOR */}
                        {activeTab === 'profile' && (
                            <div className="bg-gray-900/50 border border-gray-800 rounded-xl overflow-hidden">
                                <table className="w-full text-left">
                                    <thead className="bg-gray-900 text-gray-400 text-xs uppercase font-medium">
                                        <tr>
                                            <th className="px-6 py-4">Campo</th>
                                            <th className="px-6 py-4">Valor</th>
                                            <th className="px-6 py-4">Observações</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-800">
                                        {profileData.map((item, idx) => (
                                            <tr key={idx} className="hover:bg-gray-800/30 transition-colors">
                                                <td className="px-6 py-4 text-sm font-medium text-white">
                                                    {item.Campo}
                                                </td>
                                                <td className="px-6 py-4">
                                                    <input 
                                                        type="text" 
                                                        value={item.Valor}
                                                        onChange={(e) => handleProfileEdit(idx, 'Valor', e.target.value)}
                                                        className="bg-transparent border-b border-gray-700 focus:border-emerald-500 w-full text-white px-1 py-0.5 focus:outline-none transition-colors"
                                                    />
                                                </td>
                                                <td className="px-6 py-4">
                                                     <input 
                                                        type="text" 
                                                        value={item.Observações || ''}
                                                        onChange={(e) => handleProfileEdit(idx, 'Observações', e.target.value)}
                                                        className="bg-transparent border-b border-gray-700 focus:border-emerald-500 w-full text-gray-400 px-1 py-0.5 focus:outline-none transition-colors"
                                                    />
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                                {profileData.length === 0 && (
                                     <div className="p-8 text-center text-gray-500">Nenhum dado de perfil encontrado.</div>
                                )}
                            </div>
                        )}

                        {/* MEMORY VIEWER */}
                        {activeTab === 'memory' && (
                            <div className="grid gap-4 md:grid-cols-2">
                                {memoryFacts.length === 0 ? (
                                    <p className="text-gray-400 col-span-2">O cérebro da IA está vazio.</p>
                                ) : (
                                    memoryFacts.map((fact, idx) => (
                                        <div key={idx} className="bg-gray-900/50 border border-gray-800 rounded-xl p-4 flex justify-between items-start group hover:border-violet-500/50 transition-all">
                                            <div>
                                                <p className="text-white font-medium">{fact.content}</p>
                                                <p className="text-xs text-gray-500 mt-2">
                                                    Aprendido em: {fact.created_at} • Via: {fact.source}
                                                </p>
                                            </div>
                                            <button 
                                                onClick={() => deleteMemory(fact.content)}
                                                className="text-gray-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity p-2"
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </div>
                                    ))
                                )}
                            </div>
                        )}

                         {/* RULES VIEWER */}
                         {activeTab === 'rules' && (
                            <div className="grid gap-4 md:grid-cols-2">
                                {rules.length === 0 ? (
                                    <p className="text-gray-400 col-span-2">Nenhuma regra de monitoramento ativa.</p>
                                ) : (
                                    rules.map((rule) => (
                                        <div key={rule.id} className="bg-gray-900/50 border border-gray-800 rounded-xl p-4 flex justify-between items-start group hover:border-orange-500/50 transition-all">
                                            <div>
                                                <div className="flex items-center space-x-2 mb-1">
                                                    <span className="text-orange-400 font-bold">{rule.category}</span>
                                                    <span className="text-gray-600 text-xs bg-gray-900 px-2 py-0.5 rounded-full border border-gray-800">
                                                        {rule.period === 'monthly' ? 'Mensal' : 'Semanal'}
                                                    </span>
                                                </div>
                                                <p className="text-white">Limite: R$ {rule.threshold}</p>
                                                <p className="text-xs text-gray-500 mt-2 italic">"{rule.custom_message}"</p>
                                            </div>
                                            <button 
                                                onClick={() => deleteRule(rule.id)}
                                                className="text-gray-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity p-2"
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </div>
                                    ))
                                )}
                            </div>
                        )}

                        {/* SETTINGS */}
                        {activeTab === 'settings' && (
                            <div className="space-y-6 max-w-md">
                                <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
                                    <h3 className="text-lg font-medium text-white mb-4">Conexão Local API</h3>
                                    <div className="space-y-4">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-400 mb-1">User ID (API)</label>
                                            <input 
                                                type="text" 
                                                value={userId}
                                                onChange={(e) => setUserId(e.target.value)}
                                                className="w-full bg-gray-950 border border-gray-700 text-white rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500 transition-colors"
                                            />
                                            <p className="text-xs text-gray-600 mt-1">Padrão: jsmith (Demo)</p>
                                        </div>
                                        <button 
                                            onClick={handleSaveUserId}
                                            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                                        >
                                            Salvar Conexão
                                        </button>
                                    </div>
                                </div>

                                <div className="bg-red-900/10 border border-red-900/30 rounded-xl p-6">
                                     <h3 className="text-lg font-medium text-red-400 mb-2">Zona de Perigo</h3>
                                     <p className="text-sm text-gray-500 mb-4">Ações destrutivas que não podem ser desfeitas.</p>
                                     <button 
                                        onClick={async () => {
                                            if(confirm("ATENÇÃO: Isso apagará TODOS os dados da sua conta (configurações, onboarding). Continuar?")) {
                                                try {
                                                    await fetchAPI('/profile/reset', { method: 'POST' });
                                                    localStorage.clear();
                                                    alert('Conta resetada com sucesso.');
                                                    window.location.reload();
                                                } catch (e) {
                                                    alert('Erro ao resetar conta.');
                                                }
                                            }
                                        }}
                                        className="text-red-400 hover:text-red-300 text-sm font-medium hover:underline block w-full text-left"
                                     >
                                        Resetar Conta Completamente (Zona de Perigo)
                                     </button>
                                     
                                     <button 
                                        onClick={() => {
                                            if(confirm("Isso apagará apenas o cache do navegador. Continuar?")) {
                                                localStorage.clear();
                                                window.location.reload();
                                            }
                                        }}
                                        className="text-gray-500 hover:text-white text-xs mt-4 hover:underline block w-full text-left"
                                     >
                                        Limpar apenas Cache Local
                                     </button>
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
