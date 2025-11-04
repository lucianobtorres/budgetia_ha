# tests/test_planilha_manager.py

import datetime

import pandas as pd
import pytest

import config
from finance.excel_handler import ExcelHandler
from finance.planilha_manager import PlanilhaManager


# --- TESTE 1: CÁLCULO DE RESUMO ---
def test_get_summary_calcula_saldo_corretamente() -> None:
    """Testa se o método get_summary() calcula corretamente os totais."""
    handler_teste = ExcelHandler(file_path="dummy.xlsx")
    plan_manager = PlanilhaManager(excel_handler=handler_teste)

    dados_de_teste = {
        "Tipo (Receita/Despesa)": ["Receita", "Despesa", "Despesa"],
        "Valor": [1000.00, 150.25, 50.00],
    }
    colunas = config.LAYOUT_PLANILHA[config.NomesAbas.TRANSACOES]
    df_teste = pd.DataFrame(dados_de_teste, columns=colunas).fillna(0)
    plan_manager.dfs[config.NomesAbas.TRANSACOES] = df_teste

    summary = plan_manager.get_summary()
    assert summary["saldo"] == 799.75


# --- TESTE 2: ADIÇÃO DE TRANSAÇÃO E EFEITO NO ORÇAMENTO ---
def test_adicionar_registro_atualiza_dados_e_orcamento() -> None:
    """Testa o fluxo completo: inicialização, adição de registro e verificação."""
    handler_teste = ExcelHandler(file_path="dummy.xlsx")
    plan_manager = PlanilhaManager(excel_handler=handler_teste)

    # ARRANGE: Cria um estado inicial limpo e explícito
    plan_manager.dfs[config.NomesAbas.TRANSACOES] = pd.DataFrame(
        columns=config.LAYOUT_PLANILHA[config.NomesAbas.TRANSACOES]
    )
    dados_orcamento = {
        "Categoria": ["Alimentação"],
        "Valor Limite Mensal": [600.0],
        "Período Orçamento": ["Mensal"],
    }
    df_orcamentos = pd.DataFrame(
        dados_orcamento, columns=config.LAYOUT_PLANILHA[config.NomesAbas.ORCAMENTOS]
    ).fillna(0)
    plan_manager.dfs[config.NomesAbas.ORCAMENTOS] = df_orcamentos
    plan_manager.recalculate_budgets()

    # ACT
    plan_manager.adicionar_registro(
        data=datetime.date.today().strftime("%Y-%m-%d"),
        tipo="Despesa",
        categoria="Alimentação",
        descricao="Almoço",
        valor=45.50,
    )

    # ASSERT
    orcamento_final = plan_manager.visualizar_dados(config.NomesAbas.ORCAMENTOS).iloc[0]
    assert orcamento_final["Valor Gasto Atual"] == 45.50


# --- TESTE 3: CRIAÇÃO DE UM NOVO ORÇAMENTO ---
def test_adicionar_ou_atualizar_orcamento_cria_novo_orcamento() -> None:
    """Testa se o método cria uma nova linha de orçamento quando a categoria é nova."""
    handler_teste = ExcelHandler(file_path="dummy.xlsx")
    plan_manager = PlanilhaManager(excel_handler=handler_teste)

    # ARRANGE: Começa com orçamentos vazios
    plan_manager.dfs[config.NomesAbas.ORCAMENTOS] = pd.DataFrame(
        columns=config.LAYOUT_PLANILHA[config.NomesAbas.ORCAMENTOS]
    )

    # ACT
    plan_manager.adicionar_ou_atualizar_orcamento(
        categoria="Educação", valor_limite=300.0
    )

    # ASSERT
    df_final = plan_manager.visualizar_dados(config.NomesAbas.ORCAMENTOS)
    assert len(df_final) == 1
    assert df_final.iloc[0]["Categoria"] == "Educação"
    assert df_final.iloc[0]["Valor Limite Mensal"] == 300.0


# --- TESTE 4: ATUALIZAÇÃO DE UM ORÇAMENTO EXISTENTE ---
def test_adicionar_ou_atualizar_orcamento_atualiza_orcamento_existente() -> None:
    """Testa se o método atualiza a linha de um orçamento existente, sem criar uma nova."""
    handler_teste = ExcelHandler(file_path="dummy.xlsx")
    plan_manager = PlanilhaManager(excel_handler=handler_teste)

    # ARRANGE: Começa com um orçamento de Alimentação existente
    dados_orcamento = {
        "Categoria": ["Alimentação"],
        "Valor Limite Mensal": [600.0],
        "Período Orçamento": ["Mensal"],  # Adicionando o período explicitamente
    }
    df_orcamentos = pd.DataFrame(
        dados_orcamento, columns=config.LAYOUT_PLANILHA[config.NomesAbas.ORCAMENTOS]
    ).fillna(0)
    plan_manager.dfs[config.NomesAbas.ORCAMENTOS] = df_orcamentos

    # ACT
    plan_manager.adicionar_ou_atualizar_orcamento(
        categoria="Alimentação", valor_limite=750.50
    )

    # ASSERT
    df_final = plan_manager.visualizar_dados(config.NomesAbas.ORCAMENTOS)
    assert len(df_final) == 1  # Garante que não adicionou uma nova linha
    assert df_final.iloc[0]["Valor Limite Mensal"] == 750.50

    # Adicione estas duas novas funções ao final de tests/test_planilha_manager.py


def test_adicionar_ou_atualizar_divida_cria_nova_divida_com_saldo_calculado() -> None:
    """
    Testa se, ao criar uma nova dívida, a linha é adicionada e o
    saldo devedor é calculado corretamente com base nos juros e parcelas.
    """
    # --- ARRANGE (Preparação) ---
    handler_teste = ExcelHandler(file_path="dummy_create_debt.xlsx")
    plan_manager = PlanilhaManager(excel_handler=handler_teste)
    plan_manager.dfs[config.NomesAbas.DIVIDAS] = pd.DataFrame(
        columns=config.LAYOUT_PLANILHA[config.NomesAbas.DIVIDAS]
    )

    # Dados conhecidos para o teste
    valor_parcela = 1000.0
    taxa_juros = 1.0  # 1.0% ao mês
    parcelas_totais = 24

    # --- ACT (Ação) ---
    plan_manager.adicionar_ou_atualizar_divida(
        nome_divida="Financiamento XPTO",
        valor_original=20000.0,
        taxa_juros_mensal=taxa_juros,
        parcelas_totais=parcelas_totais,
        valor_parcela=valor_parcela,
    )

    # --- ASSERT (Verificação) ---
    df_dividas = plan_manager.visualizar_dados(config.NomesAbas.DIVIDAS)
    assert len(df_dividas) == 1

    divida_criada = df_dividas.iloc[0]
    assert divida_criada["Nome da Dívida"] == "Financiamento XPTO"

    # Verificação da matemática financeira (Valor Presente de uma anuidade)
    # Saldo devedor = PMT * [1 - (1 + i)^-n] / i
    juros = taxa_juros / 100
    saldo_devedor_esperado = (
        valor_parcela * (1 - (1 + juros) ** (-parcelas_totais)) / juros
    )
    # Para nossos valores (1000, 1%, 24m), o resultado é ~21243.39

    assert divida_criada["Saldo Devedor Atual"] == pytest.approx(saldo_devedor_esperado)


def test_adicionar_ou_atualizar_divida_atualiza_divida_existente() -> None:
    """
    Testa se, ao atualizar uma dívida, as parcelas pagas e o saldo devedor
    são recalculados corretamente, sem adicionar uma nova linha.
    """
    # --- ARRANGE (Preparação) ---
    handler_teste = ExcelHandler(file_path="dummy_update_debt.xlsx")
    plan_manager = PlanilhaManager(excel_handler=handler_teste)

    # Começamos com uma dívida já existente
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
    plan_manager.dfs[config.NomesAbas.DIVIDAS] = df_dividas

    # --- ACT (Ação) ---
    # Simulamos o pagamento de mais uma parcela
    plan_manager.adicionar_ou_atualizar_divida(
        nome_divida="Financiamento XPTO",
        valor_original=20000.0,
        taxa_juros_mensal=1.0,
        parcelas_totais=24,
        valor_parcela=1000.0,
        parcelas_pagas=6,  # O número de parcelas pagas aumentou
    )

    # --- ASSERT (Verificação) ---
    df_dividas_final = plan_manager.visualizar_dados(config.NomesAbas.DIVIDAS)
    assert len(df_dividas_final) == 1  # Garante que não criou uma nova dívida

    divida_atualizada = df_dividas_final.iloc[0]
    assert divida_atualizada["Parcelas Pagas"] == 6

    # Recalcula o saldo devedor esperado com as parcelas restantes (24 - 6 = 18)
    juros = 1.0 / 100
    parcelas_restantes = 18
    saldo_devedor_esperado = 1000.0 * (1 - (1 + juros) ** (-parcelas_restantes)) / juros
    # O resultado esperado é ~16398.27

    assert divida_atualizada["Saldo Devedor Atual"] == pytest.approx(
        saldo_devedor_esperado
    )
