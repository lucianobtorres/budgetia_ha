from ..models.category import Category
from ..repositories.category_repository import ICategoryRepository


class CategoryDomainService:
    """
    Serviço de Domínio para Categorias.
    Centraliza a lógica de validação e busca de categorias.
    """

    def __init__(self, repository: ICategoryRepository):
        self._repository = repository

    def list_all(self) -> list[Category]:
        """Retorna todas as categorias."""
        return self._repository.list_all()

    def get_by_name(self, name: str) -> Category | None:
        """Busca uma categoria pelo nome."""
        return self._repository.get_by_name(name)

    def add_category(
        self,
        name: str,
        type: str = "Despesa",
        icon: str | None = None,
        tags: str | None = None,
    ) -> Category:
        """Adiciona uma nova categoria com validação de duplicidade."""
        existing = self._repository.get_by_name(name)
        if existing:
            raise ValueError(f"A categoria '{name}' já existe.")

        new_cat = Category(name=name, type=type, icon=icon, tags=tags)
        return self._repository.save(new_cat)

    def ensure_category_exists(
        self, name: str, default_type: str = "Despesa"
    ) -> Category:
        """
        Garante que a categoria existe. Se não existir, cria uma nova.
        Útil para importação de transações.
        """
        category = self._repository.get_by_name(name)
        if not category:
            category = Category(name=name, type=default_type)
            self._repository.save(category)
        return category

    def delete_category(self, name: str) -> bool:
        """Remove uma categoria."""
        return self._repository.delete(name)

    def update_category(
        self,
        old_name: str,
        new_name: str,
        type: str,
        icon: str | None,
        tags: str | None,
    ) -> Category:
        """Atualiza uma categoria existente."""
        existing = self._repository.get_by_name(old_name)
        if not existing:
            raise ValueError(f"Categoria '{old_name}' não encontrada.")

        # Se mudou o nome, verifica se o novo nome já existe
        if old_name.lower() != new_name.lower():
            if self._repository.get_by_name(new_name):
                raise ValueError(
                    f"Não é possível renomear para '{new_name}': categoria já existe."
                )

            # Remove a antiga se o nome mudou (já que o nome é a chave no ExcelRepository)
            self._repository.delete(old_name)

        updated_cat = Category(name=new_name, type=type, icon=icon, tags=tags)
        return self._repository.save(updated_cat)

    def rename_category(self, old_name: str, new_name: str) -> bool:
        """Renomeia uma categoria preservando seus outros atributos."""
        existing = self._repository.get_by_name(old_name)
        if not existing:
            return False

        if old_name.lower() != new_name.lower():
            if self._repository.get_by_name(new_name):
                raise ValueError(f"Nome '{new_name}' já está em uso.")
            self._repository.delete(old_name)

        existing.name = new_name
        self._repository.save(existing)
        return True

    def ensure_default_categories(self) -> None:
        """
        Garante que um conjunto básico de categorias exista no sistema.
        Útil para novas instalações ou migrações.
        """
        defaults = [
            ("Alimentação", "Despesa", "utensils"),
            ("Transporte", "Despesa", "car"),
            ("Moradia", "Despesa", "home"),
            ("Lazer", "Despesa", "gamepad"),
            ("Saúde", "Despesa", "stethoscope"),
            ("Educação", "Despesa", "graduation-cap"),
            ("Salário", "Receita", "money-bill-wave"),
            ("Investimentos", "Receita", "chart-line"),
            ("Outros", "Despesa", "tag"),
        ]

        existing_names = {c.name.lower() for c in self.list_all()}

        for name, type, icon in defaults:
            if name.lower() not in existing_names:
                new_cat = Category(name=name, type=type, icon=icon)
                self._repository.save(new_cat)
