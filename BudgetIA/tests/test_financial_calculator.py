# Em: tests/test_financial_calculator.py
import datetime

import pandas as pd
import pytest

import config
from finance.financial_calculator import FinancialCalculator


# Fixture para inicializar o calculator (boa prática para testes futuros)
@pytest.fixture
def calculator() -> FinancialCalculator:
    """Retorna uma instância limpa do FinancialCalculator para cada teste."""
    return FinancialCalculator()


def test_calcular_saldo_devedor_atual_com_juros(
    calculator: FinancialCalculator,
) -> None:
    """
    Testa o cálculo do Valor Presente (saldo devedor) com juros.
    Exemplo: R$ 1000/mês, 1% juros, 12 parcelas restantes.
    """
    # ARRANGE
    taxa_juros = 1.0  # 1%
    parcelas_restantes = 12
    valor_parcela = 1000.0

    # Cálculo esperado (usando a fórmula de VP):
    # VP = 1000 * (1 - (1 + 0.01)**-12) / 0.01 = 11255.08
    saldo_esperado = 11255.08

    # ACT
    saldo_calculado = calculator.calcular_saldo_devedor_atual(
        valor_parcela=valor_parcela,
        taxa_juros_mensal=taxa_juros,
        parcelas_totais=24,  # Irrelevante, desde que parcelas_pagas esteja correto
        parcelas_pagas=12,  # (24 - 12 = 12 restantes)
    )

    # ASSERT
    assert saldo_calculado == pytest.approx(saldo_esperado, abs=0.01)


def test_calcular_saldo_devedor_atual_sem_juros(
    calculator: FinancialCalculator,
) -> None:
    """Testa o cálculo simples de multiplicação quando não há juros."""
    # ARRANGE
    taxa_juros = 0.0
    parcelas_restantes = 10
    valor_parcela = 150.0
    saldo_esperado = 1500.0  # (150 * 10)

    # ACT
    saldo_calculado = calculator.calcular_saldo_devedor_atual(
        valor_parcela=valor_parcela,
        taxa_juros_mensal=taxa_juros,
        parcelas_totais=10,
        parcelas_pagas=0,
    )

    # ASSERT
    assert saldo_calculado == pytest.approx(saldo_esperado)


def test_calcular_saldo_devedor_quitado(calculator: FinancialCalculator) -> None:
    """Testa se o saldo é zero quando não há parcelas restantes."""
    # ARRANGE
    taxa_juros = 1.0
    valor_parcela = 1000.0

    # ACT
    saldo_calculado = calculator.calcular_saldo_devedor_atual(
        valor_parcela=valor_parcela,
        taxa_juros_mensal=taxa_juros,
        parcelas_totais=24,
        parcelas_pagas=24,  # Quitada!
    )

    # ASSERT
    assert saldo_calculado == 0.0


def test_get_summary_calcula_corretamente(calculator: FinancialCalculator) -> None:
    """Testa o cálculo de receitas, despesas e saldo."""
    # ARRANGE
    dados_transacoes = {
        "Tipo (Receita/Despesa)": ["Receita", "Despesa", "Receita", "Despesa"],
        "Valor": [5000.0, 150.0, 200.0, 80.50],
        "Categoria": ["Salário", "Lazer", "Freelance", "Alimentação"],
    }
    # Usamos as colunas do config para garantir consistência
    df_transacoes = pd.DataFrame(
        dados_transacoes, columns=config.LAYOUT_PLANILHA[config.NomesAbas.TRANSACOES]
    ).fillna("")  # Preenche o resto com strings vazias ou NaN apropriados

    # (5000.0 + 200.0) - (150.0 + 80.50) = 4969.50
    receitas_esperadas = 5200.0
    despesas_esperadas = 230.50
    saldo_esperado = 4969.50

    # ACT
    resumo = calculator.get_summary(df_transacoes)

    # ASSERT
    assert resumo["receitas"] == pytest.approx(receitas_esperadas)
    assert resumo["despesas"] == pytest.approx(despesas_esperadas)
    assert resumo["saldo"] == pytest.approx(saldo_esperado)


def test_get_summary_dataframe_vazio(calculator: FinancialCalculator) -> None:
    """Testa se o resumo retorna zeros para um DataFrame vazio."""
    # ARRANGE
    df_vazio = pd.DataFrame(columns=config.LAYOUT_PLANILHA[config.NomesAbas.TRANSACOES])

    # ACT
    resumo = calculator.get_summary(df_vazio)

    # ASSERT
    assert resumo["receitas"] == 0.0
    assert resumo["despesas"] == 0.0
    assert resumo["saldo"] == 0.0


def test_calcular_status_orcamentos_cenarios_diversos(
    calculator: FinancialCalculator,
) -> None:
    """
    Testa o cálculo de status de orçamentos para vários cenários:
    - Ativo: Gasto abaixo de 90%
    - Atenção: Gasto entre 90% e 100%
    - Excedido: Gasto acima de 100%
    - Ignorado: Transações de categorias sem orçamento
    - Ignorado: Transações de meses anteriores
    """
    # ARRANGE

    # 1. Definir data atual para os testes
    hoje = datetime.datetime.now()
    data_hoje_str = hoje.strftime("%Y-%m-%d")
    # Data de um mês atrás (para ser ignorada)
    mes_passado = (hoje.replace(day=1) - datetime.timedelta(days=1)).strftime(
        "%Y-%m-%d"
    )

    # 2. Criar DataFrame de Orçamentos
    dados_orcamentos = {
        "Categoria": ["Alimentação", "Lazer", "Transporte", "Educação"],
        "Valor Limite Mensal": [1000.0, 500.0, 300.0, 1500.0],
        "Período Orçamento": ["Mensal", "Mensal", "Mensal", "Mensal"],
    }
    df_orcamentos = pd.DataFrame(
        dados_orcamentos,
        columns=config.LAYOUT_PLANILHA[config.NomesAbas.ORCAMENTOS],
    ).fillna(0)

    # 3. Criar DataFrame de Transações
    dados_transacoes = {
        "Tipo (Receita/Despesa)": [
            "Despesa",  # 1. Gasto ATIVO (60%)
            "Despesa",  # 2. Gasto em ATENÇÃO (95%)
            "Despesa",  # 3. Gasto EXCEDIDO (110%)
            "Receita",  # 4. Receita (deve ser ignorada)
            "Despesa",  # 5. Gasto em categoria SEM orçamento (deve ser ignorado)
            "Despesa",  # 6. Gasto do MÊS PASSADO (deve ser ignorado)
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

    # Criar um dict para facilitar a verificação
    status_por_categoria = df_resultado.set_index("Categoria")["Status Orçamento"]
    gasto_por_categoria = df_resultado.set_index("Categoria")["Valor Gasto Atual"]

    # 1. Transporte (180 de 300 = 60%)
    assert status_por_categoria["Transporte"] == "Ativo"
    assert gasto_por_categoria["Transporte"] == pytest.approx(180.0)

    # 2. Lazer (475 de 500 = 95%)
    assert status_por_categoria["Lazer"] == "Atenção: Próximo do Limite"
    assert gasto_por_categoria["Lazer"] == pytest.approx(475.0)

    # 3. Alimentação (1100 de 1000 = 110%)
    assert status_por_categoria["Alimentação"] == "Excedido"
    assert gasto_por_categoria["Alimentação"] == pytest.approx(1100.0)

    # 4. Educação (sem gastos)
    assert status_por_categoria["Educação"] == "Ativo"
    assert gasto_por_categoria["Educação"] == pytest.approx(0.0)


def test_get_expenses_by_category_ranking_correto(
    calculator: FinancialCalculator,
) -> None:
    """
    Testa a soma de despesas por categoria e o ranking top_n.
    """
    # ARRANGE
    dados_transacoes = {
        "Tipo (Receita/Despesa)": [
            "Despesa",
            "Despesa",
            "Receita",  # Deve ser ignorada
            "Despesa",
            "Despesa",
        ],
        "Categoria": ["Alimentação", "Lazer", "Salário", "Alimentação", "Moradia"],
        "Valor": [100.0, 50.0, 5000.0, 150.0, 300.0],
    }
    df_transacoes = pd.DataFrame(
        dados_transacoes,
        columns=config.LAYOUT_PLANILHA[config.NomesAbas.TRANSACOES],
    ).fillna("")

    # Despesas esperadas:
    # Moradia: 300.0
    # Alimentação: 100.0 + 150.0 = 250.0
    # Lazer: 50.0
    # Top 2 esperado: Moradia (300), Alimentação (250)

    # ACT
    top_expenses = calculator.get_expenses_by_category(df_transacoes, top_n=2)

    # ASSERT
    assert isinstance(top_expenses, pd.Series)
    assert len(top_expenses) == 2
    assert top_expenses.index[0] == "Moradia"
    assert top_expenses.values[0] == pytest.approx(300.0)
    assert top_expenses.index[1] == "Alimentação"
    assert top_expenses.values[1] == pytest.approx(250.0)


def test_get_expenses_by_category_sem_despesas(calculator: FinancialCalculator) -> None:
    """
    Testa o comportamento quando não há nenhuma transação de 'Despesa'.
    """
    # ARRANGE
    dados_transacoes = {
        "Tipo (Receita/Despesa)": ["Receita", "Receita"],
        "Categoria": ["Salário", "Freelance"],
        "Valor": [5000.0, 300.0],
    }
    df_transacoes = pd.DataFrame(
        dados_transacoes,
        columns=config.LAYOUT_PLANILHA[config.NomesAbas.TRANSACOES],
    ).fillna("")

    # ACT
    top_expenses = calculator.get_expenses_by_category(df_transacoes, top_n=3)

    # ASSERT
    assert isinstance(top_expenses, pd.Series)
    assert top_expenses.empty  # Esperamos uma Series vazia


def test_gerar_analise_proativa_com_alertas(calculator: FinancialCalculator) -> None:
    """
    Testa a geração de múltiplos insights:
    - Saldo Negativo
    - Orçamento Excedido
    - Orçamento em Atenção
    """
    # ARRANGE
    # 1. Orçamentos
    dados_orcamentos = {
        "Categoria": ["Alimentação", "Lazer", "Transporte"],
        "Valor Limite Mensal": [1000.0, 500.0, 300.0],
        "Valor Gasto Atual": [1100.0, 475.0, 100.0],
        "Porcentagem Gasta (%)": [110.0, 95.0, 33.3],
        "Status Orçamento": ["Excedido", "Atenção: Próximo do Limite", "Ativo"],
    }
    df_orcamentos = pd.DataFrame(
        dados_orcamentos,
        columns=config.LAYOUT_PLANILHA[config.NomesAbas.ORCAMENTOS],
    ).fillna(0)

    # 2. Saldo
    saldo_total = -500.0

    # ACT
    insights = calculator.gerar_analise_proativa(df_orcamentos, saldo_total)

    # ASSERT
    assert len(insights) == 3  # Um insight para cada alerta

    tipos_de_insight = {insight["tipo_insight"] for insight in insights}
    titulos_de_insight = {insight["titulo_insight"] for insight in insights}

    assert "Alerta de Orçamento Excedido" in tipos_de_insight
    assert "Atenção ao Orçamento" in tipos_de_insight
    assert "Alerta de Saldo Negativo" in tipos_de_insight

    assert "Atenção: Orçamento de 'Alimentação' excedido!" in titulos_de_insight
    assert "Alerta: Orçamento de 'Lazer' próximo do limite." in titulos_de_insight
    assert "Seu balanço geral está negativo." in titulos_de_insight


def test_gerar_analise_proativa_cenario_saudavel(
    calculator: FinancialCalculator,
) -> None:
    """
    Testa a geração de insight de "Sugestão de Economia" quando
    o saldo está positivo e os orçamentos estão "Ativos".
    """
    # ARRANGE
    # 1. Orçamentos
    dados_orcamentos = {
        "Categoria": ["Alimentação", "Lazer"],
        "Valor Limite Mensal": [1000.0, 500.0],
        "Valor Gasto Atual": [700.0, 200.0],
        "Porcentagem Gasta (%)": [70.0, 40.0],
        "Status Orçamento": ["Ativo", "Ativo"],
    }
    df_orcamentos = pd.DataFrame(
        dados_orcamentos,
        columns=config.LAYOUT_PLANILHA[config.NomesAbas.ORCAMENTOS],
    ).fillna(0)

    # 2. Saldo
    saldo_total = 2500.0

    # ACT
    insights = calculator.gerar_analise_proativa(df_orcamentos, saldo_total)

    # ASSERT
    assert len(insights) == 1  # Apenas 1 insight (sugestão de economia)

    tipo_de_insight = insights[0]["tipo_insight"]
    titulo_de_insight = insights[0]["titulo_insight"]

    assert tipo_de_insight == "Sugestão de Economia"
    assert titulo_de_insight == "Ótimo! Seu saldo está positivo."
