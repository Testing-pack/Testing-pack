from core.enums import MetricPurpose, MetricStatisticalType, StatisticalTest, DataSourceType, ExperimentStatus
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from typing import List, Optional, Dict, Any
from schemas.metric import MetricSelection, StatisticalTestConfig
from core.predefined_sources import PREDEFINED_DATA_SOURCES


class Hypothesis(BaseModel):
    change_description: str = Field(..., example="Изменение цвета кнопки с синего на зеленый")
    expected_impact: str = Field(..., example="Увеличение конверсии в покупку")
    measurement_method: str = Field(..., example="Сравнение конверсии между контрольной и тестовой группами")
    h0: str = Field(..., example="Нет различий в конверсии между группами")
    h1: str = Field(..., example="Конверсия в тестовой группе выше")


class Variation(BaseModel):
    name: str = Field(..., example="Синяя кнопка")
    traffic_percentage: float = Field(..., ge=0, le=100, example=50.0)



class DataSourceSelection(BaseModel):
    source_type: DataSourceType = Field(..., description="Тип источника данных")
    source_id: Optional[str] = Field(None, description="ID предопределенного источника данных")
    external_source_info: Optional[Dict[str, str]] = Field(None, description="Информация о стороннем источнике")

    @model_validator(mode='after')
    def validate_data_source(self):
        if self.source_type == DataSourceType.INTERNAL_SPLITTING and self.source_id is None:
            raise ValueError("Для сплитования нашей системой необходимо указать source_id")
        if self.source_type == DataSourceType.EXTERNAL_SPLITTING and self.external_source_info is None:
            raise ValueError("Для стороннего сплитования необходимо указать external_source_info")
        if self.source_type == DataSourceType.INTERNAL_SPLITTING and self.source_id not in PREDEFINED_DATA_SOURCES:
            raise ValueError(f"Источник данных с ID '{self.source_id}' не найден")
        return self


class TestParameters(BaseModel):
    test_name: str = Field(..., example="Увеличиваем конверсию в покупку — тест нового дизайна кнопки")
    description: str = Field(..., example="Тестируем новую цветную кнопку для увеличения конверсии")
    owner: str = Field(..., example="user@company.com")
    hypothesis: Hypothesis = Field(...)
    variations: List[Variation]
    metrics: List[MetricSelection]
    data_source: DataSourceSelection
    start_date: datetime
    planned_duration_days: int = Field(..., ge=1, example=14)
    significance_level: float = Field(default=0.05, ge=0.0, le=0.5, example=0.05)
    mde: float = Field(..., ge=0.0, le=1.0, example=0.05, description="Minimum Detectable Effect")
    power: float = Field(default=0.8, ge=0.0, le=1.0, example=0.8, description="Статистическая мощность теста")
    expected_daily_users: int = Field(default=1000, ge=10, description="Ожидаемое количество пользователей в день")

    @field_validator('variations')
    @classmethod
    def validate_traffic_percentage(cls, v):
        if len(v) != 2:
            raise ValueError("Должно быть ровно две вариации (контрольная и тестовая)")
        total = sum(var.traffic_percentage for var in v)
        if abs(total - 100.0) > 0.01:
            raise ValueError(f"Сумма процентов трафика должна быть 100%, получилось {total:.2f}%")
        return v

    @field_validator('metrics')
    @classmethod
    def validate_primary_metrics(cls, v):
        if not v:
            raise ValueError("Должна быть хотя бы одна метрика")
        primary_metrics = [m for m in v if m.purpose == MetricPurpose.PRIMARY]
        if not primary_metrics:
            raise ValueError("Должна быть хотя бы одна целевая (primary) метрика")
        primary_main_metrics = [m for m in primary_metrics if m.is_primary]
        if len(primary_main_metrics) != 1:
            raise ValueError("Может быть только одна основная метрика (is_primary=True)")
        if primary_main_metrics[0].purpose != MetricPurpose.PRIMARY:
            raise ValueError("Основная метрика должна иметь purpose=primary")

        return v



class SampleSizeCalculation(BaseModel):
    metric_id: str
    statistical_type: MetricStatisticalType
    baseline_value: float
    mde: float
    significance_level: float
    power: float
    variance_estimate: Optional[float] = None
    ratio: Optional[float] = Field(default=1.0, description="Соотношение размеров групп")
    expected_daily_users: Optional[int] = Field(default=1000)



class HypothesisResponse(BaseModel):
    change_description: str
    expected_impact: str
    measurement_method: str
    h0: str
    h1: str


class DataSourceResponse(BaseModel):
    source_type: str
    source_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    platform: Optional[str] = None
    contact_person: Optional[str] = None
    additional_info: Optional[str] = None


class VariationResponse(BaseModel):
    var_test_id: str
    name: str = Field(alias="Название")
    traffic_percentage: float = Field(alias="Процент трафика")


class MetricResponse(BaseModel):
    metric_id: str
    purpose: str
    is_primary: bool
    description: Optional[str] = None
    sql_query: Optional[str] = None
    baseline_value: float
    statistical_type: str
    variance_estimate: float
    source: str  # "predefined" или "custom"
    distribution: str
    variance_assumption: str
    outliers: str
    statistical_test: StatisticalTestConfig
    recommended_test: Optional[str] = Field(None)


class LaunchParamsResponse(BaseModel):
    start_date: Optional[str] = Field(None, alias="Дата старта")
    end_date: Optional[str] = Field(None, alias="Дата окончания")
    duration_days: Optional[int] = Field(None, alias="Длительность (дни)")
    significance_level: Optional[float] = Field(None, alias="Уровень значимости")
    mde: Optional[float] = Field(None, alias="MDE")
    power: Optional[float] = Field(None, alias="Мощность теста")
    expected_daily_users: Optional[int] = Field(None, alias="Ожидаемое кол-во пользователей в день")


class SampleSizeValues(BaseModel):
    control: Optional[int] = None
    treatment: Optional[int] = None
    total: Optional[int] = None


class StatisticalResultItem(BaseModel):
    metric_name: str
    metric_id: Optional[str] = None # ИЗМЕНЕНО: сделано Optional для обработки ошибок
    is_primary: Optional[bool] = None # ИЗМЕНЕНО
    sample_size: Optional[SampleSizeValues] = None # ИЗМЕНЕНО
    days_needed: Optional[int] = None
    planned_days: Optional[int] = None
    sufficient: Optional[bool] = None # ИЗМЕНЕНО
    calculation_details: Dict[str, Any] = {}
    error: Optional[str] = None # ДОБАВЛЕНО: поле для описания ошибки


class StatisticalCalculationsResponse(BaseModel):
    results: List[StatisticalResultItem] = []
    total_primary_metrics: int
    parameters: Dict[str, Any]  # mde, significance_level, power, expected_daily_users, planned_duration_days


class TestConfigurationResponse(BaseModel):
    main_params: Dict[str, Any] = Field(alias="Основные параметры")          # может быть уточнено позже
    data_source: DataSourceResponse = Field(alias="Источник данных")
    variations: List[VariationResponse] = Field(alias="Варианты теста")
    metrics: List[MetricResponse] = Field(alias="Метрики")
    launch_params: LaunchParamsResponse = Field(alias="Параметры запуска")
    statistical_calculations: StatisticalCalculationsResponse = Field(alias="Статистические расчеты")


class ExperimentDetailResponse(BaseModel):
    test_id: str
    status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    test_configuration: TestConfigurationResponse
    metadata: Dict[str, Any]


class ExperimentListItem(BaseModel):
    test_id: str
    test_name: str
    owner: str
    status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    variations_count: int
    metrics_count: int
    planned_duration: Optional[int] = None


class ExperimentsListResponse(BaseModel):
    total: int
    experiments: List[ExperimentListItem]
    data_source: str


class DeleteExperimentResponse(BaseModel):
    status: str
    message: str
    test_id: str


class UpdateStatusResponse(BaseModel):
    status: str
    test_id: str
    new_status: str
    message: str