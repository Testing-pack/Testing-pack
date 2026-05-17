import re
import logging
import pandas as pd
import numpy as np
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.trino.hooks.trino import TrinoHook

from ab_tasks.helpers import split_ratio_sql, MetricStatisticalType

logger = logging.getLogger(__name__)


def prepare_gold_layer_with_trino(**context):
    """
    Для каждого эксперимента выполняет SQL-запросы метрик
    через Trino и сохраняет результаты в Iceberg таблицы (золотой слой).
    Использует пакетную вставку для ускорения.
    """
    pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    trino_hook = TrinoHook(trino_conn_id='trino_default')

    with pg_hook.get_conn() as pg_conn:
        with pg_conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT e.test_id
                FROM experiment_metrics em
                JOIN experiments e ON em.test_id = e.test_id
                WHERE e.status = 'active'
            """)
            experiments = [row[0] for row in cur.fetchall()]

    if not experiments:
        logger.info("Нет экспериментов для обработки")
        return

    trino_hook.run("CREATE SCHEMA IF NOT EXISTS iceberg.gold WITH (location='s3://gold-layer/')")

    for exp_id in experiments:
        logger.info(f"Обработка эксперимента {exp_id}")
        safe_exp_id = exp_id.replace('-', '_')

        with pg_hook.get_conn() as pg_conn:
            with pg_conn.cursor() as cur:
                cur.execute("""
                    SELECT id, sql_query, statistical_type
                    FROM experiment_metrics
                    WHERE test_id = %s AND sql_query IS NOT NULL
                """, (exp_id,))
                metrics = cur.fetchall()

        for metric_id, sql_query, stat_type in metrics:
            try:
                replacement_table = f"(SELECT * FROM iceberg.silver.silver_data WHERE experiment_id = '{exp_id}')"
                pattern = r'(?i)(\bFROM\b|\bJOIN\b)\s+(?:iceberg\.silver\.)?silver_data\b'
                sql_final = re.sub(pattern, f"\\1 {replacement_table}", sql_query)

                target_table = f"iceberg.gold.metric_{safe_exp_id}_{metric_id}"

                if stat_type == MetricStatisticalType.RATIO.value:
                    num_sql, den_sql = split_ratio_sql(sql_final)
                    df_num = trino_hook.get_pandas_df(num_sql)
                    df_den = trino_hook.get_pandas_df(den_sql)

                    if df_num.empty or df_den.empty:
                        logger.warning(f"Пустой результат для метрики {metric_id}")
                        continue

                    result_df = pd.merge(df_num, df_den, on=['user_id', 'var_id'], how='inner')
                    result_df['experiment_id'] = exp_id
                    result_df = result_df[['user_id', 'var_id', 'numerator', 'denominator', 'experiment_id']]

                    create_sql = f"""
                    CREATE TABLE IF NOT EXISTS {target_table} (
                        user_id VARCHAR, var_id VARCHAR, numerator DOUBLE, denominator DOUBLE, experiment_id VARCHAR
                    ) WITH (format = 'PARQUET', partitioning = ARRAY['experiment_id'])
                    """
                    trino_hook.run(create_sql)
                    trino_hook.run(f"DELETE FROM {target_table} WHERE experiment_id = '{exp_id}'")

                    if not result_df.empty:
                        def fmt_val(v):
                            if pd.isna(v): return "NULL"
                            if isinstance(v, str):
                                safe_v = v.replace("'", "''")
                                return f"'{safe_v}'"
                            return str(v)

                        values_str = ", ".join([
                            f"({', '.join([fmt_val(x) for x in row])})"
                            for row in result_df.to_numpy()
                        ])
                        insert_sql = f"INSERT INTO {target_table} VALUES {values_str}"
                        trino_hook.run(insert_sql)

                else:
                    df = trino_hook.get_pandas_df(sql_final)
                    if df.empty:
                        logger.warning(f"Пустой результат для метрики {metric_id}")
                        continue

                    if 'user_id' not in df.columns or 'var_id' not in df.columns:
                        logger.error(f"Нет user_id или var_id")
                        continue

                    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                    value_cols = [c for c in numeric_cols if c not in ['user_id', 'var_id']]
                    if not value_cols:
                        logger.error(f"Нет числовых колонок")
                        continue

                    value_col = value_cols[0]
                    result_df = df[['user_id', 'var_id', value_col]].copy()
                    result_df.rename(columns={value_col: 'metric_value'}, inplace=True)
                    result_df['experiment_id'] = exp_id

                    create_sql = f"""
                    CREATE TABLE IF NOT EXISTS {target_table} (
                        user_id VARCHAR, var_id VARCHAR, metric_value DOUBLE, experiment_id VARCHAR
                    ) WITH (format = 'PARQUET', partitioning = ARRAY['experiment_id'])
                    """
                    trino_hook.run(create_sql)
                    trino_hook.run(f"DELETE FROM {target_table} WHERE experiment_id = '{exp_id}'")

                    if not result_df.empty:
                        def fmt_val(v):
                            if pd.isna(v): return "NULL"
                            if isinstance(v, str):
                                safe_v = v.replace("'", "''")
                                return f"'{safe_v}'"
                            return str(v)

                        values_str = ", ".join([
                            f"({', '.join([fmt_val(x) for x in row])})"
                            for row in result_df.to_numpy()
                        ])
                        insert_sql = f"INSERT INTO {target_table} VALUES {values_str}"
                        trino_hook.run(insert_sql)

                logger.info(f"Метрика {metric_id} сохранена в {target_table}")

            except Exception as e:
                logger.error(f"Ошибка обработки метрики {metric_id}: {e}")
                continue

    logger.info("Подготовка золотого слоя завершена")