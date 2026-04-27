import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { ApiTransactionRepository } from '../infrastructure/repositories/ApiTransactionRepository';
import type { TransactionCreate, TransactionUpdate } from '../types/api';

const transactionRepo = new ApiTransactionRepository();

interface TransactionFilters {
    month?: number;
    year?: number;
    limit?: number;
}

export function useTransactions(filters?: TransactionFilters) {
    return useQuery({
        queryKey: ['transactions', filters],
        queryFn: () => transactionRepo.list(filters),
        staleTime: 1000 * 60 * 5, // 5 minutes
    });
}

export function useDeleteTransaction() {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: (id: number) => transactionRepo.delete(id),
        onSuccess: () => {
            toast.success("Transação excluída");
            queryClient.invalidateQueries({ queryKey: ['transactions'] });
        },
    });
}

export function useCreateTransaction() {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: (data: TransactionCreate) => transactionRepo.create(data),
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
        mutationFn: ({ id, data }: { id: number, data: TransactionUpdate }) => transactionRepo.update(id, data),
        onSuccess: () => {
             toast.success("Transação atualizada!");
             queryClient.invalidateQueries({ queryKey: ['transactions'] });
        },
        onError: () => toast.error("Erro ao atualizar transação")
    });
}

export function useCreateTransactionsBatch() {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: (data: TransactionCreate[]) => transactionRepo.createBatch(data),
        onSuccess: (response: { message: string }) => {
             toast.success(response.message || "Transações importadas com sucesso!");
             queryClient.invalidateQueries({ queryKey: ['transactions'] });
             queryClient.invalidateQueries({ queryKey: ['dashboard'] });
        },
        onError: () =>  toast.error("Erro ao importar transações")
    });
}
