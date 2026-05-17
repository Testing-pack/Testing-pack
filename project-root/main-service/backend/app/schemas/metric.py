from core.enums import MetricPurpose, MetricStatisticalType, StatisticalTest
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, List
from core.predefined_metrics import PREDEFINED_METRICS
from core.enums import MetricStatisticalType, MetricPurpose, StatisticalTest

class StatisticalTestConfig(BaseModel):
    test_type: StatisticalTest

class CustomMetric(BaseModel):
    statistical_type: MetricStatisticalType = Field(default=MetricStatisticalType.PROPORTION)
    purpose: MetricPurpose = Field(default=MetricPurpose.PRIMARY)
    description: str = Field(..., example="Конверсия в покупку")
    sql_query: str = Field(..., example="...")
    baseline_value: Optional[float] = Field(default=0.0, ge=0.0, example=0.03)
    variance_estimate: Optional[float] = Field(default=0.0, ge=0.0, example=0.0001)
    recommended_test: Optional[StatisticalTest] = None

    distribution: str = Field(
        default="unknown",
        pattern="^(normal|non_normal|unknown)$"
    )
    variance_assumption: str = Field(
        default="unknown",
        pattern="^(equal|unequal|unknown)$"
    )
    outliers: str = Field(
        default="insignificant",
        pattern="^(significant|insignificant)$"
    )


class MetricSelection(BaseModel):
    custom_metric: CustomMetric = Field(..., description="Кастомная метрика")
    purpose: MetricPurpose = Field(default=MetricPurpose.PRIMARY)
    statistical_test: Optional[StatisticalTestConfig] = Field(None, description="Настройки статистического теста")
    is_primary: bool = Field(default=False, description="Основная ли метрика (только для primary purpose)")

    @model_validator(mode='after')
    def validate_metric_selection(self):
        if self.is_primary and self.purpose != MetricPurpose.PRIMARY:
            raise ValueError("Только primary метрики могут быть помечены как основные")
        return self


class PredefinedMetricInfo(BaseModel):
    statistical_type: MetricStatisticalType
    purpose: MetricPurpose
    description: str
    recommended_test: StatisticalTest
    sql_template: str
    baseline_value: float
    variance_estimate: float

class AvailableMetricsResponse(BaseModel):
    predefined_metrics: Dict[str, PredefinedMetricInfo]
    metric_purposes: List[str]
    statistical_types: List[str]
    statistical_tests: List[str]

class SqlTemplateResponse(BaseModel):
    metric_id: str
    sql_template: str
    description: str
    statistical_type: str
    purpose: str
    recommended_test: str
    baseline_value: float
    variance_estimate: float

class SampleSizeValues(BaseModel):
    control: int
    treatment: int
    total: int

class CalculationDetails(BaseModel):
    baseline: float
    mde: float
    significance_level: float
    power: float
    variance_estimate: Optional[float] = None

class SampleSizeResponse(BaseModel):
    sample_size: SampleSizeValues
    days_needed: int
    expected_daily_users: int
    statistical_type: str
    calculation_details: CalculationDetails

class RecommendTestResponse(BaseModel):
    recommended_test: str
    explanation: str
    statistical_type: str
