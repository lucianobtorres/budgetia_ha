import { useQuery } from '@tanstack/react-query';
import { fetchAPI } from '../services/api';

export interface Category {
    name: string;
    type: string;
    icon: string;
    tags: string;
}

export function useCategories() {
    const query = useQuery({
        queryKey: ['categories'],
        queryFn: () => fetchAPI('/categories/') as Promise<Category[]>,
        staleTime: 1000 * 60 * 5, // 5 minutes
    });

    return {
        categories: query.data || [],
        isLoading: query.isLoading,
        isError: query.isError,
        error: query.error,
        refetch: query.refetch
    };
}
