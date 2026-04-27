import type { TransactionSchema } from '../../types/api';

export type TransactionType = 'Receita' | 'Despesa';

export interface Transaction {
    id: number;
    date: string;
    type: TransactionType;
    category: string;
    description: string;
    value: number;
    status: string;
}

// Utility to create a domain transaction from API schema
export function createTransactionFromSchema(schema: TransactionSchema): Transaction {
    return {
        id: schema['ID Transacao'] || 0,
        date: schema.Data || '',
        type: schema['Tipo (Receita/Despesa)'] as TransactionType,
        category: schema.Categoria || '',
        description: schema.Descricao || '',
        value: schema.Valor || 0,
        status: schema.Status || '',
    };
}
