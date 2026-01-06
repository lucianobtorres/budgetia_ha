import pandas as pd
from typing import Any
import config
from finance.repositories.category_repository import CategoryRepository
from finance.repositories.transaction_repository import TransactionRepository
from core.logger import get_logger

logger = get_logger("CategoryService")

class CategoryService:
    """
    Serviço de domínio para Gestão de Categorias.
    Responsável por garantir que a lista de categorias esteja sempre válida
    e sicronizada com as transações legado.
    """

    def __init__(self, repo: CategoryRepository, transaction_repo: TransactionRepository) -> None:
        self.repo = repo
        self.transaction_repo = transaction_repo

    def ensure_default_categories(self) -> None:
        """
        Verifica se a aba de categorias está vazia. Se estiver,
        popula com as categorias distintas encontradas nas Transações existentes.
        Isso garante migração suave.
        """
        categories_df = self.repo.get_all()
        
        if not categories_df.empty:
            return

        logger.info("Aba de Categorias vazia. Iniciando migração automática das Transações...")
        
        transactions_df = self.transaction_repo.get_all_transactions()
        if transactions_df.empty or config.ColunasTransacoes.CATEGORIA not in transactions_df.columns:
             logger.info("Nenhuma transação encontrada para migrar.")
             return

        # Extrai categorias únicas
        unique_cats = transactions_df[config.ColunasTransacoes.CATEGORIA].dropna().unique()
        
        count = 0
        for cat_raw in unique_cats:
            cat_name = str(cat_raw).strip()
            if not cat_name: 
                continue
                
            # Infere Tipo (Receita/Despesa) olhando UMA transação
            # (Simplificado: marca como Despesa por padrão se misto, ou tenta estatística)
            # Por segurança, vamos marcar "Despesa" como default, o usuário ajusta depois.
            self.repo.add_category(
                nome=cat_name, 
                tipo=config.ValoresTipo.DESPESA,  # Default seguro (Constante)
                icone="circle",
                tags="migrado_auto"
            )
            count += 1
            
        logger.info(f"Migração Concluída: {count} categorias criadas.")
