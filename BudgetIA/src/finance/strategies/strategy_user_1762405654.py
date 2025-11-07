from typing import Any

import pandas as pd

import config

from .base_strategy import BaseMappingStrategy


class CustomStrategy(BaseMappingStrategy):
    """
    Estratégia personalizada para mapear a planilha do usuário
    com o formato 'Meu Extrato' para o formato interno do sistema.
    """

    def __init__(
        self, layout_config: dict[str, Any], mapeamento: dict[str, Any] | None = None
    ):
        # Define o mapeamento da aba de transações do usuário para o nome interno.
        # Isso será usado pelo método get_sheet_name_to_save da classe base.
        custom_mapeamento = {"aba_transacoes": "Meu Extrato"}
        if mapeamento:
            custom_mapeamento.update(mapeamento)  # Mescla com mapeamentos adicionais, se houver

        super().__init__(layout_config, custom_mapeamento)
        print("LOG: Estratégia 'CustomStrategy' selecionada.")

    def map_transactions(self, df_bruto: pd.DataFrame) -> pd.DataFrame:
        """
        Recebe um DataFrame bruto da aba 'Meu Extrato' do usuário
        e o transforma no DataFrame padrão de transações do nosso sistema.
        """
        df_interno = pd.DataFrame()

        # Mapeamento direto das colunas do usuário para as colunas internas
        df_interno['Data'] = df_bruto['Data da Operação']
        df_interno['Descricao'] = df_bruto['Detalhes']
        df_interno['Valor'] = df_bruto['Valor (R$)']
        df_interno['Categoria'] = df_bruto['Minha Categoria']

        # Deriva a coluna 'Tipo (Receita/Despesa)' com base no 'Valor (R$)'
        df_interno['Tipo (Receita/Despesa)'] = df_bruto['Valor (R$)'].apply(
            lambda x: 'Receita' if x >= 0 else 'Despesa'
        )

        # Define valores padrão ou placeholders para colunas internas não presentes
        # no arquivo do usuário. 'ID Transacao' será gerado pelo sistema,
        # 'Status' pode ter um valor inicial padrão.
        df_interno['ID Transacao'] = pd.NA  # Será preenchido pelo sistema
        df_interno['Status'] = 'Concluído'  # Valor padrão inicial

        # Garante que todas as colunas do layout interno existam e estejam na ordem correta.
        # Preenche com pd.NA se alguma coluna interna não foi mapeada ou derivada.
        for col in self.colunas_transacoes:
            if col not in df_interno.columns:
                df_interno[col] = pd.NA
        
        return df_interno[self.colunas_transacoes]

    def unmap_transactions(self, df_interno: pd.DataFrame) -> pd.DataFrame:
        """
        Recebe o DataFrame de transações no formato INTERNO do sistema
        e o "traduz de volta" para o formato ORIGINAL do usuário ('Meu Extrato').
        """
        df_usuario = pd.DataFrame()

        # Mapeamento das colunas internas de volta para as colunas do usuário
        df_usuario['Data da Operação'] = df_interno['Data']
        df_usuario['Detalhes'] = df_interno['Descricao']
        df_usuario['Valor (R$)'] = df_interno['Valor']
        df_usuario['Minha Categoria'] = df_interno['Categoria']

        # Retorna apenas as colunas do usuário na ordem esperada,
        # ignorando colunas internas como 'ID Transacao', 'Tipo (Receita/Despesa)', 'Status'.
        return df_usuario[['Data da Operação', 'Detalhes', 'Valor (R$)', 'Minha Categoria']]

    # O método get_sheet_name_to_save não precisa ser sobrescrito,
    # pois a classe base já utiliza self.mapeamento.get("aba_transacoes", ...)
    # e nós definimos "aba_transacoes": "Meu Extrato" no __init__.
    # Isso garante que a aba de transações seja salva com o nome 'Meu Extrato'.