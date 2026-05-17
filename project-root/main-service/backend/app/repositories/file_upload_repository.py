import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime as dt
from sqlalchemy import select

from models.file_upload import FileUpload

logger = logging.getLogger(__name__)


class FileUploadRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_upload_record(
            self, file_name: str,
            file_format: str,
            file_hash: str,
            file_size: int,
            experiment_id: Optional[str] = None,
            mapping_id: Optional[int] = None
    ) -> FileUpload:
        """Создать запись о загрузке"""
        try:
            upload_record = FileUpload(
                file_name=file_name,
                file_format=file_format,
                s3_path='temp_path',
                original_hash_sha256=file_hash,
                file_size_bytes=file_size,
                upload_status='uploading',
                experiment_id=experiment_id,
                mapping_id=mapping_id,
                uploaded_at=dt.utcnow()
            )

            self.session.add(upload_record)
            await self.session.commit()
            await self.session.refresh(upload_record)

            return upload_record
        except Exception as e:
            await self.session.rollback()
            raise


    async def update_upload_record(self, upload_id: int, updates: dict) -> bool:
        """Обновить запись о загрузке"""
        try:
            result = await self.session.execute(
                select(FileUpload).where(FileUpload.upload_id == upload_id)
            )
            upload_record = result.scalar_one_or_none()

            if not upload_record:
                raise Exception(f"Запись с upload_id={upload_id} не найдена")

            for key, value in updates.items():
                if hasattr(upload_record, key):
                    setattr(upload_record, key, value)

            upload_record.updated_at = dt.utcnow()
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            raise Exception(f"Ошибка обновления записи в PostgreSQL: {e}")

    async def get_upload_by_id(self, upload_id: int) -> Optional[FileUpload]:
        """Получить запись о загрузке по ID"""
        try:
            result = await self.session.execute(
                select(FileUpload).where(FileUpload.upload_id == upload_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Ошибка получения записи о загрузке: {e}")
            raise




