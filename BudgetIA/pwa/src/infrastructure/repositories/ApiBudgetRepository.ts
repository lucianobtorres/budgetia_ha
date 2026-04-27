import type { BudgetCreate, BudgetSchema } from '../../types/api';
import type { Budget } from '../../domain/models/Budget';
import { createBudgetFromSchema } from '../../domain/models/Budget';
import type { IBudgetRepository } from '../../domain/repositories/IBudgetRepository';
import { fetchAPI } from '../../services/api';

export class ApiBudgetRepository implements IBudgetRepository {
    async list(): Promise<Budget[]> {
        const data = await fetchAPI<BudgetSchema[]>('/budgets/');
        return (data || []).map(createBudgetFromSchema);
    }

    async create(data: BudgetCreate): Promise<void> {
        await fetchAPI('/budgets/', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async update(id: number, data: BudgetCreate): Promise<void> {
        await fetchAPI(`/budgets/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async delete(id: number): Promise<void> {
        await fetchAPI(`/budgets/${id}`, { method: 'DELETE' });
    }
}
