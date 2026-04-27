import pandas as pd

import config
from config import ColunasCategorias
from finance.domain.models.category import Category
from finance.domain.repositories.category_repository import ICategoryRepository
from finance.infrastructure.persistence.data_context import FinancialDataContext


class ExcelCategoryRepository(ICategoryRepository):
    """
    Implementação concreta do repositório de categorias para Excel.
    """

    def __init__(self, context: FinancialDataContext):
        self._context = context
        self._sheet_name = config.NomesAbas.CATEGORIAS

    def _to_entity(self, row: pd.Series) -> Category:
        """Converte linha do DataFrame para Entidade Category."""
        return Category(
            name=str(row[ColunasCategorias.NOME]),
            type=str(row[ColunasCategorias.TIPO]),
            icon=str(row[ColunasCategorias.ICONE])
            if pd.notna(row[ColunasCategorias.ICONE])
            else None,
            tags=str(row[ColunasCategorias.TAGS])
            if pd.notna(row[ColunasCategorias.TAGS])
            else None,
        )

    def _to_row(self, c: Category) -> dict:
        """Converte Entidade Category para dicionário de linha."""
        return {
            ColunasCategorias.NOME: c.name,
            ColunasCategorias.TIPO: c.type,
            ColunasCategorias.ICONE: c.icon,
            ColunasCategorias.TAGS: c.tags,
        }

    def list_all(self) -> list[Category]:
        """Lista todas as categorias da planilha."""
        try:
            df = self._context.get_dataframe(self._sheet_name)
        except ValueError:
            return []

        if df.empty:
            return []
        return [self._to_entity(row) for _, row in df.iterrows()]

    def get_by_name(self, name: str) -> Category | None:
        """Busca categoria pelo nome (case-insensitive)."""
        df = self._context.get_dataframe(self._sheet_name)
        if df.empty:
            return None

        mask = df[ColunasCategorias.NOME].astype(str).str.lower() == name.lower()
        row = df[mask]
        if row.empty:
            return None
        return self._to_entity(row.iloc[0])

    def save(self, category: Category) -> Category:
        """Salva ou atualiza uma categoria."""
        df = self._context.get_dataframe(self._sheet_name)

        mask = (
            df[ColunasCategorias.NOME].astype(str).str.lower() == category.name.lower()
        )
        if mask.any():
            # Atualiza existente
            idx = df.index[mask][0]
            row_data = self._to_row(category)
            for col, val in row_data.items():
                df.at[idx, col] = val
        else:
            # Adiciona nova
            new_row = pd.DataFrame([self._to_row(category)])
            df = pd.concat([df, new_row], ignore_index=True)

        self._context.update_dataframe(self._sheet_name, df)
        return category

    def delete(self, name: str) -> bool:
        """Remove categoria pelo nome."""
        df = self._context.get_dataframe(self._sheet_name)
        mask = df[ColunasCategorias.NOME].astype(str).str.lower() == name.lower()
        if not mask.any():
            return False

        df = df[~mask]
        self._context.update_dataframe(self._sheet_name, df)
        return True
