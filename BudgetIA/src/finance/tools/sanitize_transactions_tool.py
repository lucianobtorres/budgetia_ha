# src/finance/tools/sanitize_transactions_tool.py

from pydantic import BaseModel, Field

from core.base_tool import BaseTool


class SanitizeTransactionsInput(BaseModel):
    confirm: bool = Field(
        ..., description="Confirmação para iniciar a faxina de transações genéricas."
    )


class SanitizeTransactionsTool(BaseTool):
    name: str = "sanitize_transactions"
    description: str = (
        "Organiza e categoriza automaticamente transações que estão como 'Outros' ou 'Desconhecido'. "
        "Útil para manter a planilha limpa e as categorias precisas."
    )
    label: str = "Faxineiro de Dados"
    args_schema: type[BaseModel] = SanitizeTransactionsInput

    def _run(self, confirm: bool) -> str:
        if not confirm:
            return "Operação cancelada pelo usuário."

        try:
            # O PlanilhaManager tem o método sanitize_transactions_use_case ou similar exposto
            # Se não, chamamos o use case diretamente.
            # No factory vimos que ele é injetado no manager.
            result = self.plan_manager.sanitize_transactions()

            processed = result.get("processed_count", 0)
            updated = result.get("updated_count", 0)

            if processed == 0:
                return "Não encontrei nenhuma transação precisando de faxina no momento. Tudo limpo! ✨"

            return (
                f"Faxina concluída! ✅\n"
                f"- Transações analisadas: {processed}\n"
                f"- Categorias corrigidas: {updated}\n"
                f"Sua planilha está agora mais organizada."
            )
        except Exception as e:
            return f"Ocorreu um erro durante a faxina: {str(e)}"
