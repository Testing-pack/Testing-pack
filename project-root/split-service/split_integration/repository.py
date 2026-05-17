import logging
from typing import Optional, List, Dict, Any
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import UserAssignment
from .config import settings

logger = logging.getLogger(__name__)

class ExperimentApiRepository:
    """Получает конфигурацию эксперимента через REST API основного сервиса."""

    async def get_experiment_with_variations(self, test_id: str) -> Optional[Dict[str, Any]]:
        url = f"{settings.MAIN_SERVICE_URL}/experiments/{test_id}"
        logger.info(f"Запрашиваем эксперимент из основного сервиса: {url}")
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                return data
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return None
                raise Exception(f"Ошибка при запросе эксперимента: {e.response.text}")
            except Exception as e:
                raise Exception(f"Не удалось связаться с основным сервисом: {str(e)}")


class AssignmentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_assignment(self, test_id: str, user_id: str) -> Optional[UserAssignment]:
        result = await self.session.execute(
            select(UserAssignment).where(
                UserAssignment.test_id == test_id,
                UserAssignment.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def create_assignment(
        self, test_id: str, user_id: str, variation_id: str
    ) -> UserAssignment:
        assignment = UserAssignment(
            test_id=test_id,
            user_id=user_id,
            variation_id=variation_id,
        )
        self.session.add(assignment)
        await self.session.commit()
        await self.session.refresh(assignment)
        logger.info(f"Назначен пользователь {user_id} в вариант {variation_id} теста {test_id}")
        return assignment