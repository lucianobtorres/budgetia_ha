/**
 * Este arquivo foi gerado automaticamente pelo script export_types.py.
 * NÃO EDITE DIRETAMENTE.
 */

export interface TransactionSchema {
  "ID Transacao"?: number;
  Data: string;
  "Tipo (Receita/Despesa)": string;
  Categoria: string;
  Descricao: string;
  Valor: number;
  Status?: string;
}

export interface TransactionCreate {
  data?: string;
  tipo: string;
  categoria: string;
  descricao: string;
  valor: number;
  status?: string;
  parcelas?: number;
}

export interface TransactionUpdate {
  data?: string;
  tipo: string;
  categoria: string;
  descricao: string;
  valor: number;
  status?: string;
  parcelas?: number;
}

export interface BudgetSchema {
  "ID Orcamento"?: number;
  Categoria: string;
  "Valor Limite": number;
  "Valor Gasto Atual"?: number;
  "Porcentagem Gasta (%)"?: number;
  "Período Orçamento"?: string;
  "Status Orçamento"?: string;
  Observações?: string;
  "Última Atualização Orçamento"?: string;
}

export interface BudgetCreate {
  categoria: string;
  valor_limite: number;
  periodo?: string;
  observacoes?: string;
}

export interface CategorySchema {
  name: string;
  type: string;
  icon?: string;
  tags?: string;
}

export interface CategoryCreate {
  name: string;
  type?: string;
  icon?: string;
  tags?: string;
}

export interface GoalSchema {
  nome: string;
  valor_alvo: number;
  valor_atual?: number;
  data_alvo?: string;
  status?: string;
  observacoes?: string;
  id: number;
  percentual_progresso: number;
}

export interface GoalCreate {
  nome: string;
  valor_alvo: number;
  valor_atual?: number;
  data_alvo?: string;
  status?: string;
  observacoes?: string;
}

export interface DebtSchema {
  nome: string;
  valor_original: number;
  taxa_juros_mensal: number;
  parcelas_totais: number;
  parcelas_pagas?: number;
  valor_parcela: number;
  data_proximo_pgto?: string;
  observacoes?: string;
  id: number;
  saldo_devedor_atual: number;
}

export interface DebtCreate {
  nome: string;
  valor_original: number;
  taxa_juros_mensal: number;
  parcelas_totais: number;
  parcelas_pagas?: number;
  valor_parcela: number;
  data_proximo_pgto?: string;
  observacoes?: string;
}

export interface ToolInfoSchema {
  name: string;
  description: string;
  label?: string;
  is_essential: boolean;
}

export interface ObserverInfoSchema {
  id: string;
  name: string;
  description: string;
  is_active: boolean;
  config?: unknown;
}

export interface SubscriptionKeywordsUpdate {
  keywords: string[];
}

