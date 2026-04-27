from unittest.mock import MagicMock

import pytest

from finance.domain.models.category import Category
from finance.domain.services.category_service import CategoryDomainService


@pytest.fixture
def mock_repo():
    return MagicMock()


def test_ensure_category_exists_creates_new(mock_repo):
    """Testa se cria a categoria quando ela não existe."""
    mock_repo.get_by_name.return_value = None

    service = CategoryDomainService(mock_repo)
    cat = service.ensure_category_exists("Farmácia", default_type="Despesa")

    assert cat.name == "Farmácia"
    mock_repo.save.assert_called_once()


def test_ensure_category_exists_returns_existing(mock_repo):
    """Testa se retorna a existente sem criar nova."""
    existing = Category(name="Saúde", type="Despesa")
    mock_repo.get_by_name.return_value = existing

    service = CategoryDomainService(mock_repo)
    cat = service.ensure_category_exists("Saúde")

    assert cat == existing
    mock_repo.save.assert_not_called()


def test_add_category_prevents_duplicate(mock_repo):
    """Testa se impede adição de duplicatas."""
    mock_repo.get_by_name.return_value = Category(name="Lazer", type="Despesa")

    service = CategoryDomainService(mock_repo)
    with pytest.raises(ValueError, match="já existe"):
        service.add_category("Lazer")


def test_update_category_renames_correctly(mock_repo):
    """Testa renomeação com deleção da antiga."""
    mock_repo.get_by_name.side_effect = [
        Category(name="Old", type="Despesa"),  # Primeira chamada: existe a antiga
        None,  # Segunda chamada (check new_name): não existe a nova
    ]

    service = CategoryDomainService(mock_repo)
    service.update_category("Old", "New", type="Despesa", icon=None, tags=None)

    mock_repo.delete.assert_called_once_with("Old")
    mock_repo.save.assert_called_once()
    saved = mock_repo.save.call_args[0][0]
    assert saved.name == "New"
