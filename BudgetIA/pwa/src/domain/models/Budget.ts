import type { BudgetSchema } from '../../types/api';

export interface Budget {
    id: number;
    category: string;
    limitValue: number;
    currentSpent: number;
    spentPercentage: number;
    period: string;
    status: string;
    observations: string;
    lastUpdate: string;
}

export function createBudgetFromSchema(schema: BudgetSchema): Budget {
    return {
        id: schema['ID Orcamento'] || 0,
        category: schema.Categoria || '',
        limitValue: schema['Valor Limite'] || 0,
        currentSpent: schema['Valor Gasto Atual'] || 0,
        spentPercentage: schema['Porcentagem Gasta (%)'] || 0,
        period: schema['Período Orçamento'] || '',
        status: schema['Status Orçamento'] || '',
        observations: schema['Observações'] || '',
        lastUpdate: schema['Última Atualização Orçamento'] || '',
    };
}
