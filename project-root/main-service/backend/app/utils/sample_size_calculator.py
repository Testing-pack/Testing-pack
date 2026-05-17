import math
from scipy import stats
from typing import Dict

import math
from scipy import stats
from typing import Dict


def calculate_sample_size_proportion(
        p1: float,
        mde: float,
        alpha: float,
        power: float,
        ratio: float = 1.0
) -> Dict[str, float]:
    """Расчет размера выборки для пропорций (конверсий)"""
    p2 = p1 * (1 + mde)
    q1 = 1 - p1
    q2 = 1 - p2
    p_bar = (p1 + p2 * ratio) / (1 + ratio)
    q_bar = 1 - p_bar
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)

    numerator = (z_alpha * math.sqrt(p_bar * q_bar * (1 + 1 / ratio)) +
                 z_beta * math.sqrt(p1 * q1 + p2 * q2 / ratio)) ** 2
    denominator = (p1 - p2) ** 2

    n_control = numerator / denominator  # Явно переименовали для ясности

    return {
        "control": math.ceil(n_control),
        "treatment": math.ceil(n_control * ratio),
        "total": math.ceil(n_control * (1 + ratio))
    }


def calculate_sample_size_continuous(
        mean1: float,
        mde: float,
        std: float,
        alpha: float,
        power: float,
        ratio: float = 1.0
) -> Dict[str, float]:
    """Расчет размера выборки для непрерывных метрик"""
    mean2 = mean1 * (1 + mde)
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)

    numerator = (std ** 2) * (1 + 1 / ratio) * (z_alpha + z_beta) ** 2
    denominator = (mean1 - mean2) ** 2

    n_control = numerator / denominator

    return {
        "control": math.ceil(n_control),
        "treatment": math.ceil(n_control * ratio),
        "total": math.ceil(n_control * (1 + ratio))
    }


def calculate_sample_size_ratio(
        ratio1: float,
        mde: float,
        variance: float,
        alpha: float,
        power: float,
        ratio_groups: float = 1.0
) -> Dict[str, float]:
    """Расчет размера выборки для метрик-отношений"""
    ratio2 = ratio1 * (1 + mde)
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    se = math.sqrt(variance)

    numerator = (se ** 2) * (1 + 1 / ratio_groups) * (z_alpha + z_beta) ** 2
    denominator = (ratio1 - ratio2) ** 2

    n_control = numerator / denominator

    return {
        "control": math.ceil(n_control),
        "treatment": math.ceil(n_control * ratio_groups),
        "total": math.ceil(n_control * (1 + ratio_groups))
    }