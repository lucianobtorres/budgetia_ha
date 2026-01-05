import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Button } from '../ui/Button';
import { Loader2, ExternalLink, CreditCard, Clock } from 'lucide-react';
import { toast } from 'sonner';
import { AuthService } from '../../services/auth';
import { GradientBanner } from '../ui/GradientBanner';
import { SubscriptionService, type UserSubscription } from '../../services/subscription';
import { PlanCard } from '../subscription/PlanCard';

import { PLANS } from '../../config/plans';

export function SubscriptionTab() {
    const [status, setStatus] = useState<UserSubscription | null>(null);
    const [loading, setLoading] = useState(true);
    const [processingPlan, setProcessingPlan] = useState<string | null>(null);

    useEffect(() => {
        loadStatus();
    }, []);

    const loadStatus = async () => {
        try {
            const data = await SubscriptionService.getStatus();
            setStatus(data);
        } catch (error) {
            console.error(error);
            toast.error("Erro ao carregar assinatura");
        } finally {
            setLoading(false);
        }
    };

    const handleSubscribe = async (planId: string) => {
        try {
            setProcessingPlan(planId);
            const url = await SubscriptionService.getCheckoutUrl(planId);
            
            if (url.includes('mock')) {
                 toast.success(`Redirecionando para Checkout...`);
                 setTimeout(() => {
                     window.open(url, '_blank');
                     setProcessingPlan(null);
                 }, 1500);
            } else {
                window.location.href = url;
            }
        } catch (error) {
            toast.error("Erro ao iniciar checkout");
            setProcessingPlan(null);
        }
    };

    const handleManage = async () => {
        try {
            const url = await SubscriptionService.getPortalUrl();
            window.location.href = url;
        } catch (error) {
            toast.error("Erro ao abrir portal");
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center p-12">
                <Loader2 className="w-6 h-6 animate-spin text-primary" />
            </div>
        );
    }

    const currentPlanId = status?.plan_tier || 'free';
    const isSelfHosted = AuthService.getDeployMode() === 'SELF_HOSTED';

    if (isSelfHosted) {
         return (
             <div className="text-center p-8 bg-surface-card rounded-xl border border-border">
                 <h3 className="font-bold text-lg mb-2">Modo Self-Hosted</h3>
                 <p className="text-sm text-text-secondary">Todos os recursos liberados.</p>
             </div>
         );
    }

    const isLifetime = status?.plan_tier === 'lifetime';
    const planName = isLifetime ? 'Acesso Vitalício' : (status?.plan_tier === 'pro' ? 'BudgetIA Pro' : 'Gratuito');

    return (
        <div className="space-y-6">
            <GradientBanner 
                icon={CreditCard}
                title="Minha Assinatura"
                description={isLifetime ? "Você tem acesso irrestrito ao sistema." : "Gerencie seu plano e recursos."}
                variant={isLifetime ? "emerald" : "violet"}
            >
               <div className="flex flex-col items-end gap-2">
                   <div className="flex items-center gap-3 bg-black/20 p-2 rounded-lg border border-white/10 backdrop-blur-sm shadow-sm">
                       <span className="text-lg font-bold text-white">
                           {planName}
                       </span>
                       <span className={`text-[10px] px-2.5 py-0.5 rounded-full border font-medium tracking-wide uppercase ${
                           status?.status === 'active' ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' : 
                           status?.status === 'trialing' ? 'bg-pink-500/20 text-pink-300 border-pink-500/30' :
                           'bg-yellow-500/20 text-yellow-300 border-yellow-500/30'
                       }`}>
                           {status?.status === 'trialing' ? 'TRIAL' : (status?.status || 'ATIVO')}
                       </span>
                   </div>

                   {/* Always show trial info if present */}
                   {(status?.trial_end || status?.current_period_end) && (
                       <div className="text-right">
                           <p className="text-[10px] text-text-secondary uppercase tracking-wider font-semibold mb-0.5">
                               {status?.status === 'trialing' ? 'Testes até' : 'Renovação'}
                           </p>
                           <p className="text-sm font-mono text-white flex items-center justify-end gap-2">
                               <Clock className="w-3 h-3 text-primary" />
                                {new Date(status.trial_end || status.current_period_end).toLocaleDateString()}
                            </p>
                        </div>
                    )}
                </div>
            </GradientBanner>

             {/* Manage Button only for non-lifetime/expired */} 
             {!isLifetime && status?.status !== 'expired' && status?.plan_tier !== 'free' && (
                <div className="flex justify-end -mt-4 mb-4">
                     <Button onClick={handleManage} variant="outline" size="sm" className="gap-2">
                         Gerenciar Assinatura
                        <ExternalLink className="w-3 h-3" />
                     </Button>
                </div>
            )}

            {/* Plan Cards - Hide if Lifetime */}
            {!isLifetime && (
                <div>
                    <h4 className="text-sm font-medium text-text-secondary mb-4 uppercase tracking-wider">Planos Disponíveis</h4>
                    <div className="grid md:grid-cols-2 gap-4">
                        {PLANS.map((plan) => (
                            <PlanCard
                                key={plan.id}
                                {...plan}
                                isCurrent={currentPlanId === plan.id}
                                isLoading={processingPlan === plan.id}
                                onSelect={() => handleSubscribe(plan.id)}
                            />
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
