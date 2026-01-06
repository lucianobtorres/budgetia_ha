import pandas as pd
from typing import Any
import config
from config import ColunasCategorias
from .data_context import FinancialDataContext
from core.logger import get_logger

logger = get_logger("CategoryRepo")

class CategoryRepository:
    """
    Repositório para gerenciar a aba de Categorias.
    """

    def __init__(self, context: FinancialDataContext) -> None:
        self._context = context
        self._aba_nome = config.NomesAbas.CATEGORIAS

    def get_all(self) -> pd.DataFrame:
        """Retorna o DataFrame completo de categorias."""
        try:
            return self._context.get_dataframe(sheet_name=self._aba_nome)
        except ValueError:
            # Se a aba ainda não existe no contexto, retorna vazio
            return pd.DataFrame(columns=config.LAYOUT_PLANILHA[self._aba_nome])

    def add_category(self, nome: str, tipo: str, icone: str = "", tags: str = "") -> bool:
        """Adiciona uma nova categoria."""
        df = self.get_all()
        
        # Check duplicata (Case Insensitive)
        if not df.empty and ColunasCategorias.NOME in df.columns:
            exists = df[ColunasCategorias.NOME].astype(str).str.lower() == nome.lower()
            if exists.any():
                logger.warning(f"Categoria '{nome}' já existe.")
                return False

        novo_registro = pd.DataFrame([{
            ColunasCategorias.NOME: nome,
            ColunasCategorias.TIPO: tipo,
            ColunasCategorias.ICONE: icone,
            ColunasCategorias.TAGS: tags
        }])
        
        df_atualizado = pd.concat([df, novo_registro], ignore_index=True)
        self._context.update_dataframe(self._aba_nome, df_atualizado)
        return True

    def delete_category(self, nome: str) -> bool:
        """Remove uma categoria pelo nome."""
        df = self.get_all()
        if df.empty or ColunasCategorias.NOME not in df.columns:
            return False
            
        mask = df[ColunasCategorias.NOME].astype(str).str.lower() != nome.lower()
        df_novo = df[mask]
        
        if len(df_novo) == len(df):
            return False # Nada foi deletado
            
        self._context.update_dataframe(self._aba_nome, df_novo)
        return True

    def update_category(self, old_name: str, new_name: str, tipo: str, icone: str, tags: str) -> bool:
        """Atualiza uma categoria existente."""
        df = self.get_all()
        if df.empty or ColunasCategorias.NOME not in df.columns:
            return False
            
        # Encontra o índice da linha
        mask = df[ColunasCategorias.NOME].astype(str).str.lower() == old_name.lower()
        if not mask.any():
            return False # Não encontrado
            
        # Atualiza os valores
        idx = df.index[mask][0]
        
        # Se mudou de nome, checa duplicata
        if new_name.lower() != old_name.lower():
            exists = df[ColunasCategorias.NOME].astype(str).str.lower() == new_name.lower()
            if exists.any():
                logger.warning(f"Não pode renomear '{old_name}' para '{new_name}': já existe.")
                return False
                
        df.at[idx, ColunasCategorias.NOME] = new_name
        df.at[idx, ColunasCategorias.TIPO] = tipo
        df.at[idx, ColunasCategorias.ICONE] = icone
        df.at[idx, ColunasCategorias.TAGS] = tags
        
    def get_all_category_names(self) -> list[str]:
        """Retorna apenas a lista de nomes das categorias."""
        df = self.get_all()
        if df.empty or ColunasCategorias.NOME not in df.columns:
            return []
        
        # Filtrar valores nulos ou vazios e garantir string
        categories = df[ColunasCategorias.NOME].dropna().astype(str).tolist()
        return [c.strip() for c in categories if c.strip()]
