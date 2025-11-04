import config
from finance.planilha_manager import PlanilhaManager
from finance.tools.define_budget_tool import DefineBudgetTool


def test_define_budget_tool_cria_novo_orcamento(
    plan_manager_para_ferramentas: PlanilhaManager,
) -> None:
    """
    Testa se a ferramenta consegue criar um novo orçamento e
    se o DataFrame no manager é atualizado corretamente.
    """
    # ARRANGE
    categoria = "Alimentação"
    valor_limite = 700.0
    periodo = "Mensal"
    observacoes = "Mercado e restaurantes"

    # ACT
    tool = DefineBudgetTool(planilha_manager=plan_manager_para_ferramentas)
    resultado_string = tool.run(
        categoria=categoria,
        valor_limite=valor_limite,
        periodo=periodo,
        observacoes=observacoes,
    )

    # ASSERT
    # 1. Verifica a mensagem de retorno
    assert f"Novo orçamento para '{categoria}' criado." in resultado_string

    # 2. Verifica o DataFrame no manager
    df_orcamentos = plan_manager_para_ferramentas.visualizar_dados(
        config.NomesAbas.ORCAMENTOS
    )
    assert len(df_orcamentos) == 1

    orcamento_criado = df_orcamentos.iloc[0]
    assert orcamento_criado["Categoria"] == categoria
    assert orcamento_criado["Valor Limite Mensal"] == valor_limite
    assert orcamento_criado["Período Orçamento"] == periodo
    assert orcamento_criado["Observações"] == observacoes


def test_define_budget_tool_atualiza_orcamento_existente(
    plan_manager_para_ferramentas: PlanilhaManager,
) -> None:
    """
    Testa se a ferramenta consegue atualizar um orçamento existente
    sem criar uma nova linha.
    """
    # ARRANGE
    # Pré-popula o manager com um orçamento inicial
    categoria = "Transporte"
    plan_manager_para_ferramentas.adicionar_ou_atualizar_orcamento(
        categoria=categoria, valor_limite=200.0, periodo="Mensal"
    )

    # Novos valores para atualização
    novo_valor_limite = 250.0
    novas_observacoes = "Aumento gasolina"

    # ACT
    tool = DefineBudgetTool(planilha_manager=plan_manager_para_ferramentas)
    resultado_string = tool.run(
        categoria=categoria,  # Mesma categoria
        valor_limite=novo_valor_limite,
        periodo="Mensal",  # Mesmo período
        observacoes=novas_observacoes,
    )

    # ASSERT
    # 1. Verifica a mensagem de retorno
    assert f"Orçamento para '{categoria}' atualizado." in resultado_string

    # 2. Verifica o DataFrame no manager
    df_orcamentos = plan_manager_para_ferramentas.visualizar_dados(
        config.NomesAbas.ORCAMENTOS
    )
    # Garante que não adicionou uma nova linha
    assert len(df_orcamentos) == 1

    orcamento_atualizado = df_orcamentos.iloc[0]
    assert orcamento_atualizado["Categoria"] == categoria
    assert orcamento_atualizado["Valor Limite Mensal"] == novo_valor_limite
    assert orcamento_atualizado["Observações"] == novas_observacoes
