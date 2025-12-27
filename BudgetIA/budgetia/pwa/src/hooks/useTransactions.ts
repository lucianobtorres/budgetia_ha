import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchAPI } from '../services/api';
import { toast } from 'sonner';

export interface Transaction {
    "ID Transacao": number;
    "Data": string; // YYYY-MM-DD
    "Tipo (Receita/Despesa)": "Receita" | "Despesa";
    "Categoria": string;
    "Descricao": string;
    "Valor": number;
    "Status": string;
    [key: string]: any;
}

interface TransactionFilters {
    month?: number;
    year?: number;
    limit?: number;
}

export function useTransactions(filters?: TransactionFilters) {
    return useQuery({
        queryKey: ['transactions', filters],
        queryFn: async () => {
             const params = new URLSearchParams();
             if (filters?.limit) params.append('limit', filters.limit.toString());
             if (filters?.month) params.append('month', filters.month.toString());
             if (filters?.year) params.append('year', filters.year.toString());
             
             return (await fetchAPI(`/transactions/?${params.toString()}`)) as Transaction[];
        },
        staleTime: 1000 * 60 * 5, // 5 minutes
    });
}

export function useDeleteTransaction() {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: async (id: number) => {
            return fetchAPI(`/transactions/${id}`, { method: 'DELETE' });
        },
        onSuccess: () => {
            toast.success("Transação excluída");
            queryClient.invalidateQueries({ queryKey: ['transactions'] });
        },
        onError: () => {
            // toast.error("Erro ao excluir transação");
        }
    });
}

export function useCreateTransaction() {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: async (data: any) => {
             return fetchAPI('/transactions/', {
                 method: 'POST',
                 body: JSON.stringify(data)
             });
        },
        onSuccess: () => {
             toast.success("Transação criada com sucesso!");
             queryClient.invalidateQueries({ queryKey: ['transactions'] });
        },
        onError: () =>  toast.error("Erro ao criar transação")
    });
}

export function useUpdateTransaction() {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: async ({ id, data }: { id: number, data: any }) => {
             return fetchAPI(`/transactions/${id}`, {
                 method: 'PUT',
                 body: JSON.stringify(data)
             });
        },
        onSuccess: () => {
             toast.success("Transação atualizada!");
             queryClient.invalidateQueries({ queryKey: ['transactions'] });
        },
        onError: () => toast.error("Erro ao atualizar transação")
    });
}
