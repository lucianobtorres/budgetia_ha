# Em: tests/test_financial_calculator.py
import datetime

import pandas as pd
import pytest

import config
from finance.financial_calculator import FinancialCalculator


@pytest.fixture
def calculator() -> FinancialCalculator:
    """Retorna uma instância limpa do FinancialCalculator para cada teste."""
    return FinancialCalculator()


# --- Testes de calcular_saldo_devedor_atual ---
# (Estes testes já estavam passando, permanecem iguais)
def test_calcular_saldo_devedor_atual_com_juros(
    calculator: FinancialCalculator,
) -> None:
    # ... (teste permanece igual) ...
    saldo = calculator.calcular_saldo_devedor_atual(
        valor_parcela=1000.0,
        taxa_juros_mensal=1.0,
        parcelas_totais=24,
        parcelas_pagas=5,
    )
    assert pytest.approx(saldo, 0.01) == 17226.01


def test_calcular_saldo_devedor_atual_sem_juros(
    calculator: FinancialCalculator,
) -> None:
    # ... (teste permanece igual) ...
    saldo = calculator.calcular_saldo_devedor_atual(
        valor_parcela=500.0,
        taxa_juros_mensal=0.0,
        parcelas_totais=10,
        parcelas_pagas=3,
    )
    assert saldo == 3500.0


def test_calcular_saldo_devedor_quitado(calculator: FinancialCalculator) -> None:
    # ... (teste permanece igual) ...
    saldo = calculator.calcular_saldo_devedor_atual(
        valor_parcela=1000.0,
        taxa_juros_mensal=1.0,
        parcelas_totais=24,
        parcelas_pagas=24,
    )
    assert saldo == 0.0


# --- Testes de get_summary ---


def test_get_summary_calcula_corretamente(calculator: FinancialCalculator) -> None:
    """Testa o cálculo de receitas, despesas e saldo."""
    # ARRANGE
    dados_transacoes = {
        "Tipo (Receita/Despesa)": ["Receita", "Despesa", "Receita", "Despesa"],
        "Valor": [5000.0, 150.0, 200.0, 80.50],
        "Categoria": ["Salário", "Lazer", "Freelance", "Alimentação"],
    }
    df_transacoes = pd.DataFrame(
        dados_transacoes, columns=config.LAYOUT_PLANILHA[config.NomesAbas.TRANSACOES]
    ).fillna("")

    receitas_esperadas = 5200.0
    despesas_esperadas = 230.50
    saldo_esperado = 4969.50

    # ACT
    resumo = calculator.get_summary(df_transacoes)

    # --- CORREÇÃO (KeyError - Falha 1) ---
    assert resumo["total_receitas"] == pytest.approx(receitas_esperadas)
    assert resumo["total_despesas"] == pytest.approx(despesas_esperadas)
    assert resumo["saldo"] == pytest.approx(saldo_esperado)
    # --- FIM DA CORREÇÃO ---


def test_get_summary_dataframe_vazio(calculator: FinancialCalculator) -> None:
    """Testa se o resumo retorna zeros para um DataFrame vazio."""
    # ARRANGE
    df_vazio = pd.DataFrame(columns=config.LAYOUT_PLANILHA[config.NomesAbas.TRANSACOES])

    # ACT
    resumo = calculator.get_summary(df_vazio)

    # --- CORREÇÃO (KeyError - Falha 2) ---
    assert resumo["total_receitas"] == 0.0
    assert resumo["total_despesas"] == 0.0
    assert resumo["saldo"] == 0.0
    # --- FIM DA CORREÇÃO ---


# --- Teste de calcular_status_orcamentos ---
# (Este teste deve passar agora com a correção do NameError)
def test_calcular_status_orcamentos_cenarios_diversos(
    calculator: FinancialCalculator,
) -> None:
    """
    Testa o cálculo de status de orçamentos para vários cenários:
    - OK: Gasto abaixo de 90%
    - Alerta: Gasto entre 90% e 100%
    - Estourado: Gasto acima de 100%
    - Ignorado: Transações de categorias sem orçamento
    - Ignorado: Transações de meses anteriores (FILTRO DE DATA)
    """
    # ARRANGE
    hoje = datetime.datetime.now()
    data_hoje_str = hoje.strftime("%Y-%m-%d")
    mes_passado = (hoje.replace(day=1) - datetime.timedelta(days=1)).strftime(
        "%Y-%m-%d"
    )

    dados_orcamentos = {
        "Categoria": ["Alimentação", "Lazer", "Transporte", "Educação"],
        "Valor Limite Mensal": [1000.0, 500.0, 300.0, 1500.0],
        "Período Orçamento": ["Mensal", "Mensal", "Mensal", "Mensal"],
    }
    df_orcamentos = pd.DataFrame(
        dados_orcamentos,
        columns=config.LAYOUT_PLANILHA[config.NomesAbas.ORCAMENTOS],
    ).fillna(0)

    dados_transacoes = {
        "Tipo (Receita/Despesa)": [
            "Despesa",  # 1. Gasto OK (60%)
            "Despesa",  # 2. Gasto em ALERTA (95%)
            "Despesa",  # 3. Gasto ESTOURADO (110%)
            "Receita",  # 4. Receita (ignorado)
            "Despesa",  # 5. Gasto SEM orçamento (ignorado)
            "Despesa",  # 6. Gasto MÊS PASSADO (ignorado pelo filtro de data)
        ],
        "Categoria": [
            "Transporte",
            "Lazer",
            "Alimentação",
            "Salário",
            "Saúde",
            "Alimentação",
        ],
        "Valor": [180.0, 475.0, 1100.0, 5000.0, 200.0, 300.0],
        "Data": [
            data_hoje_str,
            data_hoje_str,
            data_hoje_str,
            data_hoje_str,
            data_hoje_str,
            mes_passado,
        ],
    }
    df_transacoes = pd.DataFrame(
        dados_transacoes,
        columns=config.LAYOUT_PLANILHA[config.NomesAbas.TRANSACOES],
    ).fillna("")

    # ACT
    df_resultado = calculator.calcular_status_orcamentos(df_transacoes, df_orcamentos)

    # ASSERT
    df_resultado.set_index("Categoria", inplace=True)

    # Cenário 1: Transporte (180 / 300 = 60%) -> OK
    assert df_resultado.loc["Transporte", "Valor Gasto Atual"] == 180.0
    assert df_resultado.loc["Transporte", "Status Orçamento"] == "OK"

    # Cenário 2: Lazer (475 / 500 = 95%) -> Alerta
    assert df_resultado.loc["Lazer", "Valor Gasto Atual"] == 475.0
    assert df_resultado.loc["Lazer", "Status Orçamento"] == "Alerta"

    # Cenário 3: Alimentação (1100 / 1000 = 110%) -> Estourado (ignora os 300 do mês passado)
    assert df_resultado.loc["Alimentação", "Valor Gasto Atual"] == 1100.0
    assert df_resultado.loc["Alimentação", "Status Orçamento"] == "Estourado"

    # Cenário 4: Educação (Sem gastos) -> OK
    assert df_resultado.loc["Educação", "Valor Gasto Atual"] == 0.0
    assert df_resultado.loc["Educação", "Status Orçamento"] == "OK"


# --- Testes de get_expenses_by_category ---
# (Estes testes já estavam passando, permanecem iguais)
def test_get_expenses_by_category_ranking_correto(
    calculator: FinancialCalculator,
) -> None:
    # ... (teste permanece igual) ...
    dados = {
        "Tipo (Receita/Despesa)": ["Despesa", "Despesa", "Despesa", "Receita"],
        "Categoria": ["Alimentação", "Lazer", "Alimentação", "Salário"],
        "Valor": [100.0, 50.0, 20.0, 3000.0],
    }
    df = pd.DataFrame(dados)
    resultado = calculator.get_expenses_by_category(df, top_n=5)
    assert resultado.iloc[0] == 120.0
    assert resultado.index[0] == "Alimentação"


def test_get_expenses_by_category_sem_despesas(
    calculator: FinancialCalculator,
) -> None:
    # ... (teste permanece igual) ...
    dados = {
        "Tipo (Receita/Despesa)": ["Receita", "Receita"],
        "Categoria": ["Salário", "Freelance"],
        "Valor": [100.0, 50.0],
    }
    df = pd.DataFrame(dados)
    resultado = calculator.get_expenses_by_category(df, top_n=5)
    assert resultado.empty


# --- Testes de gerar_analise_proativa ---
# (Estes testes devem passar agora com a correção da lógica)
def test_gerar_analise_proativa_com_alertas(calculator: FinancialCalculator) -> None:
    """
    Testa a geração de múltiplos insights:
    - Saldo Negativo
    - Orçamento Estourado
    - Orçamento em Alerta (novo)
    """
    # ARRANGE
    dados_orcamentos = {
        "Categoria": ["Alimentação", "Lazer", "Transporte"],
        "Valor Limite Mensal": [1000.0, 500.0, 300.0],
        "Valor Gasto Atual": [1100.0, 475.0, 100.0],
        "Porcentagem Gasta (%)": [110.0, 95.0, 33.3],
        # --- Status como o 'calcular_status_orcamentos' gera ---
        "Status Orçamento": ["Estourado", "Alerta", "OK"],
    }
    df_orcamentos = pd.DataFrame(
        dados_orcamentos,
        columns=config.LAYOUT_PLANILHA[config.NomesAbas.ORCAMENTOS],
    ).fillna(0)

    saldo_total = -500.0

    # ACT
    insights = calculator.gerar_analise_proativa(df_orcamentos, saldo_total)

    # ASSERT
    # (Deve encontrar 3 insights: Estourado, Alerta, Saldo Negativo)
    assert len(insights) == 3
    tipos_insights = {insight["tipo_insight"] for insight in insights}
    assert "Alerta de Orçamento" in tipos_insights
    assert "Aviso de Orçamento" in tipos_insights
    assert "Alerta de Saldo" in tipos_insights


def test_gerar_analise_proativa_cenario_saudavel(
    calculator: FinancialCalculator,
) -> None:
    """
    Testa a geração de insight de "Sugestão de Economia" quando
    o saldo está positivo e os orçamentos estão "OK".
    """
    # ARRANGE
    dados_orcamentos = {
        "Categoria": ["Alimentação", "Lazer"],
        "Valor Limite Mensal": [1000.0, 500.0],
        "Valor Gasto Atual": [700.0, 200.0],
        "Porcentagem Gasta (%)": [70.0, 40.0],
        "Status Orçamento": ["OK", "OK"],  # Status correto
    }
    df_orcamentos = pd.DataFrame(
        dados_orcamentos,
        columns=config.LAYOUT_PLANILHA[config.NomesAbas.ORCAMENTOS],
    ).fillna(0)

    saldo_total = 2500.0

    # ACT
    insights = calculator.gerar_analise_proativa(df_orcamentos, saldo_total)

    # ASSERT
    # (Deve encontrar 1 insight: Sugestão de Economia)
    assert len(insights) == 1
    assert insights[0]["tipo_insight"] == "Sugestão de Economia"
