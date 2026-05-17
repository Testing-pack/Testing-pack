import os
import sys
from pathlib import Path


def pytest_configure(config):
    """Выполняется ДО сбора тестов — настраиваем окружение и пути"""

    for k, v in {
        "POSTGRESQL_HOST": "localhost",
        "POSTGRESQL_PORT": "5432",
        "POSTGRESQL_NAME": "test_db",
        "POSTGRESQL_USER": "test_user",
        "POSTGRESQL_PASS": "test_pass",
        "MINIO_ENDPOINT": "localhost:9000",
        "MINIO_ACCESS_KEY": "minioadmin",
        "MINIO_SECRET_KEY": "minioadmin",
        "MINIO_BUCKET_NAME": "test-bucket",
        "MINIO_BASE_PATH": "",
        "MINIO_SECURE": "false",
    }.items():
        os.environ.setdefault(k, str(v))

    BASE_DIR = Path(__file__).resolve().parent.parent
    APP_DIR = BASE_DIR / "main-service" / "backend" / "app"

    if str(APP_DIR) not in sys.path:
        sys.path.insert(0, str(APP_DIR))

