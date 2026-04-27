import { describe, it, expect } from 'vitest';
import { createTransactionFromSchema } from '../Transaction';
import type { TransactionSchema } from '../../../types/api';

describe('Transaction Model Mappers', () => {
    it('should map API schema to Domain entity correctly', () => {
        const schema = {
            'ID Transacao': 123,
            'Data': '2024-03-20',
            'Tipo (Receita/Despesa)': 'Despesa',
            'Categoria': 'Alimentação',
            'Descricao': 'Restaurante',
            'Valor': 50.5,
            'Status': 'Pago'
        };

        const domain = createTransactionFromSchema(schema);

        expect(domain).toEqual({
            id: 123,
            date: '2024-03-20',
            type: 'Despesa',
            category: 'Alimentação',
            description: 'Restaurante',
            value: 50.5,
            status: 'Pago'
        });
    });

    it('should handle missing fields with defaults', () => {
        const domain = createTransactionFromSchema({} as unknown as TransactionSchema);
        expect(domain.id).toBe(0);
        expect(domain.value).toBe(0);
    });
});
