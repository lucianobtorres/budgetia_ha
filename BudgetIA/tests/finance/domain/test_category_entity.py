import pytest

from finance.domain.models.category import Category


def test_category_creation_valid():
    """Testa criação de categoria válida."""
    c = Category(name=" Alimentação ", type="Despesa", icon="🍔")
    assert c.name == "Alimentação"  # Deve limpar espaços
    assert c.type == "Despesa"
    assert c.icon == "🍔"


def test_category_invalid_type():
    """Testa se rejeita tipos inválidos."""
    with pytest.raises(ValueError, match="Tipo de categoria inválido"):
        Category(name="Salário", type="Investimento")


def test_category_equality():
    """Testa comparação de categorias."""
    c1 = Category(name="Lazer", type="Despesa")
    c2 = Category(name="lazer", type="Despesa")
    assert c1 == c2  # Comparação deve ser case-insensitive
