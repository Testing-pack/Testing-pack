import math
import logging
from typing import Dict, Any, List
from schemas.experiment import SampleSizeCalculation, TestParameters
from schemas.metric import MetricSelection
from core.enums import MetricStatisticalType, MetricPurpose
from utils.sample_size_calculator import (
    calculate_sample_size_proportion,
    calculate_sample_size_continuous,
    calculate_sample_size_ratio
)
from utils.statistical_tests import recommend_statistical_test
from core.predefined_metrics import PREDEFINED_METRICS

logger = logging.getLogger(__name__)


class MetricService:
    @staticmethod
    async def calculate_sample_size(calculation: SampleSizeCalculation) -> Dict[str, Any]:
        """Расчет размера выборки для метрики"""
        logger.info(f"РАСЧЕТ РАЗМЕРА ВЫБОРКИ ДЛЯ МЕТРИКИ: {calculation.metric_id}")

        if calculation.statistical_type in [MetricStatisticalType.CONTINUOUS_MEAN, MetricStatisticalType.RATIO]:
            if calculation.variance_estimate is None or calculation.variance_estimate < 0:
                 raise ValueError(f"Variance estimate must be non-negative for {calculation.statistical_type}, got {calculation.variance_estimate}")

        if calculation.statistical_type == MetricStatisticalType.PROPORTION:
            result = calculate_sample_size_proportion(
                p1=calculation.baseline_value,
                mde=calculation.mde,
                alpha=calculation.significance_level,
                power=calculation.power,
                ratio=calculation.ratio
            )

        elif calculation.statistical_type == MetricStatisticalType.CONTINUOUS_MEAN:

            std = math.sqrt(calculation.variance_estimate)
            result = calculate_sample_size_continuous(
                mean1=calculation.baseline_value,
                mde=calculation.mde,
                std=std,
                alpha=calculation.significance_level,
                power=calculation.power,
                ratio=calculation.ratio
            )

        elif calculation.statistical_type == MetricStatisticalType.RATIO:

            result = calculate_sample_size_ratio(
                ratio1=calculation.baseline_value,
                mde=calculation.mde,
                variance=calculation.variance_estimate,
                alpha=calculation.significance_level,
                power=calculation.power,
                ratio_groups=calculation.ratio
            )

        else:

            std = math.sqrt(calculation.variance_estimate)
            result = calculate_sample_size_continuous(
                mean1=calculation.baseline_value,
                mde=calculation.mde,
                std=std,
                alpha=calculation.significance_level,
                power=calculation.power,
                ratio=calculation.ratio
            )

        daily_control = calculation.expected_daily_users * (1 / (1 + calculation.ratio))
        daily_treatment = calculation.expected_daily_users * (calculation.ratio / (1 + calculation.ratio))

        days_control = result["control"] / daily_control
        days_treatment = result["treatment"] / daily_treatment

        days_needed = math.ceil(max(days_control, days_treatment))

        return {
            "sample_size": result,
            "days_needed": days_needed,
            "expected_daily_users": calculation.expected_daily_users,
            "statistical_type": calculation.statistical_type.value,
            "calculation_details": {
                "baseline": calculation.baseline_value,
                "mde": calculation.mde,
                "significance_level": calculation.significance_level,
                "power": calculation.power,
                "variance_estimate": calculation.variance_estimate
            }
        }

    @staticmethod
    async def calculate_all_sample_sizes(params: TestParameters) -> Dict[str, Any]:
        """Расчет размера выборки для основной метрики (первой с is_primary=True)"""
        primary_metrics = [m for m in params.metrics if m.is_primary]
        if not primary_metrics:
             # Хотя валидация TestParameters должна это проверять, на всякий случай
             return {
                "results": [],
                "total_primary_metrics": 0,
                "parameters": {}
             }

        main_metric = primary_metrics[0]
        results = []
        custom = main_metric.custom_metric
        control_traffic = params.variations[0].traffic_percentage
        treatment_traffic = params.variations[1].traffic_percentage
        ratio = treatment_traffic / control_traffic

        try:
            calculation = SampleSizeCalculation(
                metric_id="primary",
                statistical_type=custom.statistical_type,
                baseline_value=custom.baseline_value,
                mde=params.mde,
                significance_level=params.significance_level,
                power=params.power,
                variance_estimate=custom.variance_estimate,
                ratio=ratio,
                expected_daily_users=params.expected_daily_users
            )

            size_result = await MetricService.calculate_sample_size(calculation)

            results.append({
                "metric_name": custom.description or "Основная метрика",
                "metric_id": "primary",
                "is_primary": True,
                "sample_size": size_result["sample_size"],
                "days_needed": size_result["days_needed"],
                "planned_days": params.planned_duration_days,
                "sufficient": size_result["days_needed"] <= params.planned_duration_days,
                "calculation_details": size_result["calculation_details"],
                "error": None # Явно указываем отсутствие ошибки
            })
        except Exception as e:
            logger.error(f"Ошибка расчета выборки для основной метрики: {e}")
            # ИСПРАВЛЕНО: Возвращаем структуру, соответствующую схеме StatisticalResultItem
            results.append({
                "metric_name": custom.description or "Основная метрика",
                "metric_id": "primary",
                "is_primary": True,
                "sample_size": None, # Допускается None в обновленной схеме
                "days_needed": None,
                "planned_days": params.planned_duration_days,
                "sufficient": False,
                "calculation_details": {},
                "error": str(e) # Записываем текст ошибки
            })

        return {
            "results": results,
            "total_primary_metrics": len([m for m in params.metrics if m.purpose == MetricPurpose.PRIMARY]),
            "parameters": {
                "mde": params.mde,
                "significance_level": params.significance_level,
                "power": params.power,
                "expected_daily_users": params.expected_daily_users,
                "planned_duration_days": params.planned_duration_days
            }
        }

    @staticmethod
    def process_metrics(metrics: List[MetricSelection]) -> List[Dict[str, Any]]:
        processed_metrics = []
        for i, metric in enumerate(metrics):
            custom = metric.custom_metric
            metric_data = {
                "metric_id": f"custom_{i}",
                "statistical_type": custom.statistical_type,
                "purpose": metric.purpose.value,
                "is_primary": metric.is_primary,
                "description": custom.description,
                "sql_query": custom.sql_query,
                "baseline_value": custom.baseline_value or 0.0,
                "variance_estimate": custom.variance_estimate or 0.0,
                "source": "custom",
                "distribution": custom.distribution,
                "variance_assumption": custom.variance_assumption,
                "outliers": custom.outliers,
            }

            data_characteristics = {
                "non_normal": custom.distribution == "non_normal",
                "equal_var": custom.variance_assumption == "equal",
                "outliers_significant": custom.outliers == "significant"
            }

            test_config = recommend_statistical_test(
                custom.statistical_type,
                data_characteristics=data_characteristics
            )
            metric_data["statistical_test"] = test_config

            processed_metrics.append(metric_data)
        return processed_metrics