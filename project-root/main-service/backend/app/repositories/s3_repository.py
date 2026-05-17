import logging
from typing import Dict, Optional
from miniopy_async import Minio
from miniopy_async.error import S3Error as AsyncS3Error

logger = logging.getLogger(__name__)

class S3Repository:
    """Репозиторий для работы с MinIO/S3 (асинхронный)"""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False
    ):
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self.bucket = bucket


    async def ensure_bucket_exists(self) -> None:
        """Проверить и создать бакет, если не существует"""
        try:
            if not await self.client.bucket_exists(self.bucket):
                await self.client.make_bucket(self.bucket)
                logger.info(f"Бакет {self.bucket} создан")
        except Exception as e:
            logger.error(f"Ошибка при проверке/создании бакета: {e}")
            raise

    async def upload_file(self, object_name: str, file_path: str, metadata: Dict[str, str]) -> None:
        """Загрузить файл в бакет"""
        await self.client.fput_object(
            bucket_name=self.bucket,
            object_name=object_name,
            file_path=file_path,
            metadata=metadata
        )

    async def download_file(self, object_name: str, file_path: str) -> None:
        """Скачать файл из бакета"""
        await self.client.fget_object(
            bucket_name=self.bucket,
            object_name=object_name,
            file_path=file_path
        )

    async def object_exists(self, object_name: str) -> bool:
        """Проверить существование объекта"""
        try:
            await self.client.stat_object(self.bucket, object_name)
            return True
        except AsyncS3Error as e:
            if e.code == 'NoSuchKey':
                return False
            raise

    async def remove_object(self, object_name: str) -> None:
        """Удалить объект из бакета"""
        await self.client.remove_object(self.bucket, object_name)