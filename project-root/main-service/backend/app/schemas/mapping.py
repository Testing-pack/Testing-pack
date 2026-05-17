from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from schemas.common import MessageResponse

class MappingFieldBase(BaseModel):
    input_field_name: str = Field(..., description="Название поля во входных данных")
    input_field_type: str = Field(..., description="Тип данных",
                                  examples=["string", "integer", "float", "datetime", "boolean"])
    target_field: str = Field(..., description="Целевое поле в нашей системе")
    transformation_rules: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Правила преобразования")

class MappingFieldCreate(MappingFieldBase):
    pass

class MappingFieldResponse(MappingFieldBase):
    mapping_field_id: int
    mapping_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MappingSchemaBase(BaseModel):
    mapping_name: str = Field(..., description="Название схемы маппинга")
    file_format: Optional[str] = Field(None, description="Формат файла")
    description: Optional[str] = Field(None, description="Описание")
    is_active: bool = Field(default=True, description="Активна ли схема")

class MappingSchemaCreate(MappingSchemaBase):
    experiment_id: str = Field(..., description="ID эксперимента")
    fields: List[MappingFieldCreate] = Field(..., description="Список полей маппинга")

class MappingSchemaUpdate(BaseModel):
    mapping_name: Optional[str] = None
    file_format: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    fields: Optional[List[MappingFieldCreate]] = None

class MappingSchemaResponse(MappingSchemaBase):
    mapping_id: int
    experiment_id: Optional[str]
    fields: List[MappingFieldResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MappingsListResponse(BaseModel):
    mappings: List[MappingSchemaResponse]

class CreateMappingResponse(MessageResponse):
    mapping_id: int