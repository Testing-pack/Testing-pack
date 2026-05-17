from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database_pgsql import get_async_session
from services.file_service import FileService
from services.mapping_service import MappingService
from services.experiment_service import ExperimentService

from schemas.mapping import MappingSchemaCreate, MappingSchemaUpdate
from repositories.file_upload_repository import FileUploadRepository

from core.s3 import _s3_repo

def get_mapping_service(db: AsyncSession = Depends(get_async_session)) -> MappingService:
    return MappingService(db)

async def get_file_service(db: AsyncSession = Depends(get_async_session)) -> FileService:
    """
    Зависимость, возвращающая настроенный экземпляр FileService.
    """
    file_upload_repo = FileUploadRepository(db)
    return FileService(
        db=db,
        s3_repo=_s3_repo,
        file_upload_repo=file_upload_repo
    )

def get_experiment_service(db: AsyncSession = Depends(get_async_session)) -> ExperimentService:
    return ExperimentService(db)
