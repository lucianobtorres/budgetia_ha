import { useState } from 'react';
import { Brain, Eye, Wrench, ShieldAlert, Settings } from 'lucide-react';
import { PageHeader } from '../components/ui/PageHeader';
import { SegmentedControl } from '../components/ui/SegmentedControl';
import { GradientBanner } from '../components/ui/GradientBanner';
import { GlassCard } from '../components/ui/GlassCard';
import { useIntelligence } from '../hooks/useIntelligence';
import { SubscriptionSettingsDrawer } from '../components/intelligence/SubscriptionSettingsDrawer';
import { MemoryTab } from '../components/profile/MemoryTab';
import { RulesTab } from '../components/profile/RulesTab';

export default function Intelligence() {
    const [activeTab, setActiveTab] = useState<'observers' | 'rules' | 'memory' | 'tools'>('observers');
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    
    // Everything now comes from a single hook
    const { 
        tools, 
        observers, 
        memoryFacts, 
        rules: userRules, 
        deleteMemory, 
        deleteRule, 
        triggerCleaning,
        isLoading 
    } = useIntelligence();

    const tabs = [
        { id: 'observers', label: 'Observadores', icon: Eye, color: 'text-blue-400' },
        { id: 'rules', label: 'Regras', icon: ShieldAlert, color: 'text-orange-400' },
        { id: 'memory', label: 'Memória', icon: Brain, color: 'text-violet-400' },
        { id: 'tools', label: 'Ferramentas', icon: Wrench, color: 'text-emerald-400' },
    ] as const;

    return (
        <div className="h-full flex flex-col gap-6 overflow-hidden">
            <SubscriptionSettingsDrawer 
                isOpen={isSettingsOpen} 
                onClose={() => setIsSettingsOpen(false)} 
            />

            <div className="flex-none pt-safe space-y-4">
                <PageHeader 
                    title="Cérebro da IA" 
                    description="Visualize e gerencie a inteligência do seu assistente."
                    className="pt-0 !space-y-0"
                />
                
                <SegmentedControl 
                    options={tabs.map(t => ({ id: t.id, label: t.label, icon: t.icon, activeColor: t.color }))}
                    value={activeTab}
                    onChange={(val) => setActiveTab(val as any)}
                />
            </div>

            <div 
                className="flex-1 overflow-y-auto pb-20 scrollbar-thin scrollbar-thumb-gray-800 scrollbar-gutter-stable"
            >
                <div className="bg-gray-900/30 border border-gray-800/50 rounded-2xl p-6 min-h-[300px]">
                    {isLoading ? (
                        <div className="flex items-center justify-center h-40 text-gray-400 gap-2">
                            <span className="w-1 h-1 bg-gray-400 rounded-full animate-bounce"></span>
                            <span className="w-1 h-1 bg-gray-400 rounded-full animate-bounce delay-100"></span>
                            <span className="w-1 h-1 bg-gray-400 rounded-full animate-bounce delay-200"></span>
                        </div>
                    ) : (
                        <div className="max-w-2xl mx-auto animate-in fade-in slide-in-from-bottom-2 duration-300">
                            
                            {/* TAB: OBSERVADORES */}
                            {activeTab === 'observers' && (
                                <div className="space-y-6">
                                    <GradientBanner 
                                        icon={Eye}
                                        title="Observadores Ativos"
                                        description="Processos que rodam em segundo plano periodicamente, analisando suas finanças em busca de anomalias."
                                        variant="blue"
                                    />

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {observers.map((obs) => (
                                            <div key={obs.id} className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-5 hover:border-blue-500/30 transition-colors group">
                                                <div className="flex justify-between items-start mb-3">
                                                    <div className="p-2 bg-blue-500/20 rounded-lg group-hover:bg-blue-500/30 transition-colors">
                                                        <Eye className="w-5 h-5 text-blue-400" />
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        {obs.id === 'subscription_auditor' && (
                                                            <button 
                                                                onClick={() => setIsSettingsOpen(true)}
                                                                className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
                                                                title="Configurar"
                                                            >
                                                                <Settings className="w-4 h-4" />
                                                            </button>
                                                        )}
                                                        <span className={`px-2 py-1 rounded text-xs font-medium ${obs.is_active ? 'bg-emerald-500/20 text-emerald-400' : 'bg-gray-700 text-gray-400'}`}>
                                                            {obs.is_active ? 'ATIVO' : 'INATIVO'}
                                                        </span>
                                                    </div>
                                                </div>
                                                <h3 className="font-semibold text-lg text-white mb-1">
                                                    {obs.name}
                                                </h3>
                                                <p className="text-sm text-gray-400 mb-4 h-10 line-clamp-2">{obs.description}</p>
                                                
                                                {/* Config Summary Badge */}
                                                <div className="flex flex-wrap gap-2">
                                                    {obs.config.keywords_count !== undefined && (
                                                        <span className="text-xs bg-gray-700/50 text-gray-300 px-2 py-1 rounded border border-gray-600">
                                                            Monitora {obs.config.keywords_count} itens
                                                        </span>
                                                    )}
                                                    {obs.config.days_lookback !== undefined && (
                                                        <span className="text-xs bg-gray-700/50 text-gray-300 px-2 py-1 rounded border border-gray-600">
                                                            Análise: {obs.config.days_lookback} dias
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                             {/* TAB: REGRAS (Reused from Profile) */}
                            {activeTab === 'rules' && (
                                <RulesTab rules={userRules} onDelete={deleteRule} />
                            )}

                            {/* TAB: MEMÓRIA (Reused from Profile) */}
                            {activeTab === 'memory' && (
                                <MemoryTab facts={memoryFacts} onDelete={deleteMemory} />
                            )}

                            {/* TAB: FERRAMENTAS */}
                            {activeTab === 'tools' && (
                                <div className="space-y-4">
                                    <GradientBanner 
                                        icon={Wrench}
                                        title="Ferramentas Disponíveis"
                                        description="Capacidades que a IA pode utilizar para te ajudar."
                                        variant="emerald"
                                    />
                                    
                                    <div className="grid grid-cols-1 gap-4">
                                        {/* FAXINEIRO AUTÔNOMO (New) */}
                                        <GlassCard 
                                            variant="pink"
                                            className="p-5 flex items-center gap-4 group cursor-pointer hover:bg-pink-500/5 transition-colors"
                                            onClick={() => triggerCleaning()}
                                        >
                                            <div className="flex-none p-3 bg-pink-500/10 rounded-xl group-hover:bg-pink-500/20 transition-colors">
                                                <i className="lucide-sparkles w-6 h-6 text-pink-400" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <h4 className="font-semibold text-lg text-white">
                                                        Faxineiro Autônomo
                                                    </h4>
                                                    <span className="px-2 py-0.5 bg-pink-500/10 border border-pink-500/20 text-pink-400 text-[10px] rounded uppercase tracking-wider font-semibold">
                                                        NOVO
                                                    </span>
                                                </div>
                                                <p className="text-sm text-gray-400">
                                                    Varre transações mal categorizadas ("Outros") e corrige automaticamente usando IA.
                                                </p>
                                            </div>
                                            <div className="flex-none">
                                                <button className="px-4 py-2 bg-pink-500 hover:bg-pink-600 text-white text-sm font-medium rounded-lg transition-colors shadow-lg shadow-pink-500/20">
                                                    Executar Agora
                                                </button>
                                            </div>
                                        </GlassCard>

                                        {tools.map((tool) => (
                                            <GlassCard 
                                                key={tool.name} 
                                                variant="emerald"
                                                className="p-5 flex items-center gap-4 group"
                                            >
                                                <div className="flex-none p-2 bg-emerald-500/10 rounded-lg group-hover:bg-emerald-500/20 transition-colors">
                                                    <Wrench className="w-5 h-5 text-emerald-400" />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <h4 className="font-medium text-text-primary truncate">
                                                            {tool.label || tool.name}
                                                        </h4>
                                                        {tool.is_essential && (
                                                            <span className="px-1.5 py-0.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] rounded uppercase tracking-wider font-semibold">
                                                                Essencial
                                                            </span>
                                                        )}
                                                    </div>
                                                    <p className="text-sm text-text-muted">{tool.description}</p>
                                                </div>
                                            </GlassCard>
                                        ))}
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
