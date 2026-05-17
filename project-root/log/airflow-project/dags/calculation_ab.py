"""
process_bronze_to_silver_dag.py
DAG для обработки файлов из бронзы в серебро, подготовки пользовательских данных
и выполнения статистических тестов с загрузкой результатов в ClickHouse.
Данные в серебряном слое сохраняются партицированно по experiment_id.
Используется Trino для чтения серебра и записи в Iceberg (золотой слой).
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Импортируем функции из вынесенных модулей
from ab_tasks.bronze_to_silver_tasks import (
    verify_silver_bucket_exists,
    verify_gold_bucket_exists,
    check_verified_files_count,
    ensure_iceberg_silver_table,
    process_verified_files_to_siver_iceberg
)
from ab_tasks.gold_layer_tasks import prepare_gold_layer_with_trino
from ab_tasks.statistics_tasks import run_statistical_tests_from_iceberg
from ab_tasks.alert_tasks import analyze_results_and_send_alerts


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
    'email_on_retry': False,
}


with DAG(
        'calculation_ab',
        default_args=default_args,
        description='Чтение verified файлов из бронзы, преобразование в Parquet (с партиционированием по experiment_id), подготовка пользовательских данных и статистические тесты',
        schedule_interval=timedelta(minutes=15),
        catchup=False,
        max_active_runs=1,
        tags=['minio', 'postgres', 'silver', 'clickhouse', 'statistics', 'gold', 'trino', 'iceberg'],
) as dag:
    check_bucket_task = PythonOperator(
        task_id='verify_silver_bucket_exists',
        python_callable=verify_silver_bucket_exists,
    )

    check_gold_bucket_task = PythonOperator(
        task_id='verify_gold_bucket_exists',
        python_callable=verify_gold_bucket_exists,
    )

    ensure_iceberg_table_task = PythonOperator(
        task_id='ensure_hive_silver_table',
        python_callable=ensure_iceberg_silver_table,
    )

    check_files_task = PythonOperator(
        task_id='check_verified_files_count',
        python_callable=check_verified_files_count,
    )

    process_files_task = PythonOperator(
        task_id='process_verified_files_to_silver',
        python_callable=process_verified_files_to_siver_iceberg,
    )

    prepare_gold_layer_task = PythonOperator(
        task_id='prepare_gold_layer_with_trino',
        python_callable=prepare_gold_layer_with_trino,
    )

    run_tests_task = PythonOperator(
        task_id='run_statistical_tests',
        python_callable=run_statistical_tests_from_iceberg,
    )

    analyze_alerts_task = PythonOperator(
        task_id='analyze_results_and_send_alerts',
        python_callable=analyze_results_and_send_alerts,
    )

    [check_bucket_task, check_gold_bucket_task] >> ensure_iceberg_table_task >> check_files_task >> process_files_task
    process_files_task >> prepare_gold_layer_task >> run_tests_task >> analyze_alerts_task