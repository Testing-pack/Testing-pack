from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import Optional

from api.dependencies import get_file_service
from services.file_service import FileService
from schemas.file import FileUploadResponse

router = APIRouter(prefix="/files", tags=["files"])

@router.post("/upload_csv", response_model=FileUploadResponse)
async def upload_csv(
        file: UploadFile = File(...),
        experiment_id: Optional[str] = Form(None),
        file_service: FileService = Depends(get_file_service)
):
    """Загрузка CSV файла"""
    try:
        result = await file_service.upload_csv(file, experiment_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки CSV файла: {str(e)}")