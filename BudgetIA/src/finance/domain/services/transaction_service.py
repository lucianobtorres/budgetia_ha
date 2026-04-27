from typing import Any

from dateutil.relativedelta import relativedelta

from ..models.transaction import Transaction
from ..repositories.transaction_repository import ITransactionRepository


class TransactionDomainService:
    """
    Serviço de Domínio para Transações.
    Contém a lógica de negócio que não pertence a uma única entidade,
    como a criação de parcelas ou cálculos de resumo.
    """

    def __init__(self, repository: ITransactionRepository):
        self._repository = repository

    def add_transaction(self, data: dict[str, Any]) -> Transaction | list[Transaction]:
        """
        Cria uma transação no sistema. Se 'parcelas' for informado,
        gera a série de transações futuras.
        """
        parcelas = int(data.get("parcelas", 1))

        if parcelas <= 1:
            # Transação única
            tx_data = data.copy()
            tx_data.pop("parcelas", None)
            tx = Transaction(**tx_data)
            return self._repository.save(tx)

        # Gerar Parcelas
        transactions: list[Transaction] = []
        base_date = data["data"]

        # Normalização de data se vier como string
        if isinstance(base_date, str):
            from datetime import datetime

            base_date = datetime.strptime(base_date, "%Y-%m-%d").date()

        for i in range(parcelas):
            tx_payload = data.copy()
            tx_payload.pop("parcelas", None)

            # Ajusta data e descrição
            current_date = base_date + relativedelta(months=+i)
            tx_payload["data"] = current_date

            if parcelas > 1:
                tx_payload["descricao"] = f"{data['descricao']} ({i + 1}/{parcelas})"

            transactions.append(Transaction(**tx_payload))

        self._repository.save_batch(transactions)
        return transactions

    def get_summary(
        self, month: int | None = None, year: int | None = None
    ) -> dict[str, float]:
        """Calcula resumo financeiro baseado nas entidades do repositório."""
        transactions = self._repository.list_all(month=month, year=year)

        receitas = sum(tx.valor for tx in transactions if not tx.eh_despesa)
        despesas = sum(tx.valor for tx in transactions if tx.eh_despesa)

        return {
            "total_receitas": receitas,
            "total_despesas": despesas,
            "saldo": receitas - despesas,
        }

    def delete_transaction(self, transaction_id: int) -> bool:
        """Deleta uma transação pelo ID."""
        return self._repository.delete(transaction_id)

    def update_transaction(self, transaction_id: int, data: dict[str, Any]) -> bool:
        """Atualiza uma transação existente."""
        tx = self._repository.get_by_id(transaction_id)
        if not tx:
            return False

        # Atualiza os campos da entidade (Pydantic valida automaticamente)
        updated_data = tx.model_dump()
        updated_data.update(data)
        updated_tx = Transaction(**updated_data)

        self._repository.save(updated_tx)
        return True

    def get_expenses_by_category(self, top_n: int = 5) -> dict[str, float]:
        """Retorna as top N categorias de despesa."""
        transactions = self._repository.list_all()
        expenses = [tx for tx in transactions if tx.eh_despesa]

        sums: dict[str, float] = {}
        for tx in expenses:
            sums[tx.categoria] = sums.get(tx.categoria, 0.0) + tx.valor

        # Ordena por valor e pega os top N
        sorted_sums = sorted(sums.items(), key=lambda item: item[1], reverse=True)
        return dict(sorted_sums[:top_n])

    def update_category_names(self, old_name: str, new_name: str) -> int:
        """
        Atualiza em cascata o nome de uma categoria em todas as transações.
        """
        transactions = self._repository.list_all()
        count = 0
        for tx in transactions:
            if tx.categoria == old_name:
                tx.categoria = new_name
                self._repository.save(tx)
                count += 1
        return count
