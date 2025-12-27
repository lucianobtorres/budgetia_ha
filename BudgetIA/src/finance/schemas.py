from typing import Any

from pydantic import BaseModel, Field


# Schemas para Ferramentas de Transação
class AddTransactionInput(BaseModel):
    tipo: str = Field(description="Tipo da transação, deve ser 'Receita' ou 'Despesa'.")
    categoria: str = Field(
        description="Categoria da transação (ex: 'Salário', 'Aluguel', 'Alimentação', 'Transporte', 'Lazer', 'Educação', 'Saúde'). Seja específico e tente categorizar."
    )
    descricao: str | float = Field(description="Descrição detalhada da transação.")
    valor: float = Field(description="Valor da transação.")
    data: str | None = Field(
        default=None,
        description="Data da transação no formato 'AAAA-MM-DD'. Se não for fornecida, a ferramenta usará a data atual do sistema (hoje).",
    )
    status: str = Field(
        default="Concluído",
        description="Status da transação (ex: 'Concluído', 'Pendente'). Padrão é 'Concluído'.",
    )


class ExtrairTransacoesDoTextoInput(BaseModel):
    texto_usuario: str = Field(
        description="O texto do usuário contendo descrições de transações financeiras para serem extraídas."
    )


# Schemas para Ferramentas de Análise
class VisualizarDadosPlanilhaInput(BaseModel):
    """Esquema de entrada para a ferramenta visualizar_dados_planilha. Não requer parâmetros do usuário."""

    pass


class CalcularSaldoTotalInput(BaseModel):
    """Esquema de entrada para a ferramenta calcular_saldo_total. Não requer parâmetros."""

    pass


class CalcularDespesasPorCategoriaInput(BaseModel):
    """Esquema de entrada para a ferramenta calcular_despesas_por_categoria. Não requer parâmetros."""

    pass


class IdentificarMaioresGastosInput(BaseModel):
    top_n: int = Field(
        default=3,
        description="O número de maiores gastos a serem retornados (padrão é 3).",
    )


class GerarResumoMensalInput(BaseModel):
    ano: int | None = Field(
        default=None,
        description="O ano para filtrar o resumo. Se não informado, resume todos os anos.",
    )
    mes: int | None = Field(
        default=None,
        description="O mês para filtrar o resumo (1-12). Se não informado, resume todos os meses do ano.",
    )


class AnalisarTendenciasGastosInput(BaseModel):
    categoria: str | None = Field(
        default=None,
        description="A categoria específica para analisar tendências (ex: 'Alimentação').",
    )


# Schemas para Ferramentas de Orçamento
class DefinirOrcamentoInput(BaseModel):
    categoria: str = Field(
        description="A categoria para a qual o orçamento será definido (ex: 'Alimentação', 'Transporte', 'Lazer')."
    )
    valor_limite: float = Field(
        description="O valor máximo permitido para a categoria."
    )
    periodo: str = Field(
        default="Mensal",
        description="O período do orçamento (ex: 'Mensal', 'Anual'). Padrão é 'Mensal'.",
    )
    observacoes: str = Field(
        default="", description="Qualquer nota adicional sobre o orçamento."
    )


class VerificarStatusOrcamentoInput(BaseModel):
    categoria: str | None = Field(
        default=None,
        description="A categoria do orçamento a ser verificado. Se não fornecida, retorna o status de todos os orçamentos ativos.",
    )


# Schemas para Ferramentas Proativas
class RegistrarInsightIAInput(BaseModel):
    tipo_insight: str = Field(
        description="Categoria do insight (ex: 'Alerta de Orçamento', 'Sugestão de Economia', 'Análise de Tendência', 'Lembrete')."
    )
    titulo_insight: str = Field(description="Um título conciso para o insight.")
    detalhes_recomendacao: str = Field(
        description="Os detalhes completos e a recomendação acionável da IA."
    )
    status: str = Field(
        default="Novo",
        description="Status do insight (ex: 'Novo', 'Lido', 'Concluído').",
    )


class AdicionarDividaInput(BaseModel):
    nome_divida: str = Field(
        description="O nome da dívida ou credor (ex: 'Financiamento Carro', 'Cartão de Crédito Nubank')."
    )
    valor_original: float = Field(description="O valor total original da dívida.")
    taxa_juros_mensal: float = Field(
        description="A taxa de juros mensal da dívida em porcentagem (ex: 1.5 para 1.5%)."
    )
    parcelas_totais: int = Field(description="O número total de parcelas da dívida.")
    valor_parcela: float = Field(description="O valor de cada parcela mensal.")
    parcelas_pagas: int = Field(
        default=0, description="O número de parcelas já pagas. Padrão é 0."
    )
    data_proximo_pgto: str | None = Field(
        default=None, description="A data do próximo pagamento no formato 'AAAA-MM-DD'."
    )
    observacoes: str = Field(
        default="", description="Qualquer observação relevante sobre a dívida."
    )


class VisualizarDividasInput(BaseModel):
    """Esquema de entrada para a ferramenta visualizar_dividas. Não requer parâmetros do usuário."""

    pass


class AnalisarDividaInput(BaseModel):
    nome_divida: str = Field(
        description="O nome da dívida para análise (ex: 'Financiamento Carro')."
    )


# Schemas para Ferramentas de Onboarding/Perfil
class ColetarPerfilUsuarioInput(BaseModel):
    """
    Schema para a ferramenta que salva dados no Perfil Financeiro.
    """

    campo: str = Field(
        description="O nome do campo a ser salvo (ex: 'Renda Mensal Média', 'Principal Objetivo')."
    )
    valor: Any = Field(
        description="O valor a ser salvo para esse campo (pode ser texto ou número)."
    )


class RecomendarRegraIdealInput(BaseModel):
    """Esquema de entrada para a ferramenta recomendar_regra_ideal. Não requer parâmetros."""

    pass


class AnalisarAdesaoInput(BaseModel):  # NOVO NOME
    rule_name: str = Field(
        description="O nome da regra de ouro financeira a ser analisada. Escolha entre: 50/30/20, 20/10/60/10."
    )  # Pode usar FinancialRules.get_available_rules()
