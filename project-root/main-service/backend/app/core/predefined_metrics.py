from core.enums import MetricStatisticalType, MetricPurpose, StatisticalTest

registration_conversion = {
        "statistical_type": MetricStatisticalType.PROPORTION,
        "purpose": MetricPurpose.PRIMARY,
        "description": "Конверсия в регистрацию",
        "recommended_test": StatisticalTest.Z_TEST_PROPORTION,
        "sql_template": """
SELECT 
    user_id, 
    var_id, 
    MAX(CASE WHEN event_name = 'registration' THEN 1 ELSE 0 END) AS metric_value 
FROM silver_data 
GROUP BY user_id, var_id
                        """,
        "baseline_value": 0.03,
        "variance_estimate": 0.0001
    }

purchase_conversion = {
        "statistical_type": MetricStatisticalType.PROPORTION,
        "purpose": MetricPurpose.PRIMARY,
        "description": "Конверсия в покупку",
        "recommended_test": StatisticalTest.Z_TEST_PROPORTION,
        "sql_template": """
SELECT 
    user_id, 
    var_id, 
    MAX(CASE WHEN event_name = 'purchase' THEN 1 ELSE 0 END) AS metric_value 
FROM silver_data 
GROUP BY user_id, var_id
                        """,
        "baseline_value": 0.03,
        "variance_estimate": 0.0001
    }

button_click_conversion = {
        "statistical_type": MetricStatisticalType.PROPORTION,
        "purpose": MetricPurpose.PROXY,
        "description": "Клики по кнопке",
        "recommended_test": StatisticalTest.Z_TEST_PROPORTION,
        "sql_template": """
SELECT 
    user_id, 
    var_id, 
    MAX(CASE WHEN event_name = 'click_button' THEN 1 ELSE 0 END) AS metric_value 
FROM silver_data 
GROUP BY user_id, var_id
                        """,
        "baseline_value": 0.15,
        "variance_estimate": 0.0009
    }

page_views_per_user = {
        "statistical_type": MetricStatisticalType.CONTINUOUS_MEAN,
        "purpose": MetricPurpose.INFO,
        "description": "Просмотры страниц на пользователя",
        "recommended_test": StatisticalTest.STUDENT_T_TEST,
        "sql_template": """
SELECT 
    user_id, 
    var_id, 
    COUNT(*) AS metric_value 
FROM silver_data 
WHERE event_name = 'page_view' 
GROUP BY user_id, var_id
                        """,
        "baseline_value": 5.0,
        "variance_estimate": 4.0
    }

revenue_per_user = {
        "statistical_type": MetricStatisticalType.CONTINUOUS_MEAN,
        "purpose": MetricPurpose.INFO,
        "description": "Суммарный доход",
        "recommended_test": StatisticalTest.STUDENT_T_TEST,
        "sql_template": """
SELECT 
    user_id, 
    var_id, 
    COALESCE(SUM(event_value), 0) AS metric_value 
FROM silver_data 
WHERE event_name = 'revenue' 
GROUP BY user_id, var_id
                        """,
        "baseline_value": 5.0,
        "variance_estimate": 4.0
    }

session_duration_per_user = {
        "statistical_type": MetricStatisticalType.CONTINUOUS_MEAN,
        "purpose": MetricPurpose.INFO,
        "description": "Суммарное время на сайте",
        "recommended_test": StatisticalTest.STUDENT_T_TEST,
        "sql_template": """
SELECT 
    user_id, 
    var_id, 
    COALESCE(SUM(event_value), 0) AS metric_value 
FROM silver_data 
WHERE event_name = 'session_duration' 
GROUP BY user_id, var_id
                        """,
        "baseline_value": 5.0,
        "variance_estimate": 4.0
    }


average_purchase_value = {
        "statistical_type": MetricStatisticalType.RATIO,
        "purpose": MetricPurpose.PRIMARY,
        "description": "Средний чек",
        "recommended_test": StatisticalTest.LINEARIZED_Z_TEST,
        "sql_template": """
SELECT 
    user_id, 
    var_id, 
    SUM(event_value) / COUNT(*) AS metric_value 
FROM silver_data 
WHERE event_name = 'purchase' 
GROUP BY user_id, var_id
                        """,
        "baseline_value": 25.0,
        "variance_estimate": 100.0
    }

purchase_conversion_per_session = {
        "statistical_type": MetricStatisticalType.RATIO,
        "purpose": MetricPurpose.PRIMARY,
        "description": "Конверсия в покупку на сессию",
        "recommended_test": StatisticalTest.LINEARIZED_Z_TEST,
        "sql_template": """
SELECT 
    user_id, 
    var_id, 
    COUNT(CASE WHEN event_name = 'purchase' THEN 1 END) * 1.0 / NULLIF(COUNT(CASE WHEN event_name = 'session_start' THEN 1 END), 0) AS metric_value 
FROM silver_data 
GROUP BY user_id, var_id
                        """,
        "baseline_value": 25.0,
        "variance_estimate": 100.0
    }

active_days_count = {
        "statistical_type": MetricStatisticalType.NON_STANDARD,
        "purpose": MetricPurpose.PRIMARY,
        "description": "Количество дней с активностью",
        "recommended_test": StatisticalTest.BOOTSTRAP,
        "sql_template": """
SELECT
    user_id, 
    var_id, 
    COUNT(DISTINCT DATE(event_time)) AS metric_value 
FROM silver_data 
GROUP BY user_id, var_id
                        """,
        "baseline_value": 25.0,
        "variance_estimate": 100.0
    }

max_purchase_value = {
        "statistical_type": MetricStatisticalType.NON_STANDARD,
        "purpose": MetricPurpose.PRIMARY,
        "description": "Максимальная сумма покупки за один раз",
        "recommended_test": StatisticalTest.BOOTSTRAP,
        "sql_template": """
SELECT 
    user_id, 
    var_id, 
    MAX(event_value) AS metric_value 
FROM silver_data 
WHERE event_name = 'purchase' 
GROUP BY user_id, var_id
                        """,
        "baseline_value": 25.0,
        "variance_estimate": 100.0
    }



PREDEFINED_METRICS = {
    "registration_conversion": registration_conversion,
    "purchase_conversion": purchase_conversion,
    "button_click_conversion": button_click_conversion,
    "page_views_per_user": page_views_per_user,
    "revenue_per_user": revenue_per_user,
    "session_duration_per_user": session_duration_per_user,
    "average_purchase_value": average_purchase_value,
    "purchase_conversion_per_session": purchase_conversion_per_session,
    "active_days_count": active_days_count,
    "max_purchase_value": max_purchase_value,

}


