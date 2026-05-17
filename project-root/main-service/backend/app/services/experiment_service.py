import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession


from schemas.experiment import TestParameters, DataSourceSelection
from schemas.metric import MetricSelection
from core.enums import DataSourceType, ExperimentStatus, MetricPurpose
from core.predefined_sources import PREDEFINED_DATA_SOURCES
from services.metric_service import MetricService
from repositories.experiment_repository import ExperimentRepository
from models.experiment import Experiment, ExperimentVariation, ExperimentMetric

from core.predefined_metrics import PREDEFINED_METRICS
from core.enums import MetricStatisticalType
from utils.statistical_tests import recommend_statistical_test

logger = logging.getLogger(__name__)


class ExperimentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = ExperimentRepository(db)

    async def setup_test(self, params: TestParameters) -> Dict[str, Any]:
        """Создание конфигурации A/B теста"""
        test_id = str(uuid.uuid4())
        end_date = params.start_date + timedelta(days=params.planned_duration_days)

        processed_metrics = MetricService.process_metrics(params.metrics)

        sample_size_results = await MetricService.calculate_all_sample_sizes(params)

        processed_data_source = self._process_data_source(params.data_source)

        # Подумать нужны ли все параметры через репу запроса к базе данных
        result = {
            "test_id": test_id,
            "status": ExperimentStatus.DRAFT.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "test_configuration": {
                "Основные параметры": {
                    "Название теста": params.test_name,
                    "Описание": params.description,
                    "Владелец": params.owner,
                    "Гипотеза": params.hypothesis.dict()
                },
                "Источник данных": processed_data_source,
                "Варианты теста": [
                    {
                        "var_test_id": chr(65 + i),
                        "Название": var.name,
                        "Процент трафика": var.traffic_percentage
                    } for i, var in enumerate(params.variations)
                ],
                "Метрики": processed_metrics,
                "Статистические расчеты": sample_size_results,
                "Параметры запуска": {
                    "Дата старта": params.start_date.isoformat(),
                    "Дата окончания": end_date.isoformat(),
                    "Длительность (дни)": params.planned_duration_days,
                    "Уровень значимости": params.significance_level,
                    "MDE": params.mde,
                    "Мощность теста": params.power,
                    "Ожидаемое кол-во пользователей в день": params.expected_daily_users
                }
            },
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "version": "1.0.0"
            }
        }

        # Сохранение в базу данных
        await self.repository.save_experiment(test_id, result)

        return result


#
    async def get_experiment(self, test_id: str) -> Optional[Dict[str, Any]]:
        experiment_details = await self.repository.get_experiment_with_details(test_id)
        if not experiment_details:
            return None

        return self._build_experiment_response(experiment_details)

    def _build_experiment_response(
            self,
            experiment: Experiment
    ) -> Dict[str, Any]:
        """
        Формирует ответ для клиента, используя новые скалярные поля.
        Безопасно обрабатывает NULL-значения.
        """
        # --- Гипотеза ---
        hypothesis = {}
        if experiment.hypothesis_change_description:
            hypothesis = {
                "change_description": experiment.hypothesis_change_description,
                "expected_impact": experiment.hypothesis_expected_impact,
                "measurement_method": experiment.hypothesis_measurement_method,
                "h0": experiment.hypothesis_h0,
                "h1": experiment.hypothesis_h1
            }

        main_params = {
            "Название теста": experiment.test_name,
            "Описание": experiment.description or "",
            "Владелец": experiment.owner,
            "Гипотеза": hypothesis,
        }

        variations_list = []
        for idx, var in enumerate(experiment.variations or []):
            variations_list.append({
                "var_test_id": var.variation_id or chr(65 + idx),
                "Название": var.name,
                "Процент трафика": var.traffic_percentage,
            })

        metrics_list = []
        for metric in experiment.metrics or []:
            source = "predefined" if metric.metric_id in PREDEFINED_METRICS else "custom"

            metric_dict = {
                "metric_id": metric.metric_id,
                "purpose": metric.purpose,
                "is_primary": metric.is_primary,
                "description": metric.description,
                "sql_query": metric.sql_query,
                "baseline_value": metric.baseline_value,
                "statistical_type": metric.statistical_type,
                "variance_estimate": metric.variance_estimate,
                "source": source,
                "distribution": metric.distribution or "unknown",
                "variance_assumption": metric.variance_assumption or "unknown",
                "outliers": metric.outliers or "insignificant",
                "statistical_test": None,
                "recommended_test": metric.recommended_test,
            }

            if source == "predefined":
                predef = PREDEFINED_METRICS.get(metric.metric_id, {})
                metric_dict["statistical_type"] = predef.get("statistical_type", MetricStatisticalType.PROPORTION).value
                metric_dict["variance_estimate"] = predef.get("variance_estimate", 0.0)

            try:
                stat_type = MetricStatisticalType(metric_dict["statistical_type"])
                test_config = recommend_statistical_test(stat_type)
                metric_dict["statistical_test"] = test_config.dict()
            except Exception:
                pass

            metrics_list.append(metric_dict)

        # --- Параметры запуска ---
        launch_params = {
            "Дата старта": experiment.start_date.isoformat() if experiment.start_date else None,
            "Дата окончания": experiment.end_date.isoformat() if experiment.end_date else None,
            "Длительность (дни)": experiment.planned_duration_days,
            "Уровень значимости": experiment.significance_level,
            "MDE": experiment.mde,
            "Мощность теста": experiment.power,
            "Ожидаемое кол-во пользователей в день": experiment.expected_daily_users,
        }

        # --- Источник данных ---
        data_source = {}
        if experiment.source_type:
            data_source = {
                "source_type": experiment.source_type,
                "source_id": experiment.source_id,
                "name": experiment.source_name,
                "description": experiment.source_description,
                "platform": experiment.source_platform,
                "contact_person": experiment.source_contact_person,
                "additional_info": experiment.source_additional_info
            }
        else:
            # Для старых экспериментов (до миграции) возвращаем заглушку
            data_source = {
                "source_type": "internal_splitting",
                "name": "Сплитование нашей системой (по умолчанию)",
                "description": "Стандартное сплитование через нашу платформу",
                "source_id": "internal_default",
            }

        # --- Статистические расчёты ---
        statistics = {
            "results": [],
            "total_primary_metrics": len([m for m in experiment.metrics or [] if m.is_primary]),
            "parameters": {
                "mde": experiment.mde,
                "significance_level": experiment.significance_level,
                "power": experiment.power,
                "expected_daily_users": experiment.expected_daily_users,
                "planned_duration_days": experiment.planned_duration_days,
            },
        }

        if experiment.sample_size_control is not None:
            # Формируем результат для основной метрики (предполагаем, что она одна)
            # Можно улучшить, если в будущем понадобится несколько метрик, но пока так.
            statistics["results"].append({
                "metric_name": "Основная метрика",  # можно взять из первой primary метрики, если нужно
                "metric_id": "primary",
                "is_primary": True,
                "sample_size": {
                    "control": experiment.sample_size_control,
                    "treatment": experiment.sample_size_treatment,
                    "total": experiment.sample_size_total
                },
                "days_needed": experiment.days_needed,
                "planned_days": experiment.planned_duration_days,
                "sufficient": (experiment.days_needed is not None and
                               experiment.planned_duration_days is not None and
                               experiment.days_needed <= experiment.planned_duration_days),
                "calculation_details": {}
            })

        test_configuration = {
            "Основные параметры": main_params,
            "Источник данных": data_source,
            "Варианты теста": variations_list,
            "Метрики": metrics_list,
            "Параметры запуска": launch_params,
            "Статистические расчеты": statistics,
        }

        return {
            "test_id": experiment.test_id,
            "status": experiment.status,
            "created_at": experiment.created_at.isoformat() if experiment.created_at else None,
            "updated_at": experiment.updated_at.isoformat() if experiment.updated_at else None,
            "test_configuration": test_configuration,
            "metadata": {
                "created_at": experiment.created_at.isoformat() if experiment.created_at else None,
                "updated_at": experiment.updated_at.isoformat() if experiment.updated_at else None,
                "version": "1.0.0",
            },
        }
#
    async def get_all_experiments(self) -> List[Dict[str, Any]]:
        """Получение всех экспериментов"""
        experiments = await self.repository.get_all_experiments()

        result = []
        for exp in experiments:
            details = await self.repository.get_experiment_with_details(exp.test_id)

            result.append({
                "test_id": exp.test_id,
                "test_name": exp.test_name,
                "owner": exp.owner,
                "status": exp.status,
                "created_at": exp.created_at.isoformat() if exp.created_at else None,
                "updated_at": exp.updated_at.isoformat() if exp.updated_at else None,
                "variations_count": len(details.variations or []),
                "metrics_count": len(details.metrics or []),
                "planned_duration": exp.planned_duration_days
            })

        return result
#
    async def delete_experiment(self, test_id: str) -> bool:
        """Удаление эксперимента"""
        return await self.repository.delete_experiment(test_id)
#
    async def update_experiment_status(self, test_id: str, status: str) -> bool:
        """Обновление статуса эксперимента"""
        return await self.repository.update_experiment_status(test_id, status)


    def _process_data_source(self, data_source: DataSourceSelection) -> Dict[str, Any]:
        """Обработка источника данных"""
        if data_source.source_type == DataSourceType.INTERNAL_SPLITTING:
            predefined_source = PREDEFINED_DATA_SOURCES.get(data_source.source_id, {})
            return {
                "source_type": DataSourceType.INTERNAL_SPLITTING.value,
                "name": predefined_source.get("name", "Сплитование нашей системой"),
                "description": predefined_source.get("description", "Стандартное сплитование через нашу платформу"),
                "source_id": data_source.source_id
            }
        else:
            external_info = data_source.external_source_info or {}
            return {
                "source_type": DataSourceType.EXTERNAL_SPLITTING.value,
                "name": external_info.get("name", "Стороннее сплитование"),
                "description": external_info.get("description", "Сплитование выполняется внешней системой"),
                "platform": external_info.get("platform", ""),
                "contact_person": external_info.get("contact_person", ""),
                "additional_info": external_info.get("additional_info", "")
            }

    def _convert_to_experiment_dict(self, experiment, variations=None, metrics=None) -> Dict[str, Any]:
        """Преобразование модели Experiment в словарь"""
        if isinstance(experiment, dict):
            return experiment

        # Если это модель SQLAlchemy
        variations_list = []
        if variations is not None:
            for var in variations:
                variations_list.append({
                    "id": var.id,
                    "test_id": var.test_id,
                    "variation_id": var.variation_id,
                    "name": var.name,
                    "traffic_percentage": var.traffic_percentage
                })

        metrics_list = []
        if metrics is not None:
            for metric in metrics:
                metrics_list.append({
                    "id": metric.id,
                    "test_id": metric.test_id,
                    "metric_id": metric.metric_id,
                    "purpose": metric.purpose,
                    "is_primary": metric.is_primary,
                    "description": metric.description,
                    "baseline_value": metric.baseline_value,
                    "sql_query": metric.sql_query
                })

        return {
            "test_id": experiment.test_id,
            "test_name": experiment.test_name,
            "description": experiment.description,
            "owner": experiment.owner,
            "status": experiment.status,
            "start_date": experiment.start_date.isoformat() if experiment.start_date else None,
            "end_date": experiment.end_date.isoformat() if experiment.end_date else None,
            "planned_duration_days": experiment.planned_duration_days,
            "significance_level": experiment.significance_level,
            "mde": experiment.mde,
            "power": experiment.power,
            "expected_daily_users": experiment.expected_daily_users,
            "created_at": experiment.created_at.isoformat() if experiment.created_at else None,
            "updated_at": experiment.updated_at.isoformat() if experiment.updated_at else None,
            "variations": variations_list,
            "metrics": metrics_list
        }
