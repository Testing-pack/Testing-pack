from fastapi import APIRouter, HTTPException

from core.database_pgsql import get_async_session
from api.dependencies import get_file_service
from services.file_service import FileService
from core.predefined_sources import PREDEFINED_DATA_SOURCES
from core.enums import DataSourceType
import uuid

router = APIRouter(tags=["health"])

experiments_storage = {}

@router.get("/available_data_sources")
async def get_available_data_sources():
    """Получить список доступных источников данных"""
    return {
        "predefined_data_sources": PREDEFINED_DATA_SOURCES,
        "data_source_types": [source_type.value for source_type in DataSourceType]
    }

