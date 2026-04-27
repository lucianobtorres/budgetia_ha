from pydantic import BaseModel


class CategorySchema(BaseModel):
    """Esquema para uma categoria de transação."""

    name: str
    type: str
    icon: str = ""
    tags: str = ""


class CategoryCreate(BaseModel):
    """Esquema para criação/atualização de categoria."""

    name: str
    type: str = "Despesa"
    icon: str = ""
    tags: str = ""
