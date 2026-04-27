import config
from finance.planilha_manager import PlanilhaManager


def test_rename_category_cascades_to_transactions(
    plan_manager_para_ferramentas: PlanilhaManager,
):
    """
    Garante que ao renomear uma categoria no manager,
    as transações existentes também são atualizadas.
    """
    pm = plan_manager_para_ferramentas
    # 1. Setup: Categoria 'Mercado' e uma transação vinculada
    pm.adicionar_categoria(nome="Mercado", tipo="Despesa")
    pm.adicionar_registro(
        data="2024-01-01",
        tipo="Despesa",
        categoria="Mercado",
        descricao="Compras do mês",
        valor=200.0,
    )

    # 2. Renomeia 'Mercado' -> 'Supermercado'
    sucesso = pm.atualizar_categoria(  # noqa: F841
        old_name="Mercado",
        new_name="Supermercado",
        tipo="Despesa",
        icone="Cart",
        tags="",
    )

    # 3. Assert: A transação deve ter mudado para 'Alimentação'
    df_transacoes = pm.visualizar_dados(config.NomesAbas.TRANSACOES)
    assert df_transacoes.iloc[0][config.ColunasTransacoes.CATEGORIA] == "Supermercado"

    # E a categoria antiga não deve existir mais
    cats = pm.get_categorias()
    assert "Mercado" not in cats[config.ColunasCategorias.NOME].values
    assert "Supermercado" in cats[config.ColunasCategorias.NOME].values
