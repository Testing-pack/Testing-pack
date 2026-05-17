from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union

class CsvAnalysisResult(BaseModel):
    row_count: int
    headers: List[str]
    sample_data: List[List[str]]

class S3UploadBase(BaseModel):
    success: bool
    upload_id: Optional[int] = None
    file_format: Optional[str] = None
    s3_path: Optional[str] = None
    file_hash: Optional[str] = None
    file_size: Optional[int] = None
    experiment_id: Optional[str] = None

class S3UploadSuccess(S3UploadBase):
    success: bool = True
    durations: Dict[str, int] = Field(..., description="Время загрузки в мс")

class S3UploadError(S3UploadBase):
    success: bool = False
    error: str
    original_hash: Optional[str] = None
    downloaded_hash: Optional[str] = None
    original_size: Optional[int] = None
    downloaded_size: Optional[int] = None

S3UploadResult = Union[S3UploadSuccess, S3UploadError]

class FileUploadResponse(BaseModel):
    filename: str
    size: int
    row_count: int
    headers: List[str]
    sample_data: List[List[str]]
    message: str
    experiment_id: Optional[str] = None
    s3_upload: S3UploadResult
    mapping_applied: bool
    mapping_id: Optional[int] = None