# src/finance/financial_rules.py


class FinancialRules:
    """
    Define as regras de ouro financeiras padronizadas e suas categorias.
    Esta classe é o ponto de extensibilidade para adicionar novas regras.
    """

    # Mapeamento de categorias da Planilha Mestra para grupos de regras
    # A IA será instruída a usar categorias da planilha que se encaixem nestes grupos.
    # Isto é uma simplificacao da lógica que o mentor IA precisa fazer.
    CATEGORIAS_MAPEAMENTO: dict[str, list[str]] = {
        "ESSENCIAIS": [
            "Aluguel",
            "Moradia",
            "Alimentação",
            "Contas",
            "Saúde",
            "Transporte Fixo",
        ],
        "INVESTIMENTO_POUPANCA": ["Poupança", "Reserva", "Investimentos"],
        "DESEJOS_LAZER": ["Lazer", "Viagens", "Hobbies", "Restaurantes", "Compras"],
        "DIVIDAS_EDUCACAO": ["Dívidas", "Educação", "Juros", "Parcelas", "Cartão"],
    }

    REGRAS: dict[str, dict[str, float]] = {
        # Regra: 50% Essenciais / 30% Desejos/Lazer / 20% Investimentos/Dívidas
        "50/30/20": {
            "ESSENCIAIS": 0.50,
            "DESEJOS_LAZER": 0.30,
            "INVESTIMENTO_DIVIDA": 0.20,
        },
        # Regra: 20/10/60/10 (Essenciais/Investimento/Lazer/Dívida)
        # Adaptamos para que a soma seja 1.0 (100% da receita)
        "20/10/60/10": {
            "ESSENCIAIS": 0.60,  # Essenciais: 60%
            "INVESTIMENTO_POUPANCA": 0.20,  # Investimento: 20%
            "DIVIDAS_EDUCACAO": 0.10,  # Dívidas/Educação: 10%
            "DESEJOS_LAZER": 0.10,  # Lazer/Desejos: 10%
        },
    }

    @classmethod
    def get_available_rules(cls) -> list[str]:
        """Retorna os nomes de todas as regras disponíveis."""
        return list(cls.REGRAS.keys())

    @classmethod
    def get_target_percentages(cls, rule_name: str) -> dict[str, float]:
        """Retorna as porcentagens alvo para uma regra específica."""
        return cls.REGRAS.get(rule_name, {})

    @classmethod
    def get_category_mapping(cls) -> dict[str, list[str]]:
        """Retorna o mapeamento de categorias."""
        return cls.CATEGORIAS_MAPEAMENTO
