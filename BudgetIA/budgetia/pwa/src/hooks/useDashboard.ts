import { useQuery } from "@tanstack/react-query";
import { fetchAPI } from "../services/api";

export interface Summary {
    saldo_atual: number;
    total_receitas: number;
    total_despesas: number;
    [key: string]: number;
}

export interface ExpenseData {
    name: string;
    value: number;
}

interface Budget {
    Categoria: string;
    'Valor Limite': number;
    'Valor Gasto Atual': number;
}


export function useSummary() {
    return useQuery<Summary>({
        queryKey: ['dashboard', 'summary'],
        queryFn: () => fetchAPI('/dashboard/summary'),
    });
}

export function useExpenses(topN = 5) {
    return useQuery<ExpenseData[]>({
        queryKey: ['dashboard', 'expenses', topN],
        queryFn: async () => {
            const data = await fetchAPI(`/dashboard/expenses_by_category?top_n=${topN}`);
            // Transform data if needed for Recharts
            if (!data) return [];
            return Object.entries(data).map(([name, value]) => ({
                name,
                value: value as number
            }));
        },
    });
}

export function useBudgets() {
    return useQuery<Budget[]>({
        queryKey: ['dashboard', 'budgets'],
        queryFn: () => fetchAPI('/dashboard/budgets'),
    });
}
