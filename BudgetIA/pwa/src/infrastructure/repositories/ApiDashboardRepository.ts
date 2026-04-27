import { fetchAPI } from '../../services/api';
import type { FinancialSummary, CategoryExpense } from '../../domain/models/Dashboard';

export class ApiDashboardRepository {
    async getSummary(): Promise<FinancialSummary> {
        const data = await fetchAPI<{ total_receitas: number; total_despesas: number }>('/dashboard/summary');
        return {
            totalIncome: data?.total_receitas || 0,
            totalExpenses: data?.total_despesas || 0,
            balance: (data?.total_receitas || 0) - (data?.total_despesas || 0),
        };
    }

    async getExpensesByCategory(topN = 5): Promise<CategoryExpense[]> {
        const data = await fetchAPI<Record<string, number>>(`/dashboard/expenses_by_category?top_n=${topN}`);
        if (!data) return [];
        return Object.entries(data).map(([name, value]) => ({
            name,
            value: value as number
        }));
    }
}
