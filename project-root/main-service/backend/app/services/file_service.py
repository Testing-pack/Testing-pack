import io
import csv
import hashlib
import time
import os
import asyncio
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime as dt

import aiofiles
import aiofiles.os as aio_os
import aiofiles.tempfile as aio_tempfile
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.s3_repository import S3Repository
from repositories.file_upload_repository import FileUploadRepository

logger = logging.getLogger(__name__)


class FileService:
    """Сервис для работы с файлами: загрузка, анализ, сохранение в S3"""

    def __init__(
        self,
        db: AsyncSession,
        s3_repo: S3Repository,
        file_upload_repo: FileUploadRepository
    ):
        self.db = db
        self.s3_repo = s3_repo
        self.file_upload_repo = file_upload_repo
        self.base_s3_path = "file-upload"

    async def upload_csv(
        self,
        file: UploadFile,
        experiment_id: Optional[str] = None,
        mapping_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Загрузка CSV файла, анализ, сохранение в S3 с проверкой целостности.
        """
        try:
            logger.info(f"ПОЛУЧЕН CSV ФАЙЛ: {file.filename}")

            contents = await file.read()

            analysis_result = await self._analyze_csv(contents)

            upload_result = await self._upload_to_s3_and_verify(
                file_name=file.filename,
                file_content=contents,
                experiment_id=experiment_id,
                mapping_id=mapping_id,
                description=f"CSV файл для A/B тестов: {file.filename}"
            )

            response = {
                "filename": file.filename,
                "size": len(contents),
                **analysis_result,
                "message": f"Файл успешно загружен. Обработано {analysis_result['row_count']} строк.",
                "experiment_id": experiment_id,
            }

            if upload_result.get("success"):
                response["s3_upload"] = upload_result
            else:
                logger.error(f"Ошибка загрузки в S3: {upload_result.get('error')}")
                response["s3_upload"] = upload_result

            return response

        except Exception as e:
            logger.error(f"\n ОШИБКА ПРИ ОБРАБОТКЕ CSV ФАЙЛА: {str(e)}")
            raise

    # ---------- Приватные методы (загрузка и верификация) ----------

    async def _upload_to_s3_and_verify(
        self,
        file_name: str,
        file_content: bytes,
        experiment_id: Optional[str] = None,
        mapping_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Загружает файл в S3, проверяет целостность, сохраняет запись в БД."""
        total_start_time = time.time()

        file_format = self._extract_file_format(file_name)
        logger.info(f"Файл: {file_name}, формат: {file_format}")

        logger.info("Вычисление хэша...")
        original_hash, file_size = await self._calculate_sha256(file_content)

        logger.info("Создание записи в БД...")
        upload_record = await self.file_upload_repo.create_upload_record(
            file_name=file_name,
            file_format=file_format,
            file_hash=original_hash,
            file_size=file_size,
            experiment_id=experiment_id,
            mapping_id=mapping_id
        )
        upload_id = upload_record.upload_id

        current_date = dt.now()
        s3_path = (
            f"{self.base_s3_path}/"
            f"{current_date.year}/{current_date.month:02d}/{current_date.day:02d}/"
            f"{upload_id}/"
            f"{file_name}"
        )

        await self.file_upload_repo.update_upload_record(upload_id, {'s3_path': s3_path})

        logger.info("Загрузка в S3...")
        upload_start_time = time.time()

        temp_file_path = await self._write_temp_file(file_content, suffix=f"_upload_{upload_id}")

        try:
            metadata = {
                'upload-id': str(upload_id),
                'original-sha256': original_hash,
                'file-name': self._clean_metadata_value(file_name),
                'file-format': file_format,
                'integrity-check': 'full-verification'
            }
            if experiment_id:
                metadata['experiment-id'] = experiment_id
            if description:
                metadata['description'] = self._clean_metadata_value(description)

            await self.s3_repo.ensure_bucket_exists()
            await self.s3_repo.upload_file(
                object_name=s3_path,
                file_path=temp_file_path,
                metadata=metadata
            )

            upload_duration = int((time.time() - upload_start_time) * 1000)

            logger.info("Проверка целостности...")
            verification_start_time = time.time()

            temp_verify_path = await self._write_temp_file(b'', suffix=f"_verify_{upload_id}")

            try:
                await self.s3_repo.download_file(object_name=s3_path, file_path=temp_verify_path)

                async with aiofiles.open(temp_verify_path, 'rb') as f:
                    downloaded_content = await f.read()

                downloaded_hash, downloaded_size = await self._calculate_sha256(downloaded_content)
                verification_duration = int((time.time() - verification_start_time) * 1000)

                success = (original_hash == downloaded_hash and file_size == downloaded_size)
                error_details = None
                if not success:
                    error_details = "hash_mismatch" if original_hash != downloaded_hash else "size_mismatch"

                total_duration = int((time.time() - total_start_time) * 1000)

                if success:
                    await self.file_upload_repo.update_upload_record(upload_id, {
                        'upload_status': 'verified',
                        'verified_hash_sha256': downloaded_hash,
                        'verified_at': dt.utcnow()
                    })
                    return {
                        'success': True,
                        'upload_id': upload_id,
                        'mapping_id': mapping_id,
                        'file_format': file_format,
                        's3_path': s3_path,
                        'file_hash': original_hash,
                        'file_size': file_size,
                        'experiment_id': experiment_id,
                        'durations': {
                            'upload_ms': upload_duration,
                            'verification_ms': verification_duration,
                            'total_ms': total_duration
                        }
                    }
                else:
                    await self.file_upload_repo.update_upload_record(upload_id, {'upload_status': 'failed'})
                    return {
                        'success': False,
                        'upload_id': upload_id,
                        'error': error_details,
                        'original_hash': original_hash,
                        'downloaded_hash': downloaded_hash,
                        'original_size': file_size,
                        'downloaded_size': downloaded_size
                    }

            finally:
                await self._delete_temp_file(temp_verify_path)

        finally:
            await self._delete_temp_file(temp_file_path)

    # ---------- Приватные утилиты ----------

    def _extract_file_format(self, file_name: str) -> str:
        parts = file_name.split('.')
        if len(parts) > 1:
            file_format = parts[-1].lower()
            file_format = ''.join(c for c in file_format if c.isalnum())
            return file_format if file_format else 'unknown'
        return 'unknown'

    async def _calculate_sha256(self, file_content: bytes) -> Tuple[str, int]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._calculate_sha256_sync, file_content)

    def _calculate_sha256_sync(self, file_content: bytes) -> Tuple[str, int]:
        sha256_hash = hashlib.sha256()
        file_size = len(file_content)
        sha256_hash.update(file_content)
        return sha256_hash.hexdigest(), file_size

    def _clean_metadata_value(self, value: str) -> str:
        if isinstance(value, str):
            return ''.join(c if ord(c) < 128 else '_' for c in value)
        return str(value)

    async def _write_temp_file(self, content: bytes, suffix: str = "") -> str:
        async with aio_tempfile.NamedTemporaryFile(
                mode='wb',
                delete=False,
                suffix=suffix
        ) as tmp:
            await tmp.write(content)
            return tmp.name

    async def _delete_temp_file(self, file_path: str):
        try:
            if os.path.exists(file_path):
                await aio_os.remove(file_path)
        except Exception as e:
            logger.warning(f"Не удалось удалить временный файл {file_path}: {e}")

    async def _analyze_csv(self, contents: bytes) -> Dict[str, Any]:
        try:
            content_str = contents.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content_str = contents.decode('windows-1251')
            except:
                content_str = contents.decode('latin-1')

        csv_file = io.StringIO(content_str)
        csv_reader = csv.reader(csv_file)

        headers = next(csv_reader)
        row_count = 0
        sample_rows = []

        for row in csv_reader:
            row_count += 1
            if row_count <= 10:
                sample_rows.append(row)

        return {
            "row_count": row_count,
            "headers": headers,
            "sample_data": sample_rows[:5]
        }
