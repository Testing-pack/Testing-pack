from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from schemas.experiment import SampleSizeCalculation
from services.metric_service import MetricService
from utils.statistical_tests import recommend_statistical_test, get_test_explanation
from core.predefined_metrics import PREDEFINED_METRICS
from core.enums import MetricPurpose, MetricStatisticalType, StatisticalTest
from core.enums import MetricStatisticalType

from schemas.metric import (
    AvailableMetricsResponse,
    SqlTemplateResponse,
    SampleSizeResponse,
    RecommendTestResponse,
    PredefinedMetricInfo
)
import uuid

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/available", response_model=AvailableMetricsResponse)
async def get_available_metrics():
    """Получить список доступных метрик"""
    return {
        "predefined_metrics": PREDEFINED_METRICS,
        "metric_purposes": [purpose.value for purpose in MetricPurpose],
        "statistical_types": [stype.value for stype in MetricStatisticalType],
        "statistical_tests": [test.value for test in StatisticalTest]
    }


@router.get("/sql_template/{metric_id}", response_model=SqlTemplateResponse)
async def get_metric_sql_template(metric_id: str):
    """Получить SQL шаблон для метрики"""
    if metric_id not in PREDEFINED_METRICS:
        raise HTTPException(status_code=404, detail=f"Метрика с ID '{metric_id}' не найдена")

    metric_data = PREDEFINED_METRICS[metric_id]
    return {
        "metric_id": metric_id,
        "sql_template": metric_data.get("sql_template", ""),
        "description": metric_data.get("description", ""),
        "statistical_type": metric_data.get("statistical_type", ""),
        "purpose": metric_data.get("purpose", ""),
        "recommended_test": metric_data.get("recommended_test", ""),
        "baseline_value": metric_data.get("baseline_value", 0.0),
        "variance_estimate": metric_data.get("variance_estimate", 0.0)
    }


@router.post("/calculate_sample_size", response_model=SampleSizeResponse)
async def calculate_sample_size_endpoint(calculation: SampleSizeCalculation):
    """Расчет размера выборки для метрики"""
    try:
        service = MetricService()
        result = await service.calculate_sample_size(calculation)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка расчета размера выборки: {str(e)}")


@router.post("/recommend_test", response_model=RecommendTestResponse)
async def recommend_test_endpoint(metric_data: Dict[str, Any]):
    """Рекомендация статистического теста для метрики"""
    try:
        statistical_type = MetricStatisticalType(metric_data.get("statistical_type", "proportion"))
        data_characteristics = metric_data.get("data_characteristics", {})

        test_config = recommend_statistical_test(statistical_type, data_characteristics)

        return {
            "recommended_test": test_config.test_type.value,
            "explanation": get_test_explanation(test_config.test_type, statistical_type),
            "statistical_type": statistical_type.value
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка рекомендации теста: {str(e)}")
