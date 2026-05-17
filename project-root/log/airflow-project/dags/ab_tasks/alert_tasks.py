import logging
from airflow.utils.email import send_email
from airflow.exceptions import AirflowException
from airflow.providers.postgres.hooks.postgres import PostgresHook
from clickhouse_driver import Client
import os

logger = logging.getLogger(__name__)


def analyze_results_and_send_alerts(**context):
    """
    Анализирует результаты статистических тестов и отправляет уведомления.
    """
    ti = context['ti']
    processed_exps = ti.xcom_pull(task_ids='run_statistical_tests', key='processed_experiments')
    if not processed_exps:
        logger.info("Нет обработанных экспериментов для анализа")
        return

    try:
        ch_client = Client(
            host=os.getenv('CH_HOST', 'clickhouse'),
            port=int(os.getenv('CH_PORT', 9000)),
            user=os.getenv('CH_USER', 'admin'),
            password=os.getenv('CH_PASSWORD', 'clickhouse123'),
            database=os.getenv('CH_DATABASE', 'default')
        )

        pg_hook = PostgresHook(postgres_conn_id='postgres_default')
        pg_conn = pg_hook.get_conn()
        pg_cursor = pg_conn.cursor()

        for exp_id in processed_exps:
            logger.info(f"Анализ эксперимента {exp_id}")

            pg_cursor.execute(
                "SELECT significance_level, test_name, owner FROM experiments WHERE test_id = %s",
                (exp_id,)
            )
            exp_row = pg_cursor.fetchone()
            if not exp_row:
                logger.warning(f"Эксперимент {exp_id} не найден в БД")
                continue
            significance_level, test_name, owner = exp_row
            recipient = owner if owner and '@' in owner else 'default@example.com'

            pg_cursor.execute(
                "SELECT id, purpose FROM experiment_metrics WHERE test_id = %s",
                (exp_id,)
            )
            metrics = pg_cursor.fetchall()
            if not metrics:
                logger.warning(f"Нет метрик для эксперимента {exp_id}")
                continue
            metric_purpose = {m[0]: m[1] for m in metrics}

            if not metric_purpose:
                continue

            metric_ids_list = list(metric_purpose.keys())
            query = """
                SELECT id, p_value
                FROM test_results
                WHERE experiment_id = %(exp_id)s AND id IN %(metric_ids)s
            """
            params = {'exp_id': exp_id, 'metric_ids': metric_ids_list}
            rows = ch_client.execute(query, params)
            results = {row[0]: row[1] for row in rows}

            alerts = []

            if not results:
                alerts.append("Данные для анализа отсутствуют (возможно, тесты не были выполнены).")
            else:
                for metric_id, p_value in results.items():
                    purpose = metric_purpose.get(metric_id)
                    if purpose == 'guardrail' and p_value <= 0.005:
                        alerts.append(
                            f"Guardrail метрика '{metric_id}' имеет p-value = {p_value:.4f} (≤0.005) – значимое ухудшение."
                        )
                    elif purpose == 'proxy' and p_value <= 0.001:
                        alerts.append(
                            f"Proxy метрика '{metric_id}' имеет p-value = {p_value:.4f} (≤0.001) – значимое улучшение. Возможно, стоит рассмотреть раннюю остановку эксперимента."
                        )

                primary_metric_id = None
                primary_p = None
                guardrail_significant = False
                for metric_id, p_value in results.items():
                    purpose = metric_purpose.get(metric_id)
                    if purpose == 'primary':
                        primary_metric_id = metric_id
                        primary_p = p_value
                    elif purpose == 'guardrail' and p_value <= 0.05:
                        guardrail_significant = True

                if primary_metric_id and primary_p is not None:
                    if primary_p <= significance_level and not guardrail_significant:
                        alerts.append(
                            f"Primary метрика '{primary_metric_id}' значима (p={primary_p:.4f} ≤ {significance_level}) и guardrail метрики не значимы. Эксперимент можно завершать."
                        )

                if not alerts:
                    alerts.append(" Значимых изменений не обнаружено.")

            subject = f"Результаты эксперимента {test_name} (ID: {exp_id})"
            body = f"<h3>Анализ эксперимента {test_name}</h3><ul>"
            for a in alerts:
                body += f"<li>{a}</li>"
            body += "</ul><p>С уважением,<br>Система A/B-тестирования</p>"

            try:
                send_email(to=recipient, subject=subject, html_content=body)
                logger.info(f"Уведомление отправлено владельцу {recipient} для эксперимента {exp_id}")
            except Exception as e:
                logger.error(f"Ошибка отправки email для {recipient}: {e}")

        pg_cursor.close()
        pg_conn.close()
        ch_client.disconnect()

    except Exception as e:
        logger.error(f"Ошибка в analyze_results_and_send_alerts: {e}")
        raise AirflowException("Не удалось выполнить анализ и отправить уведомления")