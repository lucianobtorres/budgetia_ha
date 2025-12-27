# src/finance/utils.py
import json
from typing import Any


def _carregar_dados_exemplo(file_path: str) -> list[dict[str, Any]]:
    """Carrega as transações de exemplo do arquivo JSON."""
    try:
        with open(file_path, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
            transacoes: list[dict[str, Any]] = data.get("transacoes", [])
            return transacoes
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(
            f"AVISO: Arquivo de dados de exemplo não encontrado ou mal formatado: {file_path}. {e}"
        )
        return []
