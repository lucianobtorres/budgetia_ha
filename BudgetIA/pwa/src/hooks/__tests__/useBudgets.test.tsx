import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useBudgetsList } from '../useBudgets';
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

describe('useBudgets Baseline', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should fetch budgets list successfully', async () => {
        const mockApiResponse = [
            { 'ID Orcamento': 1, 'Categoria': 'Alimentação', 'Valor Limite': 1000, 'Período Orçamento': 'Mensal' },
        ];

        vi.mocked(fetchAPI).mockResolvedValue(mockApiResponse);

        const { result } = renderHook(() => useBudgetsList(), {
            wrapper: createWrapper(),
        });

        await waitFor(() => expect(result.current.isSuccess).toBe(true));

        const expectedDomain = [
            { 
                id: 1, 
                category: 'Alimentação', 
                limitValue: 1000, 
                period: 'Mensal',
                currentSpent: 0,
                spentPercentage: 0,
                status: '',
                observations: '',
                lastUpdate: ''
            },
        ];

        expect(result.current.data).toEqual(expectedDomain);
        expect(fetchAPI).toHaveBeenCalledWith('/budgets/');
    });
});
