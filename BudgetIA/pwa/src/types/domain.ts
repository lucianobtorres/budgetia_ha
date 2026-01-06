export interface Summary {
    saldo_atual: number;
    total_receitas: number;
    total_despesas: number;
    [key: string]: number;
}

export interface ExpenseData {
    name: string;
    value: number;
    [key: string]: any;
}

export interface Budget {
    "ID Orcamento"?: number;
    Categoria: string;
    'Valor Limite': number;
    'Valor Gasto Atual': number;
    'Status Orçamento': string; // Ex: "Dentro do Orçamento", "Estourado"
    'Período Orçamento'?: string;
    'Observações'?: string;
    [key: string]: any;
}

export interface Transaction {
    id: number;
    data: string;
    descricao: string;
    categoria: string;
    valor: number;
    tipo: 'Receita' | 'Despesa';
    forma_pagamento?: string;
}
