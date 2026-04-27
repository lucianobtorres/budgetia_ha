from typing import Any

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """
    Entidade de Domínio representando o Perfil Financeiro do Usuário.
    Mapeia os campos da planilha para uma estrutura tipada.
    """

    # Campos Essenciais (Mapeados diretamente da planilha)
    renda_mensal: float | None = Field(None, description="Renda Mensal Média")
    objetivo_principal: str | None = Field(None, description="Principal Objetivo")
    tolerancia_risco: str | None = Field(None, description="Tolerância a Risco")

    # Dicionário para campos dinâmicos/adicionais
    outros_campos: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_excel_list(cls, records: list[dict]) -> "UserProfile":
        """
        Fábrica para criar a entidade a partir da lista de registros do Excel.
        """
        data = {}
        outros = {}

        # Mapeamento de nomes de colunas do Excel para campos do modelo
        mapping = {
            "Renda Mensal Média": "renda_mensal",
            "Principal Objetivo": "objetivo_principal",
            "Tolerância a Risco": "tolerancia_risco",
        }

        import math

        for rec in records:
            campo = rec.get("Campo")
            valor = rec.get("Valor")

            # Sanitização para valores NaN do Pandas/Excel
            if isinstance(valor, float) and math.isnan(valor):
                valor = None

            if campo in mapping:
                # Tenta converter para float se for renda
                if mapping[campo] == "renda_mensal" and valor:
                    try:
                        valor = float(
                            str(valor)
                            .replace("R$", "")
                            .replace(".", "")
                            .replace(",", ".")
                            .strip()
                        )
                    except:  # noqa: E722
                        pass
                data[mapping[campo]] = valor
            else:
                outros[campo] = valor

        return cls(**data, outros_campos=outros)

    def to_excel_list(self) -> list[dict]:
        """
        Converte a entidade de volta para o formato de lista do Excel.
        """
        # Mapeamento reverso
        mapping = {
            "renda_mensal": "Renda Mensal Média",
            "objetivo_principal": "Principal Objetivo",
            "tolerancia_risco": "Tolerância a Risco",
        }

        records = []
        # Adiciona campos mapeados
        for field, excel_name in mapping.items():
            val = getattr(self, field)
            if val is not None:
                records.append({"Campo": excel_name, "Valor": val, "Observações": ""})

        # Adiciona campos dinâmicos
        for campo, valor in self.outros_campos.items():
            records.append({"Campo": campo, "Valor": valor, "Observações": ""})

        return records
