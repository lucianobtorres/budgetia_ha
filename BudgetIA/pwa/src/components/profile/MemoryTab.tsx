import { Brain, Trash2, Repeat } from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { GradientBanner } from '../ui/GradientBanner';
import type { MemoryFact } from '../../hooks/useIntelligence';

interface Props {
    facts: MemoryFact[];
    onDelete: (content: string) => void;
}

export function MemoryTab({ facts, onDelete }: Props) {
    
    const handleDelete = (content: string) => {
        if(confirm("Esquecer este fato?")) {
            onDelete(content);
        }
    };

    return (
        <div className="space-y-6">
            <GradientBanner 
                icon={Brain}
                title="Memória da IA"
                description="Fatos aprendidos sobre você durante as conversas."
                variant="violet"
            />

            <div className="grid gap-4 md:grid-cols-2">
                {facts.length === 0 ? (
                    <div className="col-span-2 text-center py-10 bg-surface-card/30 rounded-xl border border-border border-dashed">
                        <Brain size={48} className="mx-auto text-text-muted mb-2" />
                        <p className="text-text-muted">O cérebro da IA está vazio.</p>
                    </div>
                ) : (
                    facts.map((fact, idx) => {
                        const isPattern = fact.metadata?.pattern_type === 'weekly' || fact.metadata?.pattern_type === 'monthly';
                        
                        return (
                            <GlassCard 
                                key={idx} 
                                variant="violet" 
                                className="p-5 flex justify-between items-start group"
                            >
                                <div className="flex-1 pr-4">
                                    <div className="flex items-start gap-2 mb-2">
                                        <p className="text-text-primary font-medium text-sm leading-relaxed">{fact.content}</p>
                                        
                                        {/* Pattern Badge */}
                                        {isPattern && (
                                            <span className="shrink-0 flex items-center gap-1 px-1.5 py-0.5 bg-violet-500/20 text-violet-300 text-[10px] rounded border border-violet-500/20 font-semibold" title="Hábito Recorrente Detectado">
                                                <Repeat className="w-3 h-3" />
                                                <span>{fact.metadata?.pattern_type === 'weekly' ? 'Semanal' : 'Mensal'}</span>
                                            </span>
                                        )}
                                    </div>
                                    
                                    <div className="flex items-center gap-2 text-[10px] text-text-muted uppercase tracking-wider font-semibold">
                                        <span className={fact.source === 'behavior_analyst' ? 'text-violet-400' : ''}>
                                            {fact.source === 'behavior_analyst' ? '🤖 Observador' : fact.source}
                                        </span>
                                        <span className="w-1 h-1 rounded-full bg-text-muted"></span>
                                        <span>{new Date(fact.created_at).toLocaleDateString()}</span>
                                    </div>
                                    
                                    {/* Debug Metadata (Optional: remove later) */}
                                    {fact.metadata?.expected_day_of_week && (
                                         <p className="mt-1 text-[10px] text-gray-500">
                                            Previsto: {fact.metadata.expected_day_of_week} (~R${fact.metadata.avg_amount})
                                         </p>
                                    )}
                                </div>
                                <button 
                                    onClick={() => handleDelete(fact.content)}
                                    className="text-text-secondary hover:text-danger p-2 hover:bg-danger/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                                    title="Esquecer"
                                >
                                    <Trash2 size={16} />
                                </button>
                            </GlassCard>
                        );
                    })
                )}
            </div>
        </div>
    );
}
