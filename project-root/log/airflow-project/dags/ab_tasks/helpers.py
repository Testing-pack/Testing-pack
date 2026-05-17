import re
import logging
from enum import Enum
from minio import Minio
from airflow.exceptions import AirflowException
import os

logger = logging.getLogger(__name__)


class StatisticalTest(str, Enum):
    STUDENT_T_TEST = "student_t_test"
    WELCH_T_TEST = "welch_t_test"
    LINEARIZED_Z_TEST = "linearized_z_test"
    Z_TEST_PROPORTION = "z_test_proportion"
    BOOTSTRAP = "bootstrap"


class MetricStatisticalType(str, Enum):
    PROPORTION = "proportion"
    CONTINUOUS_MEAN = "continuous_mean"
    RATIO = "ratio"

def get_minio_client():
    try:
        client = Minio(
            endpoint=os.getenv('MINIO_ENDPOINT', 'minio:9000'),
            access_key=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
            secret_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin123'),
            secure=os.getenv('MINIO_SECURE', 'false').lower() == 'true'
        )
        logger.info("MinIO клиент создан успешно")
        return client
    except Exception as e:
        logger.error(f"Ошибка создания MinIO клиента: {e}")
        raise AirflowException(f"Ошибка создания MinIO клиента: {e}")


def split_ratio_sql(sql_query: str) -> tuple:
    """
    Разделяет SQL-запрос для ratio-метрики на два запроса: для числителя и знаменателя.
    Ожидается структура: SELECT key1, key2, expr1 / expr2 AS alias FROM ... GROUP BY ...
    Возвращает (numerator_sql, denominator_sql).
    """
    sql = re.sub(r'\s+', ' ', sql_query.strip())
    from_idx = sql.upper().find(' FROM ')
    if from_idx == -1:
        raise ValueError("Не найден FROM в запросе")

    select_part = sql[:from_idx].replace('SELECT', '', 1).strip()
    from_where_group = sql[from_idx:].strip()

    parts = []
    current = ''
    paren_level = 0
    for ch in select_part:
        if ch == '(':
            paren_level += 1
            current += ch
        elif ch == ')':
            paren_level -= 1
            current += ch
        elif ch == ',' and paren_level == 0:
            parts.append(current.strip())
            current = ''
        else:
            current += ch
    if current:
        parts.append(current.strip())

    if len(parts) < 3:
        raise ValueError("Недостаточно полей в SELECT. Ожидается минимум два ключа и выражение с делением.")

    expr_part = parts[-1]
    as_idx = expr_part.upper().find(' AS ')
    if as_idx != -1:
        expr_part = expr_part[:as_idx].strip()

    paren_level = 0
    div_pos = -1
    for i, ch in enumerate(expr_part):
        if ch == '(':
            paren_level += 1
        elif ch == ')':
            paren_level -= 1
        elif ch == '/' and paren_level == 0:
            div_pos = i
            break

    if div_pos == -1:
        raise ValueError("Не найден оператор деления в выражении")

    numerator_expr = expr_part[:div_pos].strip()
    denominator_expr = expr_part[div_pos + 1:].strip()

    key_fields = parts[:-1]
    key_fields_clean = [k.strip() for k in key_fields]

    select_numerator = "SELECT " + ", ".join(key_fields_clean + [numerator_expr + " AS numerator"])
    select_denominator = "SELECT " + ", ".join(key_fields_clean + [denominator_expr + " AS denominator"])

    numerator_sql = select_numerator + " " + from_where_group
    denominator_sql = select_denominator + " " + from_where_group

    return numerator_sql, denominator_sql