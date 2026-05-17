from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .dependencies import get_split_db
from .service import SplitService
from .repository import AssignmentRepository

router = APIRouter(prefix="/split", tags=["split"])

@router.post("/assign")
async def assign_user_to_test(
    test_id: str,
    user_id: str,
    split_db: AsyncSession = Depends(get_split_db),
):
    service = SplitService(split_db)
    try:
        variation = await service.assign_user(test_id, user_id)
        return {
            "test_id": test_id,
            "user_id": user_id,
            "variation_id": variation
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")

@router.get("/assignment")
async def get_user_assignment(
    test_id: str,
    user_id: str,
    split_db: AsyncSession = Depends(get_split_db),
):
    repo = AssignmentRepository(split_db)
    assignment = await repo.get_assignment(test_id, user_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Назначение не найдено")
    return {
        "test_id": assignment.test_id,
        "user_id": assignment.user_id,
        "variation_id": assignment.variation_id,
        "assigned_at": assignment.assigned_at.isoformat()
    }