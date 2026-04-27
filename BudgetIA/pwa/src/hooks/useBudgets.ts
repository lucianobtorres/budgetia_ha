import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ApiBudgetRepository } from "../infrastructure/repositories/ApiBudgetRepository";
import type { Budget } from "../domain/models/Budget";
import type { BudgetCreate } from "../types/api";

const budgetRepo = new ApiBudgetRepository();

export function useBudgetsList() {
    return useQuery<Budget[]>({
        queryKey: ['budgets-list'],
        queryFn: () => budgetRepo.list()
    });
}

export function useCreateBudget() {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: (data: BudgetCreate) => budgetRepo.create(data),
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
        mutationFn: ({ id, data }: { id: number, data: BudgetCreate }) => budgetRepo.update(id, data),
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
        mutationFn: (id: number) => budgetRepo.delete(id),
        onSuccess: () => {
             toast.success("Orçamento excluído!");
             queryClient.invalidateQueries({ queryKey: ['budgets-list'] });
             queryClient.invalidateQueries({ queryKey: ['dashboard'] });
        },
        onError: () => toast.error("Erro ao excluir orçamento")
    });
}
