from core.enums import DataSourceType

PREDEFINED_DATA_SOURCES = {
    "internal_default": {
        "name": "Сплитование нашей системой (основное)",
        "description": "Стандартное сплитование пользователей через нашу платформу",
        "source_type": DataSourceType.INTERNAL_SPLITTING
    },
    "internal_mobile": {
        "name": "Сплитование нашей системой (мобильные)",
        "description": "Сплитование только мобильных пользователей",
        "source_type": DataSourceType.INTERNAL_SPLITTING
    }
}