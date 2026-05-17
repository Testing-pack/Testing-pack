from typing import Dict, Any
from schemas.metric import StatisticalTestConfig
from core.enums import MetricStatisticalType, StatisticalTest

def recommend_statistical_test(
        metric_type: MetricStatisticalType,
        data_characteristics: Dict[str, Any] = None
) -> StatisticalTestConfig:
    if data_characteristics is None:
        data_characteristics = {}

    non_normal = data_characteristics.get("non_normal", False)
    equal_var = data_characteristics.get("equal_var", True)
    outliers_significant = data_characteristics.get("outliers_significant", False)

    if metric_type == MetricStatisticalType.PROPORTION:
        return StatisticalTestConfig(
            test_type=StatisticalTest.Z_TEST_PROPORTION,
        )
    elif metric_type == MetricStatisticalType.CONTINUOUS_MEAN:
        if non_normal or outliers_significant:

            return StatisticalTestConfig(
                test_type=StatisticalTest.BOOTSTRAP,
            )
        else:
            if not equal_var:
                return StatisticalTestConfig(
                    test_type=StatisticalTest.WELCH_T_TEST,
                )
            else:
                return StatisticalTestConfig(
                    test_type=StatisticalTest.STUDENT_T_TEST,
                )
    elif metric_type == MetricStatisticalType.RATIO:
        return StatisticalTestConfig(
            test_type=StatisticalTest.LINEARIZED_Z_TEST,
        )
    else:
        return StatisticalTestConfig(
            test_type=StatisticalTest.BOOTSTRAP,
        )


def get_test_explanation(test_type: StatisticalTest, metric_type: MetricStatisticalType) -> str:
    explanations = {
        StatisticalTest.STUDENT_T_TEST: "t-тест Стьюдента для сравнения средних значений. Предполагает нормальность распределения и равенство дисперсий.",
        StatisticalTest.WELCH_T_TEST: "t-тест Уэлча для сравнения средних значений. Используется при неравных дисперсиях и/или разных размерах выборок.",
        StatisticalTest.Z_TEST_PROPORTION: "Z-тест для сравнения пропорций (конверсий). Используется для бинарных метрик с большими выборками.",
        StatisticalTest.BOOTSTRAP: "Бутстрап метод для оценки распределения статистики. Используется для нестандартных метрик или сложных статистик.",
        StatisticalTest.LINEARIZED_Z_TEST: "Метрика-отношение линеаризуется (дельта-метод), затем применяется z-тест для сравнения средних линеаризованных значений."
    }
    return explanations.get(test_type, "Тест выбран на основе типа метрики и характеристик данных.")