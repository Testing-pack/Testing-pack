import logging
from typing import List, Dict, Optional
import numpy as np
from scipy import stats
from scipy.stats import shapiro, levene
from statsmodels.stats.proportion import proportions_ztest
from clickhouse_driver import Client
from airflow.exceptions import AirflowException
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.trino.hooks.trino import TrinoHook
import os

from ab_tasks.helpers import MetricStatisticalType

logger = logging.getLogger(__name__)


def perform_statistical_test(test_type, control_values, treat_values, control_mean, treat_mean):
    """ Выполняет статистический тест для non-ratio метрик. """
    p_value = None
    effect_size = None
    ci_low = ci_high = None
    n_c = len(control_values)
    n_t = len(treat_values)

    test_type = test_type.lower()

    if test_type in ['student_t_test', 't-test', 'ttest']:
        stat, p_value = stats.ttest_ind(control_values, treat_values, equal_var=True)
        var_c = np.var(control_values, ddof=1)
        var_t = np.var(treat_values, ddof=1)
        pooled_std = np.sqrt(((n_c - 1) * var_c + (n_t - 1) * var_t) / (n_c + n_t - 2))
        effect_size = (treat_mean - control_mean) / pooled_std if pooled_std != 0 else 0
        se = pooled_std * np.sqrt(1 / n_c + 1 / n_t)
        dof = n_c + n_t - 2
        mean_diff = treat_mean - control_mean
        ci = stats.t.interval(0.95, dof, loc=mean_diff, scale=se)
        ci_low, ci_high = ci

    elif test_type in ['welch_t_test', 'welch']:
        stat, p_value = stats.ttest_ind(control_values, treat_values, equal_var=False)
        var_c = np.var(control_values, ddof=1)
        var_t = np.var(treat_values, ddof=1)
        pooled_std = np.sqrt(((n_c - 1) * var_c + (n_t - 1) * var_t) / (n_c + n_t - 2))
        effect_size = (treat_mean - control_mean) / pooled_std if pooled_std != 0 else 0
        se = np.sqrt(var_c / n_c + var_t / n_t)
        dof_numerator = (var_c / n_c + var_t / n_t) ** 2
        dof_denominator = ((var_c / n_c) ** 2 / (n_c - 1)) + ((var_t / n_t) ** 2 / (n_t - 1))
        dof = dof_numerator / dof_denominator
        mean_diff = treat_mean - control_mean
        ci = stats.t.interval(0.95, dof, loc=mean_diff, scale=se)
        ci_low, ci_high = ci

    elif test_type in ['z_test_proportion', 'ztest']:
        successes_control = int(sum(control_values))
        successes_treat = int(sum(treat_values))
        nobs_control = len(control_values)
        nobs_treat = len(treat_values)
        count = [successes_control, successes_treat]
        nobs = [nobs_control, nobs_treat]
        z_stat, p_value = proportions_ztest(count, nobs, alternative='two-sided')
        p1 = successes_control / nobs_control
        p2 = successes_treat / nobs_treat
        effect_size = p2 - p1
        se = np.sqrt(p1 * (1 - p1) / nobs_control + p2 * (1 - p2) / nobs_treat)
        ci_low = effect_size - 1.96 * se
        ci_high = effect_size + 1.96 * se

    elif test_type in ['bootstrap']:
        n_bootstrap = 1000
        np.random.seed(42)
        boot_diffs = []
        for _ in range(n_bootstrap):
            boot_control = np.random.choice(control_values, size=n_c, replace=True)
            boot_treat = np.random.choice(treat_values, size=n_t, replace=True)
            boot_diffs.append(np.mean(boot_treat) - np.mean(boot_control))
        boot_diffs = np.array(boot_diffs)
        p_value = 2 * min(np.mean(boot_diffs >= 0), np.mean(boot_diffs <= 0))
        effect_size = treat_mean - control_mean
        ci_low, ci_high = np.percentile(boot_diffs, [2.5, 97.5])

    else:
        logger.error(f"Неизвестный тип теста: {test_type}")
        return None

    if p_value is None:
        logger.error(f"Тест {test_type} не вернул p-value")
        return None

    return {
        'p_value': p_value,
        'effect_size': effect_size if effect_size is not None else 0.0,
        'ci_low': ci_low,
        'ci_high': ci_high
    }


def perform_ratio_statistical_test(
        control_num: List[float],
        control_den: List[float],
        treat_num: List[float],
        treat_den: List[float],
        test_type: str = 'linearized_z_test'
) -> Optional[Dict[str, float]]:
    """ Выполняет линеаризованный тест для ratio-метрик. """
    sum_den_c = sum(control_den)
    sum_den_t = sum(treat_den)

    if sum_den_c == 0 or sum_den_t == 0:
        logger.warning("Сумма знаменателей равна нулю в одной из групп.")
        return None

    total_num = sum(control_num) + sum(treat_num)
    total_den = sum_den_c + sum_den_t

    if total_den == 0:
        logger.warning("Общий знаменатель равен нулю.")
        return None

    R = total_num / total_den
    y_control = [n - R * d for n, d in zip(control_num, control_den)]
    y_treat = [n - R * d for n, d in zip(treat_num, treat_den)]

    stat, p_value = stats.ttest_ind(y_control, y_treat, equal_var=False)

    control_ratio = sum(control_num) / sum_den_c
    treat_ratio = sum(treat_num) / sum_den_t

    abs_effect = treat_ratio - control_ratio
    rel_effect = abs_effect / control_ratio if control_ratio != 0 else 0

    se = np.sqrt(np.var(y_control, ddof=1) / len(y_control) + np.var(y_treat, ddof=1) / len(y_treat))
    dof = len(y_control) + len(y_treat) - 2
    mean_diff_lin = np.mean(y_treat) - np.mean(y_control)

    ci = stats.t.interval(0.95, dof, loc=mean_diff_lin, scale=se)
    ci_low, ci_high = ci

    return {
        'p_value': p_value,
        'effect_size': rel_effect,
        'diff': abs_effect,
        'ci_low': ci_low,
        'ci_high': ci_high
    }


def run_statistical_tests_from_iceberg(**context):
    """
    Читает предагрегированные данные из Iceberg таблиц (золотой слой) через Trino,
    выполняет статистические тесты и сохраняет результаты в ClickHouse.
    """
    try:

        ch_client = Client(
            host=os.getenv('CH_HOST', 'clickhouse'),
            port=int(os.getenv('CH_PORT', 9000)),
            user=os.getenv('CH_USER', 'admin'),
            password=os.getenv('CH_PASSWORD', 'clickhouse123'),
            database=os.getenv('CH_DATABASE', 'default')
        )
        logger.info("Подключение к ClickHouse установлено")

        pg_hook = PostgresHook(postgres_conn_id='postgres_default')
        trino_hook = TrinoHook(trino_conn_id='trino_default')

        with pg_hook.get_conn() as pg_conn:
            with pg_conn.cursor() as pg_cursor:
                pg_cursor.execute("SELECT DISTINCT test_id FROM experiment_metrics")
                experiments = pg_cursor.fetchall()

                processed_experiments = set()
                for (exp_id,) in experiments:
                    processed_experiments.add(exp_id)
                    logger.info(f"\nАнализ эксперимента {exp_id}")

                    safe_exp_id = exp_id.replace('-', '_')

                    pg_cursor.execute("""
                        SELECT id, recommended_test, statistical_type
                        FROM experiment_metrics
                        WHERE test_id = %s
                    """, (exp_id,))
                    metrics_info = pg_cursor.fetchall()
                    if not metrics_info:
                        logger.warning(f"Для эксперимента {exp_id} нет метрик")
                        continue

                    pg_cursor.execute("""
                        SELECT variation_id, name
                        FROM experiment_variations
                        WHERE test_id = %s
                    """, (exp_id,))
                    variations = pg_cursor.fetchall()
                    if not variations:
                        logger.warning(f"Для эксперимента {exp_id} нет вариаций")
                        continue

                    control_var = None
                    treatment_vars = []
                    for var_id, name in variations:
                        if var_id == 'A':
                            control_var = 'control'
                        else:
                            treatment_vars = ['treatment']

                    if control_var is None:
                        logger.warning(f"Не найдена контрольная группа для {exp_id}")
                        continue

                    for metric_id, recommended_test, stat_type in metrics_info:
                        if not recommended_test or not recommended_test.strip():
                            logger.warning(f"  Для метрики {metric_id} не указан recommended_test, пропускаем")
                            continue

                        logger.info(f"  Метрика ID: {metric_id}, тип: {stat_type}, тест: {recommended_test}")

                        table_name = f"iceberg.gold.metric_{safe_exp_id}_{metric_id}"

                        try:
                            df = trino_hook.get_pandas_df(f"SELECT * FROM {table_name}")
                        except Exception as e:
                            logger.error(f"    Не удалось прочитать таблицу {table_name}: {e}")
                            continue

                        if df.empty:
                            logger.warning(f"    Таблица {table_name} пуста")
                            continue

                        if stat_type == MetricStatisticalType.RATIO.value:
                            required_cols = {'user_id', 'var_id', 'numerator', 'denominator'}
                        else:
                            required_cols = {'user_id', 'var_id', 'metric_value'}

                        if not required_cols.issubset(df.columns):
                            missing = required_cols - set(df.columns)
                            logger.error(f"    Отсутствуют колонки: {missing}")
                            continue

                        control_data = df[df['var_id'] == control_var]
                        if control_data.empty:
                            logger.warning(f"    Нет данных для контрольной группы {control_var}")
                            continue

                        if stat_type == MetricStatisticalType.RATIO.value:
                            control_num = control_data['numerator'].tolist()
                            control_den = control_data['denominator'].tolist()
                        else:
                            control_values = control_data['metric_value'].tolist()
                            control_mean = np.mean(control_values) if control_values else 0.0

                        for treat_var in treatment_vars:
                            treat_data = df[df['var_id'] == treat_var]
                            if treat_data.empty:
                                logger.warning(f"    Нет данных для вариации {treat_var}")
                                continue

                            if stat_type == MetricStatisticalType.RATIO.value:
                                treat_num = treat_data['numerator'].tolist()
                                treat_den = treat_data['denominator'].tolist()
                                if len(control_num) == 0 or len(treat_num) == 0:
                                    continue
                                result = perform_ratio_statistical_test(
                                    control_num, control_den,
                                    treat_num, treat_den,
                                    test_type=recommended_test
                                )
                                control_mean_val = sum(control_num) / sum(control_den) if sum(control_den) > 0 else 0
                                treat_mean_val = sum(treat_num) / sum(treat_den) if sum(treat_den) > 0 else 0
                            else:
                                treat_values = treat_data['metric_value'].tolist()
                                treat_mean = np.mean(treat_values) if treat_values else 0.0
                                if len(control_values) == 0 or len(treat_values) == 0:
                                    continue
                                result = perform_statistical_test(
                                    test_type=recommended_test.strip().lower(),
                                    control_values=control_values,
                                    treat_values=treat_values,
                                    control_mean=control_mean,
                                    treat_mean=treat_mean
                                )
                                control_mean_val = control_mean
                                treat_mean_val = treat_mean

                            if result is None:
                                logger.warning(f"    Тест не удался для метрики {metric_id}")
                                continue

                            ch_client.execute("""
                                INSERT INTO test_results
                                (experiment_id, id, test_type, p_value, effect_size,
                                 ci_low, ci_high, control_mean, treatment_mean)
                                VALUES
                            """, [{
                                'experiment_id': str(exp_id),
                                'id': str(metric_id),
                                'test_type': recommended_test.strip().lower(),
                                'p_value': float(result['p_value']),
                                'effect_size': float(result['effect_size']),
                                'ci_low': float(result['ci_low']) if result['ci_low'] is not None else 0.0,
                                'ci_high': float(result['ci_high']) if result['ci_high'] is not None else 0.0,
                                'control_mean': float(control_mean_val),
                                'treatment_mean': float(treat_mean_val)
                            }])
                            logger.info(
                                f"    Результат сохранён: p_value={result['p_value']:.4f}, "
                                f"эффект={result['effect_size']:.4f}"
                            )

        context['ti'].xcom_push(key='processed_experiments', value=list(processed_experiments))
        ch_client.disconnect()
        logger.info("Статистические тесты завершены")

    except Exception as e:
        logger.error(f"Ошибка в run_statistical_tests_from_iceberg: {e}")
        raise AirflowException(f"Ошибка выполнения статистических тестов: {e}")