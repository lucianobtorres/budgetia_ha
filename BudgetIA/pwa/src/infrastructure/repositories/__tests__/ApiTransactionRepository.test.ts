import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiTransactionRepository } from '../ApiTransactionRepository';
import { fetchAPI } from '../../../services/api';
import type { TransactionCreate } from '../../../types/api';

vi.mock('../../../services/api', () => ({
    fetchAPI: vi.fn(),
}));

describe('ApiTransactionRepository', () => {
    let repository: ApiTransactionRepository;

    beforeEach(() => {
        vi.clearAllMocks();
        repository = new ApiTransactionRepository();
    });

    it('should call fetchAPI with correct filters and map results', async () => {
        const mockApiResponse = [
            { 'ID Transacao': 1, 'Data': '2024-01-01', 'Tipo (Receita/Despesa)': 'Receita', 'Valor': 100 }
        ];
        vi.mocked(fetchAPI).mockResolvedValue(mockApiResponse);

        const results = await repository.list({ month: 1, year: 2024 });

        expect(fetchAPI).toHaveBeenCalledWith('/transactions/?month=1&year=2024');
        expect(results).toHaveLength(1);
        expect(results[0].id).toBe(1);
        expect(results[0].type).toBe('Receita');
    });

    it('should call create endpoint correctly', async () => {
        const payload = { descricao: 'Teste' } as unknown as TransactionCreate;
        await repository.create(payload);
        expect(fetchAPI).toHaveBeenCalledWith('/transactions/', expect.objectContaining({ method: 'POST' }));
    });
});
