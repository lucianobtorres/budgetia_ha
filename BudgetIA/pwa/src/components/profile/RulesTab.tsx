import { ShieldAlert, Trash2 } from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { GradientBanner } from '../ui/GradientBanner';
import type { WatchdogRule } from '../../hooks/useProfile';

interface Props {
    rules: WatchdogRule[];
    onDelete: (id: string) => void;
}

export function RulesTab({ rules, onDelete }: Props) {
    
    const handleDelete = (id: string) => {
        if(confirm("Remover esta regra?")) {
            onDelete(id);
        }
    };

    return (
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
                                onClick={() => handleDelete(rule.id)}
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
    );
}
