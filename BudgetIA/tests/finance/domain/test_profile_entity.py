from finance.domain.models.profile import UserProfile


def test_profile_from_excel_list_with_currency_conversion():
    """Testa a criação da entidade a partir de dados 'sujos' do Excel."""
    records = [
        {"Campo": "Renda Mensal Média", "Valor": "R$ 5.000,00"},
        {"Campo": "Principal Objetivo", "Valor": "Aposentadoria precoce"},
        {"Campo": "Tolerância a Risco", "Valor": "Moderado"},
        {"Campo": "Idade", "Valor": "30"},  # Campo dinâmico
    ]

    profile = UserProfile.from_excel_list(records)

    assert profile.renda_mensal == 5000.0
    assert profile.objetivo_principal == "Aposentadoria precoce"
    assert profile.tolerancia_risco == "Moderado"
    assert profile.outros_campos["Idade"] == "30"


def test_profile_to_excel_list_preserves_structure():
    """Testa a exportação da entidade para o formato da planilha."""
    profile = UserProfile(
        renda_mensal=12500.50,
        objetivo_principal="Comprar casa",
        outros_campos={"Profissão": "Engenheiro"},
    )

    records = profile.to_excel_list()

    # Verifica se os nomes de colunas do Excel foram usados
    mapping = {r["Campo"]: r["Valor"] for r in records}

    assert mapping["Renda Mensal Média"] == 12500.50
    assert mapping["Principal Objetivo"] == "Comprar casa"
    assert mapping["Profissão"] == "Engenheiro"


def test_profile_empty_initialization():
    """Garante que um perfil vazio não quebre o sistema."""
    profile = UserProfile()
    assert profile.renda_mensal is None
    assert profile.outros_campos == {}

    records = profile.to_excel_list()
    assert len(records) == 0
