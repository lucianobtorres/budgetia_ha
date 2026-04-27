import pandas as pd

import config
from finance.domain.models.profile import UserProfile
from finance.domain.repositories.profile_repository import IProfileRepository
from finance.infrastructure.persistence.data_context import FinancialDataContext


class ExcelProfileRepository(IProfileRepository):
    """
    Implementação concreta do repositório de perfil para Excel.
    """

    def __init__(self, context: FinancialDataContext):
        self._context = context
        self._sheet_name = config.NomesAbas.PERFIL_FINANCEIRO

    def get_profile(self) -> UserProfile:
        """Carrega os dados da aba de perfil e converte para Entidade."""
        df = self._context.get_dataframe(self._sheet_name)
        if df.empty:
            return UserProfile()

        records = df.to_dict(orient="records")
        return UserProfile.from_excel_list(records)

    def save_profile(self, profile: UserProfile) -> None:
        """Converte Entidade para lista de registros e salva no DataFrame."""
        records = profile.to_excel_list()
        df = pd.DataFrame(records)

        # Garante que as colunas estejam na ordem correta conforme o layout
        colunas = config.LAYOUT_PLANILHA[self._sheet_name]
        for col in colunas:
            if col not in df.columns:
                df[col] = None

        df = df[colunas]

        self._context.update_dataframe(self._sheet_name, df)

    def ensure_fields(self, fields: list[str]) -> None:
        """Garante que os campos existam na aba de perfil."""
        from config import ColunasPerfil

        df = self._context.get_dataframe(self._sheet_name)

        changed = False
        current_fields = (
            df[ColunasPerfil.CAMPO].tolist()
            if not df.empty and ColunasPerfil.CAMPO in df.columns
            else []
        )

        new_rows = []
        for field in fields:
            if field not in current_fields:
                new_rows.append(
                    {
                        ColunasPerfil.CAMPO: field,
                        ColunasPerfil.VALOR: None,
                        ColunasPerfil.OBS: "Auto-gerado",
                    }
                )
                changed = True

        if changed:
            df_new = pd.DataFrame(new_rows)
            df = pd.concat([df, df_new], ignore_index=True)
            self._context.update_dataframe(self._sheet_name, df)
