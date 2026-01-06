import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchAPI } from "../services/api";
import { toast } from "sonner";
import type { Budget } from "../types/domain";

export function useBudgetsList() {
    return useQuery<Budget[]>({
        queryKey: ['budgets-list'],
        queryFn: async () => {
             const data = await fetchAPI('/budgets/');
             return data || [];
        }
    });
}

export function useCreateBudget() {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: async (data: any) => {
            return fetchAPI('/budgets/', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        },
        onSuccess: () => {
            toast.success("Orçamento criado com sucesso!");
            queryClient.invalidateQueries({ queryKey: ['budgets-list'] });
            queryClient.invalidateQueries({ queryKey: ['dashboard'] });
        },
        onError: () => toast.error("Erro ao criar orçamento")
    });
}

export function useUpdateBudget() {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: async ({ id, data }: { id: number, data: any }) => {
            return fetchAPI(`/budgets/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
        },
        onSuccess: () => {
             toast.success("Orçamento atualizado!");
             queryClient.invalidateQueries({ queryKey: ['budgets-list'] });
             queryClient.invalidateQueries({ queryKey: ['dashboard'] });
        },
        onError: () => toast.error("Erro ao atualizar orçamento")
    });
}

export function useDeleteBudget() {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: async (id: number) => {
             return fetchAPI(`/budgets/${id}`, { method: 'DELETE' });
        },
        onSuccess: () => {
             toast.success("Orçamento excluído!");
             queryClient.invalidateQueries({ queryKey: ['budgets-list'] });
             queryClient.invalidateQueries({ queryKey: ['dashboard'] });
        },
        onError: () => toast.error("Erro ao excluir orçamento")
    });
}
