from core.config import settings
from repositories.s3_repository import S3Repository
from repositories.file_upload_repository import FileUploadRepository
from services.file_service import FileService
from core.database_pgsql import get_async_session

_s3_repo = S3Repository(
    endpoint=settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    bucket=settings.MINIO_BUCKET_NAME,
    secure=settings.MINIO_SECURE
)
