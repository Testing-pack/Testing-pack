import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from models.mapping import MappingSchema, MappingField
from sqlalchemy.orm import selectinload
from datetime import datetime as dt
logger = logging.getLogger(__name__)


class MappingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_mapping(self, mapping_data: dict, fields: list[dict]) -> MappingSchema:
        """Создать схему маппинга вместе с полями"""
        try:
            mapping = MappingSchema(
                experiment_id=mapping_data["experiment_id"],
                mapping_name=mapping_data["mapping_name"],
                file_format=mapping_data.get("file_format"),
                description=mapping_data.get("description"),
                is_active=mapping_data.get("is_active", True)
            )
            self.session.add(mapping)
            await self.session.flush()

            for field_data in fields:
                field = MappingField(
                    mapping_id=mapping.mapping_id,
                    input_field_name=field_data["input_field_name"],
                    input_field_type=field_data["input_field_type"],
                    target_field=field_data["target_field"],
                    transformation_rules=field_data.get("transformation_rules")
                )
                self.session.add(field)

            await self.session.commit()
            await self.session.refresh(mapping)
            return mapping
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка создания схемы маппинга: {e}")
            raise

    async def get_mapping_by_id(self, mapping_id: int) -> Optional[MappingSchema]:
        try:
            result = await self.session.execute(
                select(MappingSchema)
                .options(selectinload(MappingSchema.fields))
                .where(MappingSchema.mapping_id == mapping_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Ошибка получения схемы маппинга: {e}")
            raise


    async def update_mapping(self, mapping_id: int, updates: dict, fields: Optional[list] = None) -> bool:
        """Обновить схему и, если fields передан, заменить все поля"""
        try:
            if updates:
                stmt = update(MappingSchema).where(MappingSchema.mapping_id == mapping_id).values(**updates, updated_at=dt.utcnow())
                await self.session.execute(stmt)

            if fields is not None:
                await self.session.execute(
                    delete(MappingField).where(MappingField.mapping_id == mapping_id)
                )
                for field_data in fields:
                    field = MappingField(
                        mapping_id=mapping_id,
                        input_field_name=field_data["input_field_name"],
                        input_field_type=field_data["input_field_type"],
                        target_field=field_data["target_field"],
                        transformation_rules=field_data.get("transformation_rules")
                    )
                    self.session.add(field)

            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка обновления схемы маппинга: {e}")
            raise

    async def get_mappings_by_experiment(self, experiment_id: str) -> List[MappingSchema]:
        try:
            result = await self.session.execute(
                select(MappingSchema)
                .options(selectinload(MappingSchema.fields))
                .where(MappingSchema.experiment_id == experiment_id)
                .order_by(MappingSchema.created_at.desc())
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Ошибка получения схем маппинга: {e}")
            raise



    async def delete_mapping(self, mapping_id: int) -> bool:
        """Удалить схему маппинга"""
        try:
            await self.session.execute(
                delete(MappingSchema).where(MappingSchema.mapping_id == mapping_id)
            )
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка удаления схемы маппинга: {e}")
            raise

    async def get_active_mapping(self, experiment_id: str, source_type: str) -> Optional[MappingSchema]:
        """Получить активную схему маппинга"""
        try:
            result = await self.session.execute(
                select(MappingSchema)
                .where(
                    MappingSchema.experiment_id == experiment_id,
                    MappingSchema.source_type == source_type,
                    MappingSchema.is_active == True
                )
                .order_by(MappingSchema.created_at.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Ошибка получения активной схемы маппинга: {e}")
            raise