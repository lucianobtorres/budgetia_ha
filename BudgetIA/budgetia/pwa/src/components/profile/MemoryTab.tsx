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
                    <div className="col-span-2 text-center py-10 bg-gray-900/30 rounded-xl border border-gray-800 border-dashed">
                        <Brain size={48} className="mx-auto text-gray-700 mb-2" />
                        <p className="text-gray-500">O cérebro da IA está vazio.</p>
                    </div>
                ) : (
                    facts.map((fact, idx) => (
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
                                onClick={() => handleDelete(fact.content)}
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
    );
}
