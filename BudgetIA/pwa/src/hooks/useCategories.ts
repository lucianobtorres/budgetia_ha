import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ApiCategoryRepository } from '../infrastructure/repositories/ApiCategoryRepository';
import type { CategoryCreate } from '../types/api';

const categoryRepo = new ApiCategoryRepository();

export function useCategories() {
    return useQuery({
        queryKey: ['categories'],
        queryFn: () => categoryRepo.list(),
        staleTime: 1000 * 60 * 5, // 5 minutes
    });
}

export function useCreateCategory() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (data: CategoryCreate) => categoryRepo.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['categories'] });
        },
    });
}

export function useUpdateCategory() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ oldName, payload }: { oldName: string; payload: CategoryCreate }) => 
            categoryRepo.update(oldName, payload),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['categories'] });
            queryClient.invalidateQueries({ queryKey: ['transactions'] });
            queryClient.invalidateQueries({ queryKey: ['dashboard'] });
        },
    });
}

export function useDeleteCategory() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (name: string) => categoryRepo.delete(name),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['categories'] });
            queryClient.invalidateQueries({ queryKey: ['transactions'] });
        },
    });
}
