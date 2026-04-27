import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useTransactions } from '../useTransactions';
import { fetchAPI } from '../../services/api';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

// Mock fetchAPI
vi.mock('../../services/api', () => ({
    fetchAPI: vi.fn(),
}));

const createWrapper = () => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: {
                retry: false,
            },
        },
    });
    return ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
};

describe('useTransactions Baseline', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should fetch transactions successfully', async () => {
        const mockApiResponse = [
            { 'ID Transacao': 1, 'Descricao': 'Almoço', 'Valor': 35.5, 'Categoria': 'Alimentação', 'Data': '2024-03-20', 'Tipo (Receita/Despesa)': 'Despesa' },
            { 'ID Transacao': 2, 'Descricao': 'Salário', 'Valor': 5000, 'Categoria': 'Salário', 'Data': '2024-03-05', 'Tipo (Receita/Despesa)': 'Receita' },
        ];

        vi.mocked(fetchAPI).mockResolvedValue(mockApiResponse);

        const { result } = renderHook(() => useTransactions(), {
            wrapper: createWrapper(),
        });

        await waitFor(() => expect(result.current.isSuccess).toBe(true));

        const expectedDomain = [
            { id: 1, description: 'Almoço', value: 35.5, category: 'Alimentação', date: '2024-03-20', type: 'Despesa', status: '' },
            { id: 2, description: 'Salário', value: 5000, category: 'Salário', date: '2024-03-05', type: 'Receita', status: '' },
        ];

        expect(result.current.data).toEqual(expectedDomain);
        expect(fetchAPI).toHaveBeenCalledWith('/transactions/?');
    });

    it('should apply filters correctly', async () => {
        vi.mocked(fetchAPI).mockResolvedValue([]);

        const filters = { month: 3, year: 2024, limit: 10 };
        const { result } = renderHook(() => useTransactions(filters), {
            wrapper: createWrapper(),
        });

        await waitFor(() => expect(result.current.isSuccess).toBe(true));

        expect(fetchAPI).toHaveBeenCalledWith('/transactions/?limit=10&month=3&year=2024');
    });
});
