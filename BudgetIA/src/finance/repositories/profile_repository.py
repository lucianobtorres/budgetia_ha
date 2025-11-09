# src/finance/repositories/profile_repository.py
from typing import Any

import pandas as pd

import config

from .data_context import FinancialDataContext


class ProfileRepository:
    """
    Repositório para gerenciar a lógica de acesso e manipulação
    dos dados do Perfil Financeiro do usuário.
    """

    def __init__(self, context: FinancialDataContext) -> None:
        """
        Inicializa o repositório.

        Args:
            context: A Unidade de Trabalho (DataContext).
        """
        self._context = context
        self._aba_nome = config.NomesAbas.PERFIL_FINANCEIRO

    def get_profile_dataframe(self) -> pd.DataFrame:
        """Retorna o DataFrame completo do perfil."""
        return self._context.get_dataframe(self._aba_nome)

    def save_profile_field(self, campo: str, valor: Any) -> str:
        """
        Adiciona ou atualiza um item na aba 'Perfil Financeiro'.
        Usa "Campo" como chave única e salva imediatamente.
        """
        df_perfil = self.get_profile_dataframe()

        if "Campo" not in df_perfil.columns:
            df_perfil = pd.DataFrame(columns=config.LAYOUT_PLANILHA[self._aba_nome])
            print(f"AVISO (Repo): Aba '{self._aba_nome}' recriada em memória.")

        campo_limpo = str(campo).strip().lower()
        idx_existente = df_perfil[
            df_perfil["Campo"].astype(str).str.strip().str.lower() == campo_limpo
        ].index

        if not idx_existente.empty:
            idx = idx_existente[0]
            df_perfil.loc[idx, "Valor"] = valor
            mensagem = f"Perfil atualizado: '{campo}' definido como '{valor}'."
        else:
            novo_dado = pd.DataFrame(
                [{"Campo": campo, "Valor": valor, "Observações": ""}],
                columns=config.LAYOUT_PLANILHA[self._aba_nome],
            )
            df_perfil = pd.concat([df_perfil, novo_dado], ignore_index=True)
            mensagem = f"Perfil criado: '{campo}' definido como '{valor}'."

        self._context.update_dataframe(self._aba_nome, df_perfil)
        self._context.save()  # Perfil é crítico, salva imediatamente
        print(f"LOG (Repo): {mensagem}")
        return mensagem

    def get_profile_as_text(self) -> str:
        """
        Lê a aba 'Perfil Financeiro' e formata os dados como uma string
        de contexto para ser injetada no prompt da IA.
        """
        try:
            df_perfil = self.get_profile_dataframe()
            if df_perfil.empty or "Campo" not in df_perfil.columns:
                return "O perfil do usuário ainda não foi preenchido."

            if "Valor" not in df_perfil.columns:
                return "O perfil do usuário está mal formatado (Falta coluna 'Valor')."

            perfil_dict_df = df_perfil.dropna(subset=["Valor"])
            perfil_dict_df = perfil_dict_df[perfil_dict_df["Valor"] != ""]

            perfil_dict_df = perfil_dict_df.drop_duplicates(
                subset=["Campo"], keep="last"
            )

            perfil_dict = pd.Series(
                perfil_dict_df.Valor.values, index=perfil_dict_df.Campo
            ).to_dict()

            if not perfil_dict:
                return "O perfil do usuário ainda não foi preenchido."

            contexto_str = (
                "--- CONTEXTO DO PERFIL DO USUÁRIO (NÃO REPETIR/PERGUNTAR) ---\n"
            )
            for campo, valor in perfil_dict.items():
                contexto_str += f"- {campo}: {valor}\n"
            contexto_str += "--- FIM DO CONTEXTO ---"

            return contexto_str.strip()

        except Exception as e:
            print(f"ERRO (Repo) ao ler perfil como texto: {e}")
            return "Não foi possível carregar o perfil do usuário."
