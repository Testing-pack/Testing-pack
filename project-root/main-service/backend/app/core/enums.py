from enum import Enum

class MetricPurpose(str, Enum):
    PRIMARY = "primary"
    GUARDRAIL = "guardrail"
    PROXY = "proxy"
    INFO = "info"


class MetricStatisticalType(str, Enum):
    PROPORTION = "proportion"
    RATIO = "ratio"
    CONTINUOUS_MEAN = "continuous_mean"
    NON_STANDARD = "non_standard"


class StatisticalTest(str, Enum):
    STUDENT_T_TEST = "student_t_test"
    WELCH_T_TEST = "welch_t_test"
    LINEARIZED_Z_TEST = "linearized_z_test"
    Z_TEST_PROPORTION = "z_test_proportion"
    BOOTSTRAP = "bootstrap"


class DataSourceType(str, Enum):
    INTERNAL_SPLITTING = "internal_splitting"
    EXTERNAL_SPLITTING = "external_splitting"


class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
