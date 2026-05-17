from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from schemas.experiment import (
    TestParameters,
    ExperimentsListResponse,
    ExperimentDetailResponse,
    DeleteExperimentResponse,
    UpdateStatusResponse
)
from core.database_pgsql import get_async_session
from schemas.experiment import TestParameters
from services.experiment_service import ExperimentService
from schemas.metric import MetricSelection
from api.dependencies import get_experiment_service
import logging

router = APIRouter(prefix="/experiments", tags=["experiments"])

#
@router.get("/", response_model=ExperimentsListResponse)
async def get_all_experiments(experiment_service: ExperimentService = Depends(get_experiment_service)):
    """Получить все эксперименты"""
    try:
        experiments = await experiment_service.get_all_experiments()
        return {"total": len(experiments), "experiments": experiments, "data_source": "database"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения экспериментов: {str(e)}")

#
@router.get("/{test_id}", response_model=ExperimentDetailResponse)
async def get_experiment(test_id: str, experiment_service: ExperimentService = Depends(get_experiment_service)):
    """Получить детали эксперимента по ID"""
    try:
        experiment = await experiment_service.get_experiment(test_id)
        if not experiment:
            raise HTTPException(status_code=404, detail=f"Эксперимент с ID '{test_id}' не найден")
        return experiment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения эксперимента: {str(e)}")


@router.post("/setup_test", response_model=ExperimentDetailResponse)
async def setup_test(params: TestParameters, experiment_service: ExperimentService = Depends(get_experiment_service)):
    """Создание конфигурации A/B теста"""
    try:
        result = await experiment_service.setup_test(params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка создания теста: {str(e)}")



@router.delete("/{test_id}", response_model=DeleteExperimentResponse)
async def delete_experiment(test_id: str, experiment_service: ExperimentService = Depends(get_experiment_service)):
    """Удалить эксперимент"""
    try:
        await experiment_service.delete_experiment(test_id)
        return {"status": "success", "message": "Эксперимент успешно удален", "test_id": test_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка удаления эксперимента: {str(e)}")

#
@router.patch("/{test_id}/status", response_model=UpdateStatusResponse)
async def update_experiment_status(
        test_id: str,
        status_update: Dict[str, Any],
        experiment_service: ExperimentService = Depends(get_experiment_service)
):
    """Обновить статус эксперимента"""
    try:
        new_status = status_update.get("status")
        if not new_status:
            raise HTTPException(status_code=400, detail="Не указан статус")

        await experiment_service.update_experiment_status(test_id, new_status)
        return {
            "status": "success",
            "test_id": test_id,
            "new_status": new_status,
            "message": f"Статус эксперимента изменен на '{new_status}'"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления статуса: {str(e)}")

