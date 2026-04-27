import type { TransactionCreate, TransactionSchema, TransactionUpdate } from '../../types/api';
import type { Transaction } from '../../domain/models/Transaction';
import { createTransactionFromSchema } from '../../domain/models/Transaction';
import type { ITransactionRepository } from '../../domain/repositories/ITransactionRepository';
import { fetchAPI } from '../../services/api';

export class ApiTransactionRepository implements ITransactionRepository {
    async list(filters?: { month?: number; year?: number; limit?: number }): Promise<Transaction[]> {
        const params = new URLSearchParams();
        if (filters?.limit) params.append('limit', filters.limit.toString());
        if (filters?.month) params.append('month', filters.month.toString());
        if (filters?.year) params.append('year', filters.year.toString());

        const data = await fetchAPI<TransactionSchema[]>(`/transactions/?${params.toString()}`);
        return (data || []).map(createTransactionFromSchema);
    }

    async create(data: TransactionCreate): Promise<void> {
        await fetchAPI('/transactions/', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async createBatch(data: TransactionCreate[]): Promise<{ message: string }> {
        return await fetchAPI<{ message: string }>('/transactions/batch', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async update(id: number, data: TransactionUpdate): Promise<void> {
        await fetchAPI(`/transactions/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async delete(id: number): Promise<void> {
        await fetchAPI(`/transactions/${id}`, { method: 'DELETE' });
    }
}
