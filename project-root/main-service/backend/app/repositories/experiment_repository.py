import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
import uuid

from models.experiment import Experiment, ExperimentVariation, ExperimentMetric

logger = logging.getLogger(__name__)


class ExperimentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_experiment(self, test_id: str, experiment_data: dict) -> bool:
        """Сохранить эксперимент в базу данных"""
        try:
            main_params = experiment_data["test_configuration"]["Основные параметры"]
            launch_params = experiment_data["test_configuration"]["Параметры запуска"]
            test_config = experiment_data["test_configuration"]
            variations = test_config["Варианты теста"]
            metrics = test_config["Метрики"]

            hypothesis = main_params.get("Гипотеза", {})
            hypothesis_change_desc = hypothesis.get("change_description")
            hypothesis_expected_impact = hypothesis.get("expected_impact")
            hypothesis_measurement_method = hypothesis.get("measurement_method")
            hypothesis_h0 = hypothesis.get("h0")
            hypothesis_h1 = hypothesis.get("h1")

            # --- Источник данных ---
            data_source = test_config.get("Источник данных", {})
            source_type = data_source.get("source_type")
            source_id = data_source.get("source_id")
            source_name = data_source.get("name")
            source_description = data_source.get("description")
            source_platform = data_source.get("platform")
            source_contact_person = data_source.get("contact_person")
            source_additional_info = data_source.get("additional_info")

            statistical_calculations = test_config.get("Статистические расчеты", {})
            results = statistical_calculations.get("results", [])

            sample_size_control = None
            sample_size_treatment = None
            sample_size_total = None
            days_needed = None

            if results:
                primary_result = results[0]

                sample_size_data = primary_result.get("sample_size")

                if isinstance(sample_size_data, dict):
                    sample_size_control = sample_size_data.get("control")
                    sample_size_treatment = sample_size_data.get("treatment")
                    sample_size_total = sample_size_data.get("total")

                days_needed = primary_result.get("days_needed")

            start_date_str = launch_params["Дата старта"]
            end_date_str = launch_params["Дата окончания"]

            if 'T' in start_date_str:
                if start_date_str.endswith('Z'):
                    start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                else:
                    start_date = datetime.fromisoformat(start_date_str)
                start_date = start_date.replace(tzinfo=None)
            else:
                start_date = datetime.fromisoformat(start_date_str)

            if 'T' in end_date_str:
                if end_date_str.endswith('Z'):
                    end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                else:
                    end_date = datetime.fromisoformat(end_date_str)
                end_date = end_date.replace(tzinfo=None)
            else:
                end_date = datetime.fromisoformat(end_date_str)

            now = datetime.utcnow()

            experiment = Experiment(
                test_id=test_id,
                test_name=main_params["Название теста"],
                description=main_params["Описание"],
                owner=main_params["Владелец"],
                status=experiment_data.get("status", "draft"),
                start_date=start_date,
                end_date=end_date,
                planned_duration_days=launch_params["Длительность (дни)"],
                significance_level=launch_params["Уровень значимости"],
                mde=launch_params["MDE"],
                power=launch_params["Мощность теста"],
                expected_daily_users=launch_params["Ожидаемое кол-во пользователей в день"],

                hypothesis_change_description=hypothesis_change_desc,
                hypothesis_expected_impact=hypothesis_expected_impact,
                hypothesis_measurement_method=hypothesis_measurement_method,
                hypothesis_h0=hypothesis_h0,
                hypothesis_h1=hypothesis_h1,

                source_type=source_type,
                source_id=source_id,
                source_name=source_name,
                source_description=source_description,
                source_platform=source_platform,
                source_contact_person=source_contact_person,
                source_additional_info=source_additional_info,

                sample_size_control=sample_size_control,
                sample_size_treatment=sample_size_treatment,
                sample_size_total=sample_size_total,
                days_needed=days_needed,

                created_at=now,
                updated_at=now
            )
            self.session.add(experiment)

            variations = experiment_data["test_configuration"]["Варианты теста"]
            for var in variations:
                variation = ExperimentVariation(
                    test_id=test_id,
                    variation_id=var["var_test_id"],
                    name=var["Название"],
                    traffic_percentage=var["Процент трафика"]
                )
                self.session.add(variation)

            metrics = experiment_data["test_configuration"]["Метрики"]
            for metric in metrics:

                statistical_test = metric.get("statistical_test")
                recommended_test = (
                    statistical_test.test_type.value
                    if statistical_test and hasattr(statistical_test, "test_type")
                    else None
                )

                exp_metric = ExperimentMetric(
                    test_id=test_id,
                    metric_id=metric.get("metric_id", f"custom_{uuid.uuid4().hex}"),
                    purpose=metric.get("purpose", ""),
                    is_primary=metric.get("is_primary", False),
                    description=metric.get("description", ""),
                    baseline_value=metric.get("baseline_value", 0.0),
                    sql_query=metric.get("sql_query", ""),
                    distribution=metric.get("distribution", "unknown"),
                    variance_assumption=metric.get("variance_assumption", "unknown"),
                    outliers=metric.get("outliers", "insignificant"),
                    statistical_type=metric.get("statistical_type", "proportion"),
                    variance_estimate=metric.get("variance_estimate", 0.0),
                    recommended_test = recommended_test,
                )
                self.session.add(exp_metric)

            await self.session.commit()
            logger.info(f"Эксперимент {test_id} сохранен в БД")
            return True

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка сохранения эксперимента в БД: {e}")
            raise

    #
    async def get_experiment(self, test_id: str) -> Optional[Experiment]:
        """Получить эксперимент из базы данных"""
        try:
            result = await self.session.execute(
                select(Experiment)
                .options(
                    selectinload(Experiment.variations),
                    selectinload(Experiment.metrics)
                )
                .where(Experiment.test_id == test_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Ошибка получения эксперимента из БД: {e}")
            raise

    #
    async def get_experiment_with_details(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Получить эксперимент со всеми деталями"""
        try:
            result = await self.session.execute(
                select(Experiment)
                .options(
                    selectinload(Experiment.variations),
                    selectinload(Experiment.metrics)
                )
                .where(Experiment.test_id == test_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Ошибка получения эксперимента с деталями: {e}")
            raise

    #
    async def get_all_experiments(self) -> List[Experiment]:
        """Получить все эксперименты из базы данных"""
        try:
            result = await self.session.execute(
                select(Experiment)
                .order_by(Experiment.created_at.desc())
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Ошибка получения экспериментов из БД: {e}")
            raise

    #
    async def delete_experiment(self, test_id: str) -> bool:
        """Удалить эксперимент из базы данных"""
        try:
            await self.session.execute(
                delete(Experiment).where(Experiment.test_id == test_id)
            )
            await self.session.commit()
            logger.info(f"Эксперимент {test_id} удален из БД")
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка удаления эксперимента из БД: {e}")
            raise

    #
    async def update_experiment_status(self, test_id: str, status: str) -> bool:
        """Обновить статус эксперимента"""
        try:
            update_values = {
                "status": status,
                "updated_at": datetime.utcnow()
            }

            if status == "completed":
                update_values["end_date"] = datetime.utcnow()

            await self.session.execute(
                update(Experiment)
                .where(Experiment.test_id == test_id)
                .values(**update_values)
            )
            await self.session.commit()
            logger.info(f"Статус эксперимента {test_id} обновлен на '{status}'")
            return True

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка обновления статуса эксперимента: {e}")
            raise