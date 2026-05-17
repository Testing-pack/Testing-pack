# tests/test_main_service.py
import os
import sys
from pathlib import Path


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

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from main import app
from api.dependencies import (
    get_experiment_service,
    get_file_service,
    get_mapping_service,
)
from services.experiment_service import ExperimentService
from services.file_service import FileService
from services.mapping_service import MappingService
from services.metric_service import MetricService
from repositories.experiment_repository import ExperimentRepository
from repositories.file_upload_repository import FileUploadRepository
from repositories.mapping_repository import MappingRepository
from repositories.s3_repository import S3Repository
from schemas.experiment import (
    TestParameters,
    Hypothesis,
    Variation,
    DataSourceSelection,
    SampleSizeCalculation,
)
from schemas.metric import MetricSelection, CustomMetric
from schemas.mapping import MappingSchemaCreate, MappingFieldCreate
from core.enums import (
    MetricPurpose,
    MetricStatisticalType,
    StatisticalTest,
    DataSourceType,
    ExperimentStatus,
)
from models.experiment import Experiment
@pytest.fixture
def mock_db_session():
    """Асинхронная сессия БД."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def mock_experiment_repo(mock_db_session):
    return ExperimentRepository(mock_db_session)


@pytest.fixture
def mock_file_upload_repo(mock_db_session):
    return FileUploadRepository(mock_db_session)


@pytest.fixture
def mock_mapping_repo(mock_db_session):
    return MappingRepository(mock_db_session)


@pytest.fixture
def mock_s3_repo():
    repo = AsyncMock(spec=S3Repository)
    repo.ensure_bucket_exists = AsyncMock()
    repo.upload_file = AsyncMock()
    repo.download_file = AsyncMock()
    repo.object_exists = AsyncMock()
    repo.remove_object = AsyncMock()
    return repo


@pytest.fixture
def experiment_service(mock_db_session):
    return ExperimentService(mock_db_session)


@pytest.fixture
def file_service(mock_db_session, mock_s3_repo, mock_file_upload_repo):
    return FileService(
        db=mock_db_session,
        s3_repo=mock_s3_repo,
        file_upload_repo=mock_file_upload_repo,
    )


@pytest.fixture
def mapping_service(mock_db_session):
    return MappingService(mock_db_session)

SAMPLE_TEST_PARAMS = TestParameters(
    test_name="test",
    description="desc",
    owner="owner",
    hypothesis=Hypothesis(
        change_description="change",
        expected_impact="impact",
        measurement_method="method",
        h0="h0",
        h1="h1",
    ),
    variations=[
        Variation(name="control", traffic_percentage=50),
        Variation(name="test", traffic_percentage=50),
    ],
    metrics=[
        MetricSelection(
            custom_metric=CustomMetric(
                statistical_type=MetricStatisticalType.PROPORTION,
                purpose=MetricPurpose.PRIMARY,
                description="conversion",
                sql_query="SELECT 1",
                baseline_value=0.1,
            ),
            purpose=MetricPurpose.PRIMARY,
            is_primary=True,
        )
    ],
    data_source=DataSourceSelection(
        source_type=DataSourceType.INTERNAL_SPLITTING,
        source_id="internal_default",
    ),
    start_date=datetime.now(timezone.utc),
    planned_duration_days=14,
    significance_level=0.05,
    mde=0.05,
    power=0.8,
    expected_daily_users=1000,
)

@pytest.mark.asyncio
async def test_setup_test_success(experiment_service):
    with patch.object(
        experiment_service.repository, "save_experiment", new_callable=AsyncMock
    ) as mock_save:
        mock_save.return_value = True
        result = await experiment_service.setup_test(SAMPLE_TEST_PARAMS)

        assert result["test_id"] is not None
        assert result["status"] == ExperimentStatus.DRAFT.value
        config = result["test_configuration"]
        assert len(config["Варианты теста"]) == 2
        assert len(config["Метрики"]) == 1
        primary_metric = config["Метрики"][0]
        assert primary_metric["is_primary"] is True
        mock_save.assert_called_once()


@pytest.mark.asyncio
async def test_get_experiment_found(experiment_service, mock_db_session):
    mock_exp = MagicMock(spec=Experiment)
    mock_exp.test_id = "test-123"
    mock_exp.test_name = "test"
    mock_exp.owner = "owner"
    mock_exp.status = "active"
    mock_exp.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
    mock_exp.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    mock_exp.variations = []
    mock_exp.metrics = []

    with patch.object(
        experiment_service.repository,
        "get_experiment_with_details",
        return_value=mock_exp,
    ):
        result = await experiment_service.get_experiment("test-123")
        assert result is not None
        assert result["test_id"] == "test-123"


@pytest.mark.asyncio
async def test_get_experiment_found(experiment_service, mock_db_session):
    mock_exp = MagicMock(spec=Experiment)

    mock_exp.test_id = "test-123"
    mock_exp.test_name = "test"
    mock_exp.owner = "owner"
    mock_exp.status = "active"
    mock_exp.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
    mock_exp.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    mock_exp.variations = []
    mock_exp.metrics = []

    mock_exp.hypothesis_change_description = "change"
    mock_exp.hypothesis_expected_impact = "impact"
    mock_exp.hypothesis_measurement_method = "method"
    mock_exp.hypothesis_h0 = "h0"
    mock_exp.hypothesis_h1 = "h1"

    mock_exp.sample_size_control = 1000
    mock_exp.sample_size_treatment = 1000
    mock_exp.sample_size_total = 2000
    mock_exp.days_needed = 2
    mock_exp.planned_duration_days = 14

    mock_exp.start_date = datetime.now(timezone.utc)
    mock_exp.end_date = None
    mock_exp.significance_level = 0.05
    mock_exp.mde = 0.05
    mock_exp.power = 0.8
    mock_exp.expected_daily_users = 1000

    mock_exp.source_type = "internal_splitting"
    mock_exp.source_id = "internal_default"
    mock_exp.source_name = "Default"
    mock_exp.source_description = ""
    mock_exp.source_platform = None
    mock_exp.source_contact_person = None
    mock_exp.source_additional_info = None

    with patch.object(
            experiment_service.repository,
            "get_experiment_with_details",
            return_value=mock_exp,
    ):
        result = await experiment_service.get_experiment("test-123")
        assert result is not None
        assert result["test_id"] == "test-123"
        assert "test_configuration" in result
        assert result["status"] == "active"

@pytest.mark.asyncio
async def test_calculate_sample_size_proportion():
    calc = SampleSizeCalculation(
        metric_id="test",
        statistical_type=MetricStatisticalType.PROPORTION,
        baseline_value=0.1,
        mde=0.05,
        significance_level=0.05,
        power=0.8,
        expected_daily_users=1000,
    )
    result = await MetricService.calculate_sample_size(calc)
    assert "sample_size" in result
    assert "days_needed" in result
    assert result["sample_size"]["total"] > 0
    assert result["days_needed"] >= 0


@pytest.mark.asyncio
async def test_calculate_all_sample_sizes(experiment_service):
    with patch.object(
        MetricService,
        "calculate_sample_size",
        return_value={
            "sample_size": {"control": 1000, "treatment": 1000, "total": 2000},
            "days_needed": 2,
            "expected_daily_users": 1000,
            "statistical_type": "proportion",
            "calculation_details": {},
        },
    ):
        result = await MetricService.calculate_all_sample_sizes(SAMPLE_TEST_PARAMS)
        assert "results" in result
        assert len(result["results"]) == 1
        assert result["results"][0]["is_primary"] is True
        assert result["results"][0]["sample_size"]["total"] == 2000

@pytest.mark.asyncio
async def test_analyze_csv(file_service):
    csv_content = b"header1,header2\nval1,val2\nval3,val4\n"
    analysis = await file_service._analyze_csv(csv_content)
    assert analysis["row_count"] == 2
    assert analysis["headers"] == ["header1", "header2"]
    assert len(analysis["sample_data"]) == 2


@pytest.fixture
def client(mock_db_session, mock_s3_repo, mock_file_upload_repo):
    """Подменяем сервисы в зависимостях."""
    async def get_override_experiment_service():
        svc = ExperimentService(mock_db_session)
        svc.repository = AsyncMock()
        return svc

    async def get_override_file_service():
        return FileService(
            db=mock_db_session,
            s3_repo=mock_s3_repo,
            file_upload_repo=mock_file_upload_repo,
        )

    async def get_override_mapping_service():
        return MappingService(mock_db_session)

    app.dependency_overrides[get_experiment_service] = get_override_experiment_service
    app.dependency_overrides[get_file_service] = get_override_file_service
    app.dependency_overrides[get_mapping_service] = get_override_mapping_service

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_get_all_experiments(client):
    with patch(
        "services.experiment_service.ExperimentService.get_all_experiments",
        return_value=[
            {
                "test_id": "exp-1",
                "test_name": "Test",
                "owner": "owner",
                "status": "active",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "variations_count": 2,
                "metrics_count": 1,
                "planned_duration": 14,
            }
        ],
    ):
        response = client.get("/experiments/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["experiments"][0]["test_id"] == "exp-1"


def test_get_experiment_404(client):
    with patch(
        "services.experiment_service.ExperimentService.get_experiment",
        return_value=None,
    ):
        response = client.get("/experiments/non-existent")
        assert response.status_code == 404


def test_create_experiment_invalid(client):
    invalid_data = {"test_name": "missing owner and variations"}
    response = client.post("/experiments/setup_test", json=invalid_data)
    assert response.status_code == 422


def test_get_available_metrics(client):
    response = client.get("/metrics/available")
    assert response.status_code == 200
    data = response.json()
    assert "predefined_metrics" in data
    assert "metric_purposes" in data


def test_get_available_data_sources(client):
    response = client.get("/available_data_sources")
    assert response.status_code == 200
    data = response.json()
    assert "predefined_data_sources" in data
    assert "data_source_types" in data