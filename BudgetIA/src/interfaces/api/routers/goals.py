from fastapi import APIRouter, Depends, HTTPException

from finance.planilha_manager import PlanilhaManager
from interfaces.api.dependencies import get_planilha_manager
from interfaces.api.schemas.goals import GoalCreate, GoalSchema

router = APIRouter(prefix="/goals", tags=["Metas"])


@router.get("/", response_model=list[GoalSchema])
def list_goals(manager: PlanilhaManager = Depends(get_planilha_manager)):
    """Lista todas as metas financeiras."""
    try:
        goals = manager.list_goals_use_case.execute()
        return goals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=bool)
def create_goal(
    goal: GoalCreate, manager: PlanilhaManager = Depends(get_planilha_manager)
):
    """Cria uma nova meta."""
    from datetime import datetime

    from finance.domain.models.goal import Goal

    try:
        with manager.lock_file(timeout_seconds=30):
            manager.refresh_data()

            data_alvo = (
                datetime.combine(goal.data_alvo, datetime.min.time())
                if goal.data_alvo
                else None
            )

            new_goal = Goal(
                nome=goal.nome,
                valor_alvo=goal.valor_alvo,
                valor_atual=goal.valor_atual,
                data_alvo=data_alvo,
                observacoes=goal.observacoes or "",
            )

            manager.add_or_update_goal_use_case.execute(new_goal)
            manager.save()
            return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{goal_id}", response_model=bool)
def update_goal(
    goal_id: int,
    goal: GoalCreate,
    manager: PlanilhaManager = Depends(get_planilha_manager),
):
    """Atualiza uma meta existente."""
    from datetime import datetime

    from finance.domain.models.goal import Goal

    try:
        with manager.lock_file(timeout_seconds=30):
            manager.refresh_data()

            data_alvo = (
                datetime.combine(goal.data_alvo, datetime.min.time())
                if goal.data_alvo
                else None
            )

            updated_goal = Goal(
                id=goal_id,
                nome=goal.nome,
                valor_alvo=goal.valor_alvo,
                valor_atual=goal.valor_atual,
                data_alvo=data_alvo,
                observacoes=goal.observacoes or "",
            )

            manager.add_or_update_goal_use_case.execute(updated_goal)
            manager.save()
            return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{goal_id}", response_model=bool)
def delete_goal(goal_id: int, manager: PlanilhaManager = Depends(get_planilha_manager)):
    """Remove uma meta."""
    try:
        with manager.lock_file(timeout_seconds=30):
            manager.refresh_data()
            success = manager.delete_goal_use_case.execute(goal_id)
            if success:
                manager.save()
            return success
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
