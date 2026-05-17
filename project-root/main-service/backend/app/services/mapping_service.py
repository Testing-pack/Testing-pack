import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from models.mapping import MappingSchema
from repositories.mapping_repository import MappingRepository

logger = logging.getLogger(__name__)


class MappingService:
    """Сервис для работы со схемами маппинга."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = MappingRepository(db)

    async def get_mappings_by_experiment(self, experiment_id: str) -> List[MappingSchema]:
        """Получить все схемы маппинга для эксперимента."""
        try:
            return await self.repository.get_mappings_by_experiment(experiment_id)
        except Exception as e:
            logger.error(f"Ошибка получения схем маппинга для эксперимента {experiment_id}: {e}")
            raise

    async def get_mapping_by_id(self, mapping_id: int) -> Optional[MappingSchema]:
        """Получить схему маппинга по ID."""
        try:
            return await self.repository.get_mapping_by_id(mapping_id)
        except Exception as e:
            logger.error(f"Ошибка получения схемы маппинга {mapping_id}: {e}")
            raise

    async def create_mapping(self, mapping_data: dict) -> MappingSchema:
        """Создать схему маппинга"""
        try:
            fields = mapping_data.pop("fields", [])
            return await self.repository.create_mapping(mapping_data, fields)
        except Exception as e:
            logger.error(f"Ошибка создания схемы маппинга: {e}")
            raise


    async def update_mapping(self, mapping_id: int, updates: dict) -> bool:
        """Обновление схемы маппинга"""
        try:
            fields = updates.pop("fields", None)
            return await self.repository.update_mapping(mapping_id, updates, fields)
        except Exception as e:
            logger.error(f"Ошибка обновления схемы маппинга: {e}")
            raise

    async def get_mapping_config(self, mapping_id: int) -> Optional[List[dict]]:
        try:
            mapping = await self.get_mapping_by_id(mapping_id)
            if mapping is None:
                return None
            if not mapping.fields:
                return []
            return [
                {
                    "input_field_name": f.input_field_name,
                    "input_field_type": f.input_field_type,
                    "target_field": f.target_field,
                    "transformation_rules": f.transformation_rules
                }
                for f in mapping.fields
            ]
        except Exception as e:
            logger.error(f"Ошибка получения конфигурации маппинга для mapping_id={mapping_id}: {e}")
            raise

    async def delete_mapping(self, mapping_id: int) -> bool:
        """Удалить схему маппинга."""
        try:
            return await self.repository.delete_mapping(mapping_id)
        except Exception as e:
            logger.error(f"Ошибка удаления схемы маппинга {mapping_id}: {e}")
            raise

