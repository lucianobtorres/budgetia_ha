# Em: tests/services/test_budget_service.py

import datetime

import pandas as pd
import pytest

import config
from config import ColunasOrcamentos, ColunasTransacoes, ValoresTipo
from finance.services.budget_service import BudgetService


@pytest.fixture
def budget_service() -> BudgetService:
    """Retorna uma instância limpa do BudgetService para cada teste."""
    return BudgetService()


def test_calcular_status_orcamentos_cenarios_diversos(
    budget_service: BudgetService,
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
        ColunasTransacoes.CATEGORIA: ["Alimentação", "Lazer", "Transporte", "Educação"],
        ColunasOrcamentos.LIMITE: [1000.0, 500.0, 300.0, 1500.0],
        ColunasOrcamentos.PERIODO: ["Mensal", "Mensal", "Mensal", "Mensal"],
    }
    df_orcamentos = pd.DataFrame(
        dados_orcamentos,
        columns=config.LAYOUT_PLANILHA[config.NomesAbas.ORCAMENTOS],
    ).fillna(0)

    dados_transacoes = {
        ColunasTransacoes.TIPO: [
            ValoresTipo.DESPESA,  # 1. Gasto OK (60%)
            ValoresTipo.DESPESA,  # 2. Gasto em ALERTA (95%)
            ValoresTipo.DESPESA,  # 3. Gasto ESTOURADO (110%)
            ValoresTipo.RECEITA,  # 4. Receita (ignorado)
            ValoresTipo.DESPESA,  # 5. Gasto SEM orçamento (ignorado)
            ValoresTipo.DESPESA,  # 6. Gasto MÊS PASSADO (ignorado pelo filtro de data)
        ],
        ColunasTransacoes.CATEGORIA: [
            "Transporte",
            "Lazer",
            "Alimentação",
            "Salário",
            "Saúde",
            "Alimentação",
        ],
        ColunasTransacoes.VALOR: [180.0, 475.0, 1100.0, 5000.0, 200.0, 300.0],
        ColunasTransacoes.DATA: [
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
    df_resultado = budget_service.calcular_status_orcamentos(
        df_transacoes, df_orcamentos
    )

    # ASSERT
    df_resultado.set_index(ColunasTransacoes.CATEGORIA, inplace=True)

    # Cenário 1: Transporte (180 / 300 = 60%) -> OK
    assert df_resultado.loc["Transporte", ColunasOrcamentos.GASTO] == 180.0
    assert df_resultado.loc["Transporte", ColunasOrcamentos.STATUS] == "OK"

    # Cenário 2: Lazer (475 / 500 = 95%) -> Alerta
    assert df_resultado.loc["Lazer", ColunasOrcamentos.GASTO] == 475.0
    assert df_resultado.loc["Lazer", ColunasOrcamentos.STATUS] == "Alerta"

    # Cenário 3: Alimentação (1100 / 1000 = 110%) -> Estourado (ignora os 300 do mês passado)
    assert df_resultado.loc["Alimentação", ColunasOrcamentos.GASTO] == 1100.0
    assert df_resultado.loc["Alimentação", ColunasOrcamentos.STATUS] == "Estourado"

    # Cenário 4: Educação (Sem gastos) -> OK
    assert df_resultado.loc["Educação", ColunasOrcamentos.GASTO] == 0.0
    assert df_resultado.loc["Educação", ColunasOrcamentos.STATUS] == "OK"
