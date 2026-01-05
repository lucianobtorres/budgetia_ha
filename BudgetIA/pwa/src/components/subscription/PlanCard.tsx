import { Check, Loader2, Zap } from 'lucide-react';
import { Button } from '../ui/Button';
import { GlassCard } from '../ui/GlassCard';
import { cn } from '../../utils/cn';

interface PlanFeature {
    name: string;
    included: boolean;
}

interface PlanCardProps {
    id: string;
    name: string;
    price: string;
    description: string;
    features: PlanFeature[];
    isCurrent: boolean;
    isLoading?: boolean;
    onSelect: () => void;
    variant?: 'default' | 'highlight';
}

export function PlanCard({
    name,
    price,
    description,
    features,
    isCurrent,
    isLoading,
    onSelect,
    variant = 'default'
}: PlanCardProps) {
    const isHighlight = variant === 'highlight';

    return (
        <GlassCard 
            className={cn(
                "relative p-6 flex flex-col h-full transition-all duration-300",
                isHighlight ? "border-emerald-500/30 bg-emerald-900/10" : "border-white/5",
                isCurrent && "ring-2 ring-emerald-500 ring-offset-2 ring-offset-gray-950"
            )}
        >
            {isHighlight && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full text-[10px] font-bold text-white uppercase tracking-wider shadow-lg">
                    Recomendado
                </div>
            )}

            <div className="mb-6">
                <h3 className={cn("text-lg font-bold flex items-center gap-2", isHighlight ? "text-emerald-400" : "text-white")}>
                    {isHighlight && <Zap className="w-4 h-4 fill-current" />}
                    {name}
                </h3>
                <div className="mt-2 flex items-baseline gap-1">
                    <span className="text-3xl font-bold text-white">{price}</span>
                    <span className="text-sm text-gray-400">/mês</span>
                </div>
                <p className="mt-2 text-sm text-gray-400">{description}</p>
            </div>

            <div className="flex-1 space-y-3 mb-6">
                {features.map((feature, idx) => (
                    <div key={idx} className="flex items-start gap-3 text-sm">
                        <div className={cn(
                            "mt-0.5 p-0.5 rounded-full shrink-0",
                            feature.included 
                                ? (isHighlight ? "bg-emerald-500/20 text-emerald-400" : "bg-white/10 text-white")
                                : "bg-transparent text-gray-600"
                        )}>
                            <Check className={cn("w-3 h-3", !feature.included && "opacity-0")} />
                        </div>
                        <span className={cn(
                            feature.included ? "text-gray-300" : "text-gray-600 line-through"
                        )}>
                            {feature.name}
                        </span>
                    </div>
                ))}
            </div>

            <Button
                onClick={onSelect}
                disabled={isCurrent || isLoading}
                variant={isCurrent ? 'outline' : isHighlight ? 'primary' : 'secondary'}
                className="w-full"
            >
                {isLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                ) : isCurrent ? (
                    "Plano Atual"
                ) : (
                    "Escolher Plano"
                )}
            </Button>
        </GlassCard>
    );
}
