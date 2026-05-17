import logging
import pandas as pd
from io import BytesIO
from airflow.exceptions import AirflowException
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.trino.hooks.trino import TrinoHook
from minio.error import S3Error
from pyspark.sql import SparkSession
from pyspark.conf import SparkConf
import os

from ab_tasks.helpers import get_minio_client

logger = logging.getLogger(__name__)


def verify_silver_bucket_exists():
    """Проверяет существование бакета silver-layer и создаёт его при необходимости."""
    try:
        minio_client = get_minio_client()
        bucket_name = "silver-layer"
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            logger.info(f"Бакет {bucket_name} создан")
        else:
            logger.info(f"Бакет {bucket_name} существует")
    except Exception as e:
        logger.error(f"Ошибка при проверке бакета silver-layer: {e}")
        raise AirflowException(f"Ошибка при проверке бакета silver-layer: {e}")


def verify_gold_bucket_exists():
    """Проверяет существование бакета gold-layer и создаёт его при необходимости."""
    try:
        minio_client = get_minio_client()
        bucket_name = "gold-layer"
        if not minio_client.bucket_exists(bucket_name):
            try:
                minio_client.make_bucket(bucket_name)
                logger.info(f"Бакет {bucket_name} создан")
            except S3Error as e:
                if e.code == 'BucketAlreadyOwnedByYou':
                    logger.info(f"Бакет {bucket_name} уже существует (подтверждено при создании)")
                else:
                    raise
        else:
            logger.info(f"Бакет {bucket_name} существует")
    except Exception as e:
        logger.error(f"Ошибка при проверке бакета gold-layer: {e}")
        raise AirflowException(f"Ошибка при проверке бакета gold-layer: {e}")


def check_verified_files_count():
    """Проверяет количество файлов со статусом 'verified' в базе."""
    try:
        pg_hook = PostgresHook(postgres_conn_id='postgres_default')
        connection = pg_hook.get_conn()
        cursor = connection.cursor()
        query = """
        SELECT COUNT(*) as total_verified,
               COUNT(CASE WHEN file_format = 'csv' THEN 1 END) as csv_count,
               COUNT(CASE WHEN file_format != 'csv' THEN 1 END) as other_count
        FROM file_uploads
        WHERE upload_status = 'verified'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            total_verified, csv_count, other_count = result
            logger.info("СТАТИСТИКА ПО ФАЙЛАМ:")
            logger.info(f"Всего файлов со статусом 'verified': {total_verified}")
            logger.info(f"CSV файлов для преобразования: {csv_count}")
            logger.info(f"Других форматов: {other_count}")
        else:
            logger.info("Файлов со статусом 'verified' не найдено")
        cursor.close()
        connection.close()
    except Exception as e:
        logger.error(f"Ошибка при проверке файлов: {e}")
        raise AirflowException(f"Ошибка при проверке файлов: {e}")


def ensure_iceberg_silver_table(**context):
    """
    Создает схему и таблицу Iceberg для серебряного слоя.
    """
    trino_hook = TrinoHook(trino_conn_id='trino_default')

    sql_schema = """
    CREATE SCHEMA IF NOT EXISTS iceberg.silver
    WITH (location = 's3://silver-layer/')
    """
    trino_hook.run(sql_schema)
    logger.info("Схема iceberg.silver проверена/создана")

    sql_table = """
    CREATE TABLE IF NOT EXISTS iceberg.silver.silver_data (
        id VARCHAR,
        user_id VARCHAR,
        test_id VARCHAR,
        var_id VARCHAR,
        event_name VARCHAR,
        event_time TIMESTAMP,
        event_value DOUBLE,
        experiment_id VARCHAR,
        source_bronze_id VARCHAR,
        original_file_name VARCHAR
    )
    WITH (
        format = 'PARQUET',
        partitioning = ARRAY['experiment_id']
    )
    """
    trino_hook.run(sql_table)
    logger.info("Таблица iceberg.silver.silver_data проверена/создана")


def process_verified_files_to_siver_iceberg(**context):
    """
    Читает файлы, применяет маппинг и записывает в Iceberg таблицу через PySpark.
    Использует S3A (Hadoop) для работы с MinIO.
    """
    REQUIRED_TARGETS = {'id', 'user_id', 'test_id', 'var_id', 'event_name', 'event_time', 'event_value'}


    s3a_access = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
    s3a_secret = os.getenv('MINIO_SECRET_KEY', 'minioadmin123')
    jdbc_user = os.getenv('ICEBERG_JDBC_USER', 'airflow')
    jdbc_pass = os.getenv('ICEBERG_JDBC_PASSWORD', 'airflow')

    conf = SparkConf() \
        .setAppName("Airflow_Bronze_to_Silver") \
        .setMaster("spark://spark-master:7077") \
        .set("spark.jars.packages",
             "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,"
             "org.postgresql:postgresql:42.7.3,"
             "org.apache.hadoop:hadoop-aws:3.3.4,"
             "com.amazonaws:aws-java-sdk-bundle:1.12.262") \
        .set("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog") \
        .set("spark.sql.catalog.iceberg.type", "jdbc") \
        .set("spark.sql.catalog.iceberg.uri", "jdbc:postgresql://postgres:5432/airflow") \
        .set("spark.sql.catalog.iceberg.jdbc.user", jdbc_user) \
        .set("spark.sql.catalog.iceberg.jdbc.password", jdbc_pass) \
        .set("spark.sql.catalog.iceberg.warehouse", "s3a://silver-layer/") \
        .set("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
        .set("spark.hadoop.fs.s3a.access.key", s3a_access) \
        .set("spark.hadoop.fs.s3a.secret.key", s3a_secret) \
        .set("spark.hadoop.fs.s3a.path.style.access", "true") \
        .set("spark.hadoop.fs.s3.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")

    spark = SparkSession.builder.config(conf=conf).getOrCreate()

    try:
        minio_client = get_minio_client()
        bronze_bucket_name = "bronze-layer"

        pg_hook = PostgresHook(postgres_conn_id='postgres_default')
        connection = pg_hook.get_conn()
        cursor = connection.cursor()

        query = """
        SELECT upload_id, file_name, file_format, s3_path, 
               original_hash_sha256, file_size_bytes, experiment_id, mapping_id
        FROM file_uploads
        WHERE upload_status = 'verified'
        ORDER BY uploaded_at DESC
        """
        cursor.execute(query)
        verified_files = cursor.fetchall()

        if not verified_files:
            logger.info("Файлов со статусом 'verified' не найдено")
            cursor.close()
            connection.close()
            spark.stop()
            return

        logger.info(f"Найдено {len(verified_files)} файлов для обработки")
        processed_count = 0

        for upload_id, file_name, file_format, s3_path, original_hash, file_size, experiment_id, mapping_id in verified_files:
            try:
                if experiment_id is None:
                    raise ValueError("experiment_id is NULL")

                response = minio_client.get_object(bronze_bucket_name, s3_path)
                file_content = response.read()
                response.close()
                response.release_conn()

                if file_format.lower() == 'csv':
                    df_pandas = pd.read_csv(BytesIO(file_content))
                else:
                    df_pandas = pd.read_parquet(BytesIO(file_content))

                if file_format.lower() == 'csv' and mapping_id:
                    cursor.execute(
                        "SELECT input_field_name, target_field, transformation_rules FROM mapping_fields WHERE mapping_id = %s",
                        (mapping_id,))
                    mapping_fields = cursor.fetchall()
                    if mapping_fields:
                        target_fields_in_mapping = {field[1] for field in mapping_fields}
                        missing_required = REQUIRED_TARGETS - target_fields_in_mapping
                        if missing_required:
                            raise ValueError(f"Mapping missing: {missing_required}")

                        input_to_target = {field[0]: field[1] for field in mapping_fields}
                        df_pandas.rename(columns=input_to_target, inplace=True)

                        if 'event_time' in df_pandas.columns:
                            df_pandas['event_time'] = pd.to_datetime(df_pandas['event_time'], errors='coerce')
                        if 'event_value' in df_pandas.columns:
                            df_pandas['event_value'] = pd.to_numeric(df_pandas['event_value'], errors='coerce')

                elif file_format.lower() == 'csv' and not mapping_id:
                    raise ValueError("CSV requires mapping")

                df_pandas['experiment_id'] = str(experiment_id)
                df_pandas['source_bronze_id'] = str(upload_id)
                df_pandas['original_file_name'] = file_name

                for col in REQUIRED_TARGETS:
                    if col not in df_pandas.columns:
                        df_pandas[col] = None

                final_cols = ['id', 'user_id', 'test_id', 'var_id', 'event_name', 'event_time',
                              'event_value', 'experiment_id', 'source_bronze_id', 'original_file_name']
                df_pandas = df_pandas[final_cols]

                df_spark = spark.createDataFrame(df_pandas)
                df_spark.writeTo("iceberg.silver.silver_data").append()

                logger.info(f"Файл #{upload_id} успешно записан в Iceberg через Spark")
                cursor.execute("UPDATE file_uploads SET upload_status = 'processed' WHERE upload_id = %s", (upload_id,))
                connection.commit()
                processed_count += 1

            except Exception as e:
                logger.error(f"Ошибка файла #{upload_id}: {e}")
                connection.rollback()
                cursor.execute(
                    "UPDATE file_uploads SET upload_status = 'failed', description = %s WHERE upload_id = %s",
                    (str(e)[:200], upload_id))
                connection.commit()

        cursor.close()
        connection.close()
        spark.stop()
        logger.info(f"Завершено. Обработано: {processed_count}")

    except Exception as e:
        logger.error(f"Глобальная ошибка: {e}")
        if 'spark' in locals(): spark.stop()
        raise AirflowException(str(e))