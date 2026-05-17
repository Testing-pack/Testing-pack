import logging
import random
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from .repository import ExperimentApiRepository, AssignmentRepository

logger = logging.getLogger(__name__)

class SplitService:
    ACTIVE_STATUS = "active"

    def __init__(self, split_db: AsyncSession):
        self.split_db = split_db
        self.experiment_repo = ExperimentApiRepository()
        self.assignment_repo = AssignmentRepository(split_db)

    async def assign_user(self, test_id: str, user_id: str) -> str:
        exp_data = await self.experiment_repo.get_experiment_with_variations(test_id)
        if not exp_data:
            raise ValueError(f"Эксперимент с ID '{test_id}' не найден в основном сервисе")

        status = exp_data.get("status")
        if status != self.ACTIVE_STATUS:
            raise ValueError(f"Эксперимент '{test_id}' не активен (статус: {status})")

        start_date_str = exp_data.get("start_date")
        end_date_str = exp_data.get("end_date")
        if start_date_str:
            start_date = datetime.fromisoformat(start_date_str)
            if datetime.utcnow() < start_date:
                raise ValueError("Эксперимент ещё не начался")
        if end_date_str:
            end_date = datetime.fromisoformat(end_date_str)
            if datetime.utcnow() > end_date:
                raise ValueError("Эксперимент уже завершён")

        existing = await self.assignment_repo.get_assignment(test_id, user_id)
        if existing:
            return existing.variation_id

        variations = []
        test_config = exp_data.get("test_configuration", {})
        vars_list = test_config.get("Варианты теста", [])
        if not vars_list or len(vars_list) < 2:
            raise ValueError("Основной сервис вернул эксперимент без вариантов или их меньше двух")

        for var in vars_list:
            var_id = var.get("var_test_id")
            traffic = var.get("Процент трафика")
            if var_id and traffic is not None:
                variations.append((var_id, traffic))

        if not variations:
            raise ValueError("Не удалось извлечь варианты из ответа основного сервиса")

        var_ids, weights = zip(*variations)
        total = sum(weights)
        normalized = [w / total for w in weights]
        selected = random.choices(var_ids, weights=normalized, k=1)[0]

        await self.assignment_repo.create_assignment(test_id, user_id, selected)
        return selected