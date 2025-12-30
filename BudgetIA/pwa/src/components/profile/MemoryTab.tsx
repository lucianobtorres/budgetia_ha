import { Brain, Trash2 } from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { GradientBanner } from '../ui/GradientBanner';
import type { MemoryFact } from '../../hooks/useProfile';

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
                    facts.map((fact, idx) => (
                        <GlassCard 
                            key={idx} 
                            variant="violet" 
                            className="p-5 flex justify-between items-start group"
                        >
                            <div className="flex-1 pr-4">
                                <p className="text-text-primary font-medium text-sm leading-relaxed mb-2">{fact.content}</p>
                                <div className="flex items-center gap-2 text-[10px] text-text-muted uppercase tracking-wider font-semibold">
                                    <span>{fact.source}</span>
                                    <span className="w-1 h-1 rounded-full bg-text-muted"></span>
                                    <span>{fact.created_at}</span>
                                </div>
                            </div>
                            <button 
                                onClick={() => handleDelete(fact.content)}
                                className="text-text-secondary hover:text-danger p-2 hover:bg-danger/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                                title="Esquecer"
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
