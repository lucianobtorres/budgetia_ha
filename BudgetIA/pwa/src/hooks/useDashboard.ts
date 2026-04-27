import { useQuery } from "@tanstack/react-query";
import { ApiDashboardRepository } from "../infrastructure/repositories/ApiDashboardRepository";
import type { FinancialSummary, CategoryExpense } from "../domain/models/Dashboard";

const dashboardRepo = new ApiDashboardRepository();

export function useSummary() {
    return useQuery<FinancialSummary>({
        queryKey: ['dashboard', 'summary'],
        queryFn: () => dashboardRepo.getSummary(),
    });
}

export function useExpenses(topN = 5) {
    return useQuery<CategoryExpense[]>({
        queryKey: ['dashboard', 'expenses', topN],
        queryFn: () => dashboardRepo.getExpensesByCategory(topN),
    });
}
