# src/finance/repositories/transaction_repository.py
from typing import Any
import pandas as pd

import config
from config import ColunasTransacoes

# Imports relativos para "subir" um nível
from ..services.transaction_service import TransactionService
from .data_context import FinancialDataContext
from core.logger import get_logger

logger = get_logger("TransactionRepo")


import unicodedata

class TransactionRepository:
    """
    Repositório para gerenciar TODA a lógica de
    acesso e manipulação de Transações.
    """

    def __init__(
        self, context: FinancialDataContext, transaction_service: TransactionService
    ) -> None:
        """
        Inicializa o repositório.

        Args:
            context: A Unidade de Trabalho (DataContext) que gerencia os DataFrames.
            calculator: O especialista em cálculos financeiros puros.
        """
        self._context = context
        self._transaction_service = transaction_service
        self._aba_nome = config.NomesAbas.TRANSACOES

    def get_all_transactions(self) -> pd.DataFrame:
        """Retorna o DataFrame completo de transações."""
        return self._context.get_dataframe(sheet_name=self._aba_nome)

    def _resolve_category(self, df: pd.DataFrame, input_category: str) -> str:
        """
        Tenta encontrar uma categoria existente que corresponda à entrada
        ignorando case e acentos. Retorna a existente se achar,
        ou a entrada original se não.
        """
        if not input_category or not isinstance(input_category, str):
            return input_category
            
        if ColunasTransacoes.CATEGORIA not in df.columns:
            return input_category

        existing_categories = df[ColunasTransacoes.CATEGORIA].dropna().unique()
        
        def normalize(text: str) -> str:
            return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII').lower().strip()
            
        normalized_input = normalize(input_category)
        
        for existing in existing_categories:
            if not isinstance(existing, str):
                continue
            if normalize(existing) == normalized_input:
                return existing # Retorna a versão "oficial" (com acentos)
                
        return input_category

    def add_batch(self, transactions_data: list[dict[str, Any]]) -> int:
        """
        Adiciona múltiplas transações de uma vez (Performance O(1) concat).
        Espera lista de dicts com chaves: data, tipo, categoria, descricao, valor, status, parcelas.
        """
        if not transactions_data:
            return 0
            
        df_current = self.get_all_transactions()
        current_max_id = 0
        if not df_current.empty and ColunasTransacoes.ID in df_current.columns:
             current_max_id = pd.to_numeric(df_current[ColunasTransacoes.ID], errors='coerce').fillna(0).max()
             
        new_rows = []
        from dateutil.relativedelta import relativedelta
        
        for tx in transactions_data:
            parcelas = int(tx.get("parcelas", 1))
            base_date = pd.to_datetime(tx["data"], dayfirst=False)
            resolved_category = self._resolve_category(df_current, tx["categoria"])
            
            for i in range(parcelas):
                current_max_id += 1
                
                final_desc = str(tx["descricao"])
                current_date = base_date
                current_val = float(tx["valor"])
                
                if parcelas > 1:
                    current_date = base_date + relativedelta(months=+i)
                    final_desc = f"{final_desc} ({i+1}/{parcelas})"
                
                new_rows.append({
                    ColunasTransacoes.ID: int(current_max_id),
                    ColunasTransacoes.DATA: current_date,
                    ColunasTransacoes.TIPO: tx["tipo"],
                    ColunasTransacoes.CATEGORIA: resolved_category,
                    ColunasTransacoes.DESCRICAO: final_desc,
                    ColunasTransacoes.VALOR: current_val,
                    ColunasTransacoes.STATUS: tx.get("status", "Concluído"),
                })
        
        if not new_rows:
            return 0
            
        df_new = pd.DataFrame(new_rows, columns=config.LAYOUT_PLANILHA[self._aba_nome])
        df_atualizado = pd.concat([df_current, df_new], ignore_index=True)
        self._context.update_dataframe(self._aba_nome, df_atualizado)
        logger.info(f"Adicionadas {len(new_rows)} transações em lote.")
        return len(new_rows)
        
    def add_transaction(
        self,
        data: str,
        tipo: str,
        category: str,
        descricao: str,
        valor: float,
        status: str = "Concluído",
        parcelas: int = 1, 
    ) -> None:
        """wrapper around add_batch for single item"""
        self.add_batch([{
            "data": data,
            "tipo": tipo,
            "categoria": category,
            "descricao": descricao,
            "valor": valor,
            "status": status,
            "parcelas": parcelas
        }])

    def delete_transaction(self, transaction_id: int) -> bool:
        """Exclui uma transação pelo ID."""
        df = self.get_all_transactions()
        if ColunasTransacoes.ID not in df.columns:
            return False
        
        # Ensure robust numeric comparison for ID
        ids = pd.to_numeric(df[ColunasTransacoes.ID], errors='coerce').fillna(-1).astype(int)
        
        if transaction_id not in ids.values:
             return False

        # Keep rows where ID is NOT the target
        df_novo = df[ids != transaction_id]
            
        self._context.update_dataframe(self._aba_nome, df_novo)
        return True

    def update_transaction(self, transaction_id: int, novos_dados: dict[str, Any]) -> bool:
        """Atualiza uma transação existente pelo ID."""
        df = self.get_all_transactions()
        if ColunasTransacoes.ID not in df.columns:
            return False
            
        # Robust ID matching
        ids = pd.to_numeric(df[ColunasTransacoes.ID], errors='coerce').fillna(-1).astype(int)
        mask = ids == transaction_id
        
        if not mask.any():
            return False
            
        # Atualiza os campos fornecidos
        # Mapeia chaves do dict (que vêm do Pydantic) para colunas do DataFrame
        # Ex: "descricao" -> "Descricao"
        
        # Mapeamento de chaves amigáveis (do input) para colunas reais
        field_map = {
            "data": ColunasTransacoes.DATA,
            "tipo": ColunasTransacoes.TIPO,
            "categoria": ColunasTransacoes.CATEGORIA,
            "descricao": ColunasTransacoes.DESCRICAO,
            "valor": ColunasTransacoes.VALOR,
            "status": ColunasTransacoes.STATUS
        }
        
        # Check for category update to normalize
        if "categoria" in novos_dados:
            novos_dados["categoria"] = self._resolve_category(df, novos_dados["categoria"])

        idx = df.index[mask][0]
        
        for field, valor in novos_dados.items():
            # Determina o nome real da coluna
            col_name = field
            if field in field_map:
                col_name = field_map[field]
            
            if col_name in df.columns and col_name != ColunasTransacoes.ID:
                if col_name == ColunasTransacoes.DATA:
                     df.at[idx, col_name] = pd.to_datetime(valor)
                elif col_name == ColunasTransacoes.VALOR:
                     # Garante float
                     try:
                        df.at[idx, col_name] = float(valor)
                     except:
                        df.at[idx, col_name] = valor
                else:
                     df.at[idx, col_name] = valor
                     
        self._context.update_dataframe(self._aba_nome, df)
        return True

    def update_category_name(self, old_category: str, new_category: str) -> int:
        """
        Atualiza o nome da categoria em todas as transações que a utilizam.
        Retorna o número de registros atualizados.
        """
        if not old_category or not new_category:
            return 0
            
        df = self.get_all_transactions()
        if df.empty or ColunasTransacoes.CATEGORIA not in df.columns:
            return 0
            
        # Função auxiliar de normalização (mesma usada em _resolve_category)
        def normalize(text: Any) -> str:
            if not isinstance(text, str):
                return str(text).lower().strip()
            return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII').lower().strip()

        target = normalize(old_category)
        
        # Cria mascara aplicando normalização em cada valor
        # Nota: Idealmente faríamos vetorizado, mas apply é mais seguro para unicode/types mistos
        mask = df[ColunasTransacoes.CATEGORIA].apply(lambda x: normalize(x) == target)
        
        count = mask.sum()
        
        if count == 0:
            logger.warning(f"Tentativa de renomear '{old_category}' falhou: nenhuma transação encontrada (Match strict falhou).")
            return 0
            
        # Atualiza
        df.loc[mask, ColunasTransacoes.CATEGORIA] = new_category
        self._context.update_dataframe(self._aba_nome, df)
        
        if count == 0:
            logger.warning(f"Tentativa de renomear '{old_category}' falhou: nenhuma transação encontrada (Match strict falhou).")
            return 0
            
        # Atualiza
        df.loc[mask, ColunasTransacoes.CATEGORIA] = new_category
        self._context.update_dataframe(self._aba_nome, df)
        
        logger.info(f"Categoria '{old_category}' renomeada para '{new_category}' em {count} transações.")
        return int(count)

    def count_category_usage(self, category_name: str) -> int:
        """Retorna quantas transações usam esta categoria."""
        df = self.get_all_transactions()
        if df.empty or ColunasTransacoes.CATEGORIA not in df.columns:
            return 0
            
        def normalize(text):
            if not isinstance(text, str): return str(text).lower().strip()
            return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII').lower().strip()
            
        target = normalize(category_name)
        mask = df[ColunasTransacoes.CATEGORIA].apply(lambda x: normalize(x) == target)
        return int(mask.sum())

    def get_summary(self) -> dict[str, float]:
        """Delega o cálculo do resumo para o FinancialCalculator."""
        df_transacoes = self.get_all_transactions()
        return self._transaction_service.get_summary(df_transacoes)

    def get_expenses_by_category(self, top_n: int = 5) -> pd.Series:
        """Delega o cálculo das despesas por categoria para o FinancialCalculator."""
        df_transacoes = self.get_all_transactions()
        return self._transaction_service.get_expenses_by_category(df_transacoes, top_n)

    def save_transactions(self, df: pd.DataFrame) -> None:
        """Salva o DataFrame completo de transações (Útil para atualizações em lote)."""
        self._context.update_dataframe(self._aba_nome, df)
