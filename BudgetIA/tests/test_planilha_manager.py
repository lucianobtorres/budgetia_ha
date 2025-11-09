# Em: tests/test_planilha_manager.py
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

import config
from finance.excel_handler import ExcelHandler
from finance.planilha_manager import PlanilhaManager

# Precisamos do DataContext para o nosso mock


@pytest.fixture
def mock_excel_handler() -> MagicMock:
    """Cria um mock completo do ExcelHandler para um ARQUIVO EXISTENTE."""
    handler = MagicMock(spec=ExcelHandler)
    handler.file_path = "dummy_test.xlsx"

    mock_dfs = {
        aba: pd.DataFrame(columns=colunas)
        for aba, colunas in config.LAYOUT_PLANILHA.items()
    }
    # Retorna is_new_file=False para pular o _populate_initial_data no __init__
    handler.load_sheets.return_value = (mock_dfs, False)

    handler.save_sheets = MagicMock()
    return handler


@pytest.fixture
def plan_manager(mock_excel_handler: MagicMock) -> PlanilhaManager:
    """
    Cria um PlanilhaManager real para testes, com um handler mockado
    e um estado 100% limpo (sem dados de exemplo).
    """

    # Pula o 'recalculate_budgets' que é chamado no 'else' do __init__
    with patch.object(PlanilhaManager, "recalculate_budgets", return_value=None):
        pm = PlanilhaManager(excel_handler=mock_excel_handler)

        pm.save = MagicMock()
        pm.recalculate_budgets = MagicMock()

        return pm


# --- TESTES REATORADOS ---


def test_get_summary_calcula_saldo_corretamente(plan_manager: PlanilhaManager) -> None:
    """Testa se o método get_summary() calcula corretamente os totais."""

    dados_de_teste = {
        "Tipo (Receita/Despesa)": ["Receita", "Despesa", "Despesa"],
        "Valor": [1000.00, 150.25, 50.00],
    }
    colunas = config.LAYOUT_PLANILHA[config.NomesAbas.TRANSACOES]
    df_teste = pd.DataFrame(dados_de_teste, columns=colunas).fillna(0)

    plan_manager._context.update_dataframe(config.NomesAbas.TRANSACOES, df_teste)

    # (1000.00 - 150.25 - 50.00) = 799.75
    resumo = plan_manager.get_summary()

    # (Com a correção no FinancialCalculator, este teste deve passar)
    assert resumo["total_receitas"] == 1000.00
    assert resumo["total_despesas"] == 200.25
    assert resumo["saldo"] == 799.75


def test_adicionar_registro_atualiza_dados_e_orcamento(
    plan_manager: PlanilhaManager,
) -> None:
    """Testa o fluxo completo: inicialização, adição de registro e verificação."""

    plan_manager.adicionar_registro(
        data="2025-01-01",
        tipo="Despesa",
        categoria="Alimentação",
        descricao="Almoço",
        valor=50.0,
    )

    df_transacoes = plan_manager.visualizar_dados(config.NomesAbas.TRANSACOES)
    assert len(df_transacoes) == 1
    assert df_transacoes.iloc[0]["Categoria"] == "Alimentação"
    plan_manager.recalculate_budgets.assert_called_once()


def test_adicionar_ou_atualizar_orcamento_cria_novo_orcamento(
    plan_manager: PlanilhaManager,
) -> None:
    """Testa se o método cria uma nova linha de orçamento quando a categoria é nova."""

    mensagem = plan_manager.adicionar_ou_atualizar_orcamento(
        categoria="Alimentação", valor_limite=500.0, periodo="Mensal"
    )

    assert "Novo orçamento para 'Alimentação' criado" in mensagem
    df_orcamentos = plan_manager.visualizar_dados(config.NomesAbas.ORCAMENTOS)
    assert len(df_orcamentos) == 1
    assert df_orcamentos.iloc[0]["Categoria"] == "Alimentação"
    plan_manager.recalculate_budgets.assert_called_once()


def test_adicionar_ou_atualizar_orcamento_atualiza_orcamento_existente(
    plan_manager: PlanilhaManager,
) -> None:
    """Testa se o método atualiza a linha de um orçamento existente."""

    dados_orcamento = {
        "Categoria": ["Alimentação"],
        "Valor Limite Mensal": [600.0],
        "Período Orçamento": ["Mensal"],
    }
    df_orcamentos = pd.DataFrame(
        dados_orcamento, columns=config.LAYOUT_PLANILHA[config.NomesAbas.ORCAMENTOS]
    ).fillna(0)

    plan_manager._context.update_dataframe(config.NomesAbas.ORCAMENTOS, df_orcamentos)

    mensagem = plan_manager.adicionar_ou_atualizar_orcamento(
        categoria="Alimentação",
        valor_limite=750.0,
        periodo="Mensal",
        observacoes="Ajuste",
    )

    assert "Orçamento para 'Alimentação' atualizado" in mensagem
    df_orcamentos_final = plan_manager.visualizar_dados(config.NomesAbas.ORCAMENTOS)
    assert len(df_orcamentos_final) == 1
    assert df_orcamentos_final.iloc[0]["Valor Limite Mensal"] == 750.0
    assert df_orcamentos_final.iloc[0]["Observações"] == "Ajuste"


def test_adicionar_ou_atualizar_divida_cria_nova_divida_com_saldo_calculado(
    plan_manager: PlanilhaManager,
) -> None:
    """
    Testa se, ao criar uma nova dívida, a linha é adicionada e o
    saldo devedor é calculado corretamente.
    """

    mensagem = plan_manager.adicionar_ou_atualizar_divida(
        nome_divida="Financiamento XPTO",
        valor_original=20000.0,
        taxa_juros_mensal=1.0,
        parcelas_totais=24,
        valor_parcela=1000.0,
        parcelas_pagas=5,
    )

    assert "Nova dívida 'Financiamento XPTO' registrada" in mensagem

    # --- CORREÇÃO (AssertionError - Ponto para Vírgula) ---
    assert "R$ 17,226.01" in mensagem
    # --- FIM DA CORREÇÃO ---

    df_dividas = plan_manager.visualizar_dados(config.NomesAbas.DIVIDAS)
    assert len(df_dividas) == 1
    assert df_dividas.iloc[0]["Nome da Dívida"] == "Financiamento XPTO"

    assert pytest.approx(df_dividas.iloc[0]["Saldo Devedor Atual"], 0.01) == 17226.01


def test_adicionar_ou_atualizar_divida_atualiza_divida_existente(
    plan_manager: PlanilhaManager,
) -> None:
    """Testa se, ao atualizar uma dívida, o saldo é recalculado."""

    dados_divida_inicial = {
        "Nome da Dívida": ["Financiamento XPTO"],
        "Valor Original": [20000.0],
        "Taxa Juros Mensal (%)": [1.0],
        "Parcelas Totais": [24],
        "Valor Parcela": [1000.0],
        "Parcelas Pagas": [5],
    }
    df_dividas = pd.DataFrame(
        dados_divida_inicial, columns=config.LAYOUT_PLANILHA[config.NomesAbas.DIVIDAS]
    ).fillna(0)

    plan_manager._context.update_dataframe(config.NomesAbas.DIVIDAS, df_dividas)

    mensagem = plan_manager.adicionar_ou_atualizar_divida(
        nome_divida="Financiamento XPTO",
        valor_original=20000.0,
        taxa_juros_mensal=1.0,
        parcelas_totais=24,
        valor_parcela=1000.0,
        parcelas_pagas=10,
    )

    assert "Dívida 'Financiamento XPTO' atualizada" in mensagem

    # --- CORREÇÃO (AssertionError - Ponto para Vírgula) ---
    assert "R$ 13,003.70" in mensagem
    # --- FIM DA CORREÇÃO ---

    df_dividas_final = plan_manager.visualizar_dados(config.NomesAbas.DIVIDAS)
    assert len(df_dividas_final) == 1
    assert df_dividas_final.iloc[0]["Parcelas Pagas"] == 10

    assert (
        pytest.approx(df_dividas_final.iloc[0]["Saldo Devedor Atual"], 0.01) == 13003.70
    )
