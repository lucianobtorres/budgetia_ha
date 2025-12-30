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
                    <div className="col-span-2 text-center py-10 bg-surface-card/30 rounded-xl border border-border border-dashed">
                        <ShieldAlert size={48} className="mx-auto text-text-muted mb-2" />
                        <p className="text-text-muted">Nenhuma regra ativa.</p>
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
                                    <span className="text-text-muted text-[10px] uppercase font-bold bg-surface-card px-2 py-1 rounded border border-border">
                                        {rule.period === 'monthly' ? 'Mensal' : 'Semanal'}
                                    </span>
                                </div>
                                <p className="text-text-muted text-sm mb-2">Limite: <span className="text-text-primary font-mono font-bold text-lg">R$ {rule.threshold}</span></p>
                                {rule.custom_message && (
                                    <div className="text-xs text-text-muted italic bg-surface-hover/50 p-2 rounded border border-border/50">
                                        "{rule.custom_message}"
                                    </div>
                                )}
                            </div>
                            <button 
                                onClick={() => handleDelete(rule.id)}
                                className="text-text-secondary hover:text-danger p-2 hover:bg-danger/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
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
