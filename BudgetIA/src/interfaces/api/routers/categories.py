from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from core.logger import get_logger
from finance.planilha_manager import PlanilhaManager
from interfaces.api.dependencies import get_planilha_manager
from interfaces.api.schemas.categories import CategoryCreate, CategorySchema

logger = get_logger("API-Categories")

router = APIRouter(prefix="/categories", tags=["Categorias"])

# Removidos modelos inline


@router.get("/", response_model=list[CategorySchema])
def list_categories(manager: PlanilhaManager = Depends(get_planilha_manager)):
    """Retorna todas as categorias cadastradas."""
    df = manager.get_categorias()

    if df.empty:
        # Tenta popular se estiver vazia (primeiro acesso via API)
        manager.ensure_default_categories()
        df = manager.get_categorias()

    # Converte DataFrame para lista de dicionários
    try:
        # Renomeia colunas internas para o modelo da API se necessário,
        # mas aqui vamos simplificar retornando os valores diretos se baterem,
        # ou mapeando manualmente.
        # Modelo interno: Nome, Tipo (Despesa/Receita), Cor (Hex), Icone, Palavras-Chave
        from config import ColunasCategorias

        result = []
        for _, row in df.iterrows():
            result.append(
                {
                    "name": str(row.get(ColunasCategorias.NOME, "")),
                    "type": str(row.get(ColunasCategorias.TIPO, "Despesa")),
                    "icon": str(row.get(ColunasCategorias.ICONE, "")),
                    "tags": str(row.get(ColunasCategorias.TAGS, "")),
                }
            )
        return result
    except Exception as e:
        logger.error(f"Erro ao listar categorias: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao listar categorias")


@router.post("/", response_model=dict[str, str])
def create_category(
    data: CategoryCreate, manager: PlanilhaManager = Depends(get_planilha_manager)
):
    """Cria uma nova categoria."""
    try:
        success = manager.adicionar_categoria(
            nome=data.name, tipo=data.type, icone=data.icon, tags=data.tags
        )
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Categoria '{data.name}' já existe ou erro ao salvar.",
            )

        return {"message": f"Categoria '{data.name}' criada com sucesso."}
    except Exception as e:
        logger.error(f"Erro ao criar categoria: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{name}", response_model=dict[str, str])
def delete_category(
    name: str, manager: PlanilhaManager = Depends(get_planilha_manager)
) -> Any:
    """Remove uma categoria."""
    try:
        success = manager.excluir_categoria(name)
        if not success:
            raise HTTPException(
                status_code=404, detail=f"Categoria '{name}' não encontrada."
            )

        return {"message": f"Categoria '{name}' removida."}
    except Exception as e:
        logger.error(f"Erro ao deletar categoria: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{name}", response_model=dict[str, str])
def update_category(
    name: str,
    data: CategoryCreate,
    manager: PlanilhaManager = Depends(get_planilha_manager),
):
    """Atualiza uma categoria existente."""
    try:
        success = manager.atualizar_categoria(
            old_name=name,
            new_name=data.name,
            tipo=data.type,
            icone=data.icon,
            tags=data.tags,
        )
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Erro ao atualizar '{name}'. Verifique se ela existe ou se o novo nome já está em uso.",
            )

        return {"message": f"Categoria '{data.name}' atualizada."}
    except Exception as e:
        logger.error(f"Erro ao atualizar categoria: {e}")
        raise HTTPException(status_code=500, detail=str(e))
