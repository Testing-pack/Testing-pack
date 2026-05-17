from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Optional

from core.database_pgsql import get_async_session
from services.file_service import FileService
from services.mapping_service import MappingService
from schemas.mapping import MappingSchemaCreate, MappingSchemaUpdate, MappingsListResponse, MappingSchemaResponse, CreateMappingResponse
from api.dependencies import get_mapping_service, get_file_service
from schemas.common import MessageResponse
from schemas.file import FileUploadResponse, S3UploadSuccess, S3UploadError
import logging

router = APIRouter(prefix="/mapping", tags=["mapping"])


@router.get("/experiment/{experiment_id}", response_model=MappingsListResponse)
async def get_experiment_mappings(
    experiment_id: str,
    mapping_service: MappingService = Depends(get_mapping_service)
):
    """Получить все схемы маппинга для эксперимента"""
    try:
        mappings = await mapping_service.get_mappings_by_experiment(experiment_id)
        mappings_response = [MappingSchemaResponse.model_validate(m) for m in mappings]
        return MappingsListResponse(mappings=mappings_response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения схем маппинга: {str(e)}")


@router.get("/{mapping_id}", response_model=MappingSchemaResponse)
async def get_mapping_schema(
    mapping_id: int,
    mapping_service: MappingService = Depends(get_mapping_service)
):
    """Получить схему маппинга по ID"""
    try:
        mapping = await mapping_service.get_mapping_by_id(mapping_id)
        if not mapping:
            raise HTTPException(status_code=404, detail="Схема маппинга не найдена")
        return MappingSchemaResponse.model_validate(mapping)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения схемы маппинга: {str(e)}")


@router.post("/", response_model=CreateMappingResponse)
async def create_mapping_schema(
    mapping_schema: MappingSchemaCreate,
    mapping_service: MappingService = Depends(get_mapping_service)
):
    """Создать новую схему маппинга"""
    try:
        mapping = await mapping_service.create_mapping(mapping_schema.dict())
        return CreateMappingResponse(
            mapping_id=mapping.mapping_id,
            message="Схема маппинга успешно создана",
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка создания схемы маппинга: {str(e)}")


@router.put("/{mapping_id}", response_model=MessageResponse)
async def update_mapping_schema(
    mapping_id: int,
    update_data: MappingSchemaUpdate,
    mapping_service: MappingService = Depends(get_mapping_service)
):
    """Обновить схему маппинга"""
    try:
        existing_mapping = await mapping_service.get_mapping_by_id(mapping_id)
        if not existing_mapping:
            raise HTTPException(status_code=404, detail="Схема маппинга не найдена")

        await mapping_service.update_mapping(mapping_id, update_data.dict(exclude_unset=True))
        return MessageResponse(
            message="Схема маппинга успешно обновлена",
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления схемы маппинга: {str(e)}")


@router.delete("/{mapping_id}", response_model=MessageResponse)
async def delete_mapping_schema(
    mapping_id: int,
    mapping_service: MappingService = Depends(get_mapping_service)
):
    """Удалить схему маппинга"""
    try:
        existing_mapping = await mapping_service.get_mapping_by_id(mapping_id)
        if not existing_mapping:
            raise HTTPException(status_code=404, detail="Схема маппинга не найдена")

        await mapping_service.delete_mapping(mapping_id)
        return MessageResponse(
            message="Схема маппинга успешно удалена",
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка удаления схемы маппинга: {str(e)}")


@router.post("/upload_csv_with_mapping", response_model=FileUploadResponse)
async def upload_csv_with_mapping(
    file: UploadFile = File(...),
    experiment_id: Optional[str] = Form(None),
    mapping_id: Optional[int] = Form(None),
    file_service: FileService = Depends(get_file_service),
    mapping_service: MappingService = Depends(get_mapping_service)
):
    """Загрузка CSV файла с применением схемы маппинга"""
    try:
        mapping_config = None
        if mapping_id:
            mapping_config = await mapping_service.get_mapping_config(mapping_id)

        result = await file_service.upload_csv(file, experiment_id, mapping_id)

        s3_data = result.get("s3_upload", {})
        s3_upload_obj = S3UploadSuccess(**s3_data) if s3_data.get("success") else S3UploadError(**s3_data)

        return FileUploadResponse(
            filename=result["filename"],
            size=result["size"],
            row_count=result["row_count"],
            headers=result["headers"],
            sample_data=result["sample_data"],
            message=result["message"],
            experiment_id=result.get("experiment_id"),
            s3_upload=s3_upload_obj,
            mapping_applied=bool(mapping_config),
            mapping_id=mapping_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки CSV файла: {str(e)}")