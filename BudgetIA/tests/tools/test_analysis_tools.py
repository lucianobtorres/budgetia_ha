# tests/tools/test_analysis_tools.py
from unittest.mock import MagicMock

import pandas as pd

from finance.tools.calculate_expenses_by_category_tool import (
    CalcularDespesasPorCategoriaTool,
)
from finance.tools.identify_top_expenses_tool import IdentificarMaioresGastosTool


def test_calculate_expenses_by_category_tool() -> None:
    # ARRANGE
    mock_df = pd.DataFrame(
        [
            {
                "Data": "2025-01-01",
                "Tipo (Receita/Despesa)": "Despesa",
                "Categoria": "Alimentação",
                "Valor": 100.0,
                "Descricao": "Restaurante",
            },
            {
                "Data": "2025-01-02",
                "Tipo (Receita/Despesa)": "Despesa",
                "Categoria": "Transporte",
                "Valor": 50.0,
                "Descricao": "Uber",
            },
            {
                "Data": "2025-01-03",
                "Tipo (Receita/Despesa)": "Despesa",
                "Categoria": "Alimentação",
                "Valor": 50.0,
                "Descricao": "Mercado",
            },
            {
                "Data": "2025-01-04",
                "Tipo (Receita/Despesa)": "Receita",
                "Categoria": "Salário",
                "Valor": 1000.0,
                "Descricao": "Pagamento",
            },
        ]
    )
    mock_view_data = MagicMock(return_value=mock_df)

    tool = CalcularDespesasPorCategoriaTool(view_data_func=mock_view_data)

    # ACT
    result = tool.run()

    # ASSERT
    assert "Despesas por Categoria" in result
    assert "Alimentação" in result
    assert "150" in result  # 100 + 50
    assert "Transporte" in result
    assert "50" in result
    assert "Salário" not in result  # Receita não deve aparecer
    mock_view_data.assert_called_once()


def test_identify_top_expenses_tool() -> None:
    # ARRANGE
    mock_df = pd.DataFrame(
        [
            {
                "Data": "2025-01-01",
                "Tipo (Receita/Despesa)": "Despesa",
                "Categoria": "Lazer",
                "Valor": 500.0,
                "Descricao": "Viagem",
            },
            {
                "Data": "2025-01-02",
                "Tipo (Receita/Despesa)": "Despesa",
                "Categoria": "Alimentação",
                "Valor": 10.0,
                "Descricao": "Café",
            },
            {
                "Data": "2025-01-03",
                "Tipo (Receita/Despesa)": "Despesa",
                "Categoria": "Saúde",
                "Valor": 200.0,
                "Descricao": "Farmácia",
            },
        ]
    )
    mock_view_data = MagicMock(return_value=mock_df)

    tool = IdentificarMaioresGastosTool(view_data_func=mock_view_data)

    # ACT
    result = tool.run(top_n=2)

    # ASSERT
    assert "maiores gastos individuais" in result.lower()
    assert "Viagem" in result
    assert "Farmácia" in result
    assert "Café" not in result  # Pois pedimos top_n=2
    mock_view_data.assert_called_once()
