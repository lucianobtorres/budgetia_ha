# Em: tests/tools/test_add_transaction_tool.py
from finance.planilha_manager import PlanilhaManager
from finance.tools.add_transaction_tool import AddTransactionTool


def test_add_transaction_tool_com_data(
    plan_manager_para_ferramentas: PlanilhaManager,
) -> None:
    """
    Testa se a ferramenta 'AdicionarTransacaoTool' consegue adicionar um
    registro simples e se os dados são persistidos no 'dfs' do manager.
    """
    # ARRANGE
    # O plan_manager vem da fixture (vazio)

    # Argumentos para a ferramenta
    data = "2025-10-17"
    tipo = "Despesa"
    categoria = "Alimentação"
    valor = 50.75
    descricao = "Almoço"

    # ACT
    tool = AddTransactionTool(planilha_manager=plan_manager_para_ferramentas)
    resultado_string = tool.run(
        tipo=tipo,
        categoria=categoria,
        descricao=descricao,
        valor=valor,
        data=data,
        # Status é opcional e default="Concluído"
    )
    # ASSERT
    # 1. Verifica a resposta para a IA
    assert (
        "adicionada com sucesso" in resultado_string.lower()
    )  # Verifica se a ação foi bem-sucedida
    assert (
        "alimentação" in resultado_string.lower()
    )  # Verifica se a categoria está na msg
    assert "almoço" in resultado_string.lower()  # Verifica se a descrição está na msg
    assert "50.75" in resultado_string

    # 2. Verifica se o DataFrame no manager foi realmente atualizado
    df_transacoes = plan_manager_para_ferramentas.visualizar_dados(
        "Visão Geral e Transações"
    )
    assert len(df_transacoes) == 1

    registro_adicionado = df_transacoes.iloc[0]
    assert registro_adicionado["Categoria"] == "Alimentação"
    assert registro_adicionado["Valor"] == 50.75
