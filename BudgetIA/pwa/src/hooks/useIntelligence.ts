import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchAPI } from '../services/api';
import { toast } from 'sonner';

export interface ToolInfo {
    name: string;
    description: string;
    label?: string;
    is_essential: boolean;
}

export interface ObserverInfo {
    id: string;
    name: string;
    description: string;
    is_active: boolean;
    config: {
        days_lookback?: number;
        threshold_percent?: number;
        keywords_count?: number;
        keywords_sample?: string[];
    };
}

export interface MemoryFact {
    content: string;
    created_at: string;
    source: string;
    metadata?: Record<string, any>;
}

export interface WatchdogRule {
    id: string;
    category: string;
    threshold: number;
    period: string;
    custom_message?: string;
}

export function useIntelligence() {
    const queryClient = useQueryClient();
    
    const toolsQuery = useQuery({
        queryKey: ['intelligence', 'tools'],
        queryFn: () => fetchAPI('/intelligence/tools') as Promise<ToolInfo[]>,
        staleTime: 1000 * 60 * 60 // 1 hour (tools rarely change)
    });

    const observersQuery = useQuery({
        queryKey: ['intelligence', 'observers'],
        queryFn: () => fetchAPI('/intelligence/observers') as Promise<ObserverInfo[]>,
        staleTime: 1000 * 60 * 5 // 5 minutes
    });

    const memoryQuery = useQuery({
        queryKey: ['memory'],
        queryFn: () => fetchAPI('/profile/memory') as Promise<MemoryFact[]>,
        staleTime: 1000 * 60 * 5
    });

    const rulesQuery = useQuery({
        queryKey: ['rules'],
        queryFn: () => fetchAPI('/profile/rules') as Promise<WatchdogRule[]>,
        staleTime: 1000 * 60 * 5
    });

    const deleteMemoryMutation = useMutation({
        mutationFn: (content: string) => fetchAPI(`/profile/memory/${encodeURIComponent(content)}`, { method: 'DELETE' }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['memory'] });
        },
        onError: () => toast.error('Erro ao esquecer fato.')
    });

    const deleteRuleMutation = useMutation({
        mutationFn: (id: string) => fetchAPI(`/profile/rules/${id}`, { method: 'DELETE' }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['rules'] });
            toast.success("Regra removida.");
        },
        onError: () => toast.error('Erro ao remover regra.')
    });

    const subscriptionKeywordsQuery = useQuery({
        queryKey: ['intelligence', 'subscription-keywords'],
        queryFn: () => fetchAPI('/intelligence/subscription-keywords') as Promise<string[]>,
        staleTime: 1000 * 60 * 5
    });

    const updateSubscriptionKeywordsMutation = useMutation({
        mutationFn: (keywords: string[]) => fetchAPI('/intelligence/subscription-keywords', { 
            method: 'POST', 
            body: JSON.stringify({ keywords }) 
        }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['intelligence', 'subscription-keywords'] });
            queryClient.invalidateQueries({ queryKey: ['intelligence', 'observers'] }); // To update config sample
            toast.success("Lista de assinaturas atualizada.");
        }
    }); 
    
    // We need to return the mutation object itself or its properties
    const cleaningMutation = useMutation({
        mutationFn: () => fetchAPI('/intelligence/clean', { method: 'POST' }),
        onSuccess: (data) => {
            // Invalidate queries to refresh UI immediately
            queryClient.invalidateQueries({ queryKey: ['transactions'] });
            queryClient.invalidateQueries({ queryKey: ['dashboard'] });
            queryClient.invalidateQueries({ queryKey: ['categories'] });

            // Check 'processed' (backend arg) or 'updated_count'
            const count = data.processed !== undefined ? data.processed : data.updated_count;

            if (data.status === 'success' && count > 0) {
                 toast.success(`Faxina concluída! ${count} transações corrigidas.`);
            } else if (data.status === 'success' && count === 0) {
                 toast.info(data.message || "Tudo limpo! Nenhuma transação pendente.");
            } else if (data.status === 'sem_pendencias') {
                 toast.info("Tudo limpo! Nenhuma transação pendente.");
            } else {
                 toast.success("Faxina concluída.");
            }
        },
        onError: () => toast.error('Erro ao executar faxina.')
    });

    return {
        tools: toolsQuery.data || EMPTY_ARRAY,
        observers: observersQuery.data || EMPTY_ARRAY,
        memoryFacts: memoryQuery.data || EMPTY_ARRAY,
        rules: rulesQuery.data || EMPTY_ARRAY,
        subscriptionKeywords: subscriptionKeywordsQuery.data || EMPTY_ARRAY,
        updateSubscriptionKeywords: updateSubscriptionKeywordsMutation.mutateAsync,

        isLoading: toolsQuery.isLoading || observersQuery.isLoading || memoryQuery.isLoading || rulesQuery.isLoading || subscriptionKeywordsQuery.isLoading,
        isToolsError: toolsQuery.isError,
        isObserversError: observersQuery.isError,

        deleteMemory: deleteMemoryMutation.mutateAsync,
        deleteRule: deleteRuleMutation.mutateAsync,
        
        triggerCleaning: cleaningMutation.mutateAsync,
        isCleaning: cleaningMutation.isPending
    };
}

const EMPTY_ARRAY: any[] = [];
