import { useState, useEffect } from 'react';
import { fetchAPI } from '../services/api';
import { MessageCircle, Phone, Mail, MessageSquare } from 'lucide-react';
import { cn } from '../utils/cn';
import { PageHeader } from '../components/ui/PageHeader';
import { SegmentedControl } from '../components/ui/SegmentedControl';
import { Button } from '../components/ui/Button';
import { GlassCard } from '../components/ui/GlassCard';
import { Input } from '../components/ui/Input';
import { GradientBanner } from '../components/ui/GradientBanner';

interface ComConfig {
    telegram_chat_id?: string;
    whatsapp_phone?: string;
    email_address?: string;
    sms_phone?: string;
    [key: string]: string | undefined;
}

export default function Connections() {
    const [activeTab, setActiveTab] = useState<'telegram' | 'whatsapp' | 'email' | 'sms'>('telegram');
    const [config, setConfig] = useState<ComConfig>({});
    const [formState, setFormState] = useState<ComConfig>({});
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const data = await fetchAPI('/profile/settings/communication');
            if (data) {
                setConfig(data);
                setFormState(data);
            }
        } catch (error) {
            console.error("Failed to load settings", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async (field: string, value: string) => {
        try {
            await fetchAPI('/profile/settings/communication', {
                method: 'POST',
                body: JSON.stringify({ [field]: value })
            });
            setConfig(prev => ({ ...prev, [field]: value }));
            alert('Configuração salva com sucesso!');
        } catch (error) {
            console.error("Failed to save", error);
            alert('Erro ao salvar.');
        }
    };

    const tabs = [
        { id: 'telegram', label: 'Telegram', icon: MessageCircle, color: 'text-blue-400' },
        { id: 'whatsapp', label: 'WhatsApp', icon: Phone, color: 'text-green-400' },
        { id: 'email', label: 'E-mail', icon: Mail, color: 'text-yellow-400' },
        { id: 'sms', label: 'SMS', icon: MessageSquare, color: 'text-purple-400' }
    ] as const;



    return (
        <div className="h-full flex flex-col gap-6 overflow-hidden">
            {/* Fixed Header */}
            <div className="flex-none pt-safe space-y-4">
                <PageHeader 
                    title="Conexões" 
                    description="Configure os canais de integração com a IA." 
                    className="pt-0 !space-y-0"
                />

                {/* Tabs - Segmented Control Style */}
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
                        <div className="max-w-2xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
                            {/* Render Active Tab Content */}
                            {activeTab === 'telegram' && (
                                <>
                                    <GradientBanner 
                                        icon={MessageCircle}
                                        title="Telegram"
                                        description="Canal oficial recomendado. Envie áudios, textos e imagens."
                                        variant="blue"
                                    />

                                    <GlassCard className="space-y-6 p-6">
                                        <div className="bg-surface-hover/50 rounded-xl p-5 border border-border/50 text-sm space-y-3">
                                            <p className="text-text-primary font-medium">Como conectar em 3 passos:</p>
                                            <ol className="list-decimal list-inside text-text-secondary space-y-2 ml-1">
                                                <li>Abra o <a href="https://t.me/BudgetIABot" target="_blank" className="text-blue-400 hover:text-blue-300 hover:underline font-medium">@BudgetIABot</a> no Telegram.</li>
                                                <li>Envie o comando <strong>/start</strong>.</li>
                                                <li>Copie o número (Chat ID) que o bot responder e cole abaixo.</li>
                                            </ol>
                                        </div>

                                        <div className="space-y-4">
                                            <label className="text-sm font-medium text-text-primary">Seu Chat ID</label>
                                            <div className="flex gap-3">
                                                <Input 
                                                    value={formState.telegram_chat_id || ''}
                                                    onChange={(e) => setFormState(prev => ({...prev, telegram_chat_id: e.target.value}))}
                                                    placeholder="Ex: 123456789"
                                                    className="font-mono h-11"
                                                />
                                                <Button 
                                                    onClick={() => handleSave('telegram_chat_id', formState.telegram_chat_id || '')}
                                                    variant="primary"
                                                    className="shrink-0 h-11 px-6"
                                                >
                                                    Salvar
                                                </Button>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                 <div className={cn("w-2 h-2 rounded-full", config.telegram_chat_id ? "bg-emerald-500" : "bg-red-500")} />
                                                 <p className="text-xs text-text-muted">
                                                    Status: <span className={config.telegram_chat_id ? "text-emerald-400" : "text-red-400"}>{config.telegram_chat_id ? 'Conectado' : 'Desconectado'}</span>
                                                </p>
                                            </div>
                                        </div>
                                    </GlassCard>
                                </>
                            )}

                             {activeTab === 'whatsapp' && (
                                <>
                                    <GradientBanner 
                                        icon={Phone}
                                        title="WhatsApp (Beta)"
                                        description="Integração via Twilio Sandbox."
                                        variant="green"
                                    />
                                    <GlassCard className="space-y-6 p-6">
                                        <label className="text-sm font-medium text-text-primary block">Número (com DDD)</label>
                                        <div className="flex gap-3">
                                            <Input 
                                                value={formState.whatsapp_phone || ''}
                                                onChange={(e) => setFormState(prev => ({...prev, whatsapp_phone: e.target.value}))}
                                                placeholder="+55 11 99999-9999"
                                                className="font-mono h-11"
                                            />
                                            <Button 
                                                onClick={() => handleSave('whatsapp_phone', formState.whatsapp_phone || '')}
                                                variant="primary"
                                                className="shrink-0 h-11 px-6"
                                            >
                                                Salvar
                                            </Button>
                                        </div>
                                    </GlassCard>
                                </>
                             )}

                             {activeTab === 'email' && (
                                <>
                                    <GradientBanner 
                                        icon={Mail}
                                        title="E-mail"
                                        description="Relatórios mensais e alertas de segurança."
                                        variant="yellow"
                                    />
                                    <GlassCard className="space-y-6 p-6">
                                        <label className="text-sm font-medium text-text-primary block">Endereço de E-mail</label>
                                        <div className="flex gap-3">
                                            <Input 
                                                type="email"
                                                value={formState.email_address || ''}
                                                onChange={(e) => setFormState(prev => ({...prev, email_address: e.target.value}))}
                                                placeholder="seu@email.com"
                                                className="h-11"
                                            />
                                            <Button 
                                                onClick={() => handleSave('email_address', formState.email_address || '')}
                                                variant="primary"
                                                className="shrink-0 h-11 px-6"
                                            >
                                                Salvar
                                            </Button>
                                        </div>
                                    </GlassCard>
                                </>
                             )}

                             {activeTab === 'sms' && (
                                <>
                                    <GradientBanner 
                                        icon={MessageSquare}
                                        title="SMS"
                                        description="Alertas Críticos e autenticação."
                                        variant="violet"
                                    />
                                    <GlassCard className="space-y-6 p-6">
                                        <label className="text-sm font-medium text-text-primary block">Número Celular</label>
                                        <div className="flex gap-3">
                                            <Input 
                                                value={formState.sms_phone || ''}
                                                onChange={(e) => setFormState(prev => ({...prev, sms_phone: e.target.value}))}
                                                placeholder="+55 11..."
                                                className="font-mono h-11"
                                            />
                                            <Button 
                                                onClick={() => handleSave('sms_phone', formState.sms_phone || '')}
                                                variant="primary"
                                                className="shrink-0 h-11 px-6"
                                            >
                                                Salvar
                                            </Button>
                                        </div>
                                    </GlassCard>
                                </>
                             )}
                        </div>
                    )}
                 </div>
            </div>
        </div>
    );
}
