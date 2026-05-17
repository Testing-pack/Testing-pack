import sys
from pathlib import Path
SPLIT_SERVICE_DIR = Path(__file__).resolve().parent.parent / "split-service"
sys.path.insert(0, str(SPLIT_SERVICE_DIR))
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from split_integration.app import app
from split_integration.dependencies import get_split_db
from split_integration.service import SplitService
from split_integration.repository import (
    ExperimentApiRepository,
    AssignmentRepository,
)
from split_integration.models import UserAssignment


@pytest.fixture
def mock_http_client():
    """Подменяем httpx.AsyncClient в ExperimentApiRepository."""
    with patch("split_integration.repository.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_db_session():
    """Асинхронная сессия БД."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def assignment_repo(mock_db_session):
    return AssignmentRepository(mock_db_session)



@pytest.mark.asyncio
async def test_get_assignment_found(assignment_repo, mock_db_session):
    test_id, user_id = "t1", "u1"
    fake_assignment = UserAssignment(
        id=1, test_id=test_id, user_id=user_id, variation_id="var-a"
    )
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = fake_assignment
    mock_db_session.execute.return_value = result_mock

    assignment = await assignment_repo.get_assignment(test_id, user_id)
    assert assignment == fake_assignment


@pytest.mark.asyncio
async def test_get_assignment_not_found(assignment_repo, mock_db_session):
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = result_mock

    assignment = await assignment_repo.get_assignment("t2", "u2")
    assert assignment is None


@pytest.mark.asyncio
async def test_create_assignment(assignment_repo, mock_db_session):
    test_id, user_id, variation_id = "t3", "u3", "var-x"
    await assignment_repo.create_assignment(test_id, user_id, variation_id)

    mock_db_session.add.assert_called_once()
    added_obj = mock_db_session.add.call_args[0][0]
    assert added_obj.test_id == test_id
    assert added_obj.user_id == user_id
    assert added_obj.variation_id == variation_id
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(added_obj)



ACTIVE_EXP_TEMPLATE = {
    "status": "active",
    "start_date": None,
    "end_date": None,
    "test_configuration": {
        "Варианты теста": [
            {"var_test_id": "v1", "Процент трафика": 30},
            {"var_test_id": "v2", "Процент трафика": 70},
        ]
    },
}


@pytest.fixture
def split_service(mock_db_session):
    return SplitService(mock_db_session)


def _naive_utc_now() -> datetime:
    """Возвращает текущее наивное UTC-время, аналог datetime.utcnow."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


@pytest.mark.asyncio
async def test_assign_user_experiment_not_found(split_service):
    with patch.object(
        split_service.experiment_repo,
        "get_experiment_with_variations",
        return_value=None,
    ):
        with pytest.raises(ValueError, match="не найден"):
            await split_service.assign_user("bad_id", "u1")


@pytest.mark.asyncio
async def test_assign_user_experiment_not_active(split_service):
    inactive_exp = {**ACTIVE_EXP_TEMPLATE, "status": "paused"}
    with patch.object(
        split_service.experiment_repo,
        "get_experiment_with_variations",
        return_value=inactive_exp,
    ):
        with pytest.raises(ValueError, match="не активен"):
            await split_service.assign_user("exp-1", "u1")


@pytest.mark.asyncio
async def test_assign_user_experiment_not_started(split_service):
    future = _naive_utc_now() + timedelta(days=1)
    not_started = {**ACTIVE_EXP_TEMPLATE, "start_date": future.isoformat()}

    with patch("split_integration.service.datetime") as mock_dt:
        mock_dt.utcnow.return_value = _naive_utc_now()
        mock_dt.fromisoformat = datetime.fromisoformat

        with patch.object(
            split_service.experiment_repo,
            "get_experiment_with_variations",
            return_value=not_started,
        ):
            with pytest.raises(ValueError, match="ещё не начался"):
                await split_service.assign_user("exp-1", "u1")


@pytest.mark.asyncio
async def test_assign_user_experiment_ended(split_service):
    past = _naive_utc_now() - timedelta(days=1)
    ended = {**ACTIVE_EXP_TEMPLATE, "end_date": past.isoformat()}

    with patch("split_integration.service.datetime") as mock_dt:
        mock_dt.utcnow.return_value = _naive_utc_now()
        mock_dt.fromisoformat = datetime.fromisoformat

        with patch.object(
            split_service.experiment_repo,
            "get_experiment_with_variations",
            return_value=ended,
        ):
            with pytest.raises(ValueError, match="уже завершён"):
                await split_service.assign_user("exp-1", "u1")


@pytest.mark.asyncio
async def test_assign_user_existing_assignment(split_service):
    existing_assignment = UserAssignment(
        test_id="exp-1", user_id="u1", variation_id="v1"
    )
    with patch.object(
        split_service.experiment_repo,
        "get_experiment_with_variations",
        return_value=ACTIVE_EXP_TEMPLATE,
    ), patch.object(
        split_service.assignment_repo,
        "get_assignment",
        return_value=existing_assignment,
    ):
        variation = await split_service.assign_user("exp-1", "u1")
        assert variation == "v1"


@pytest.mark.asyncio
async def test_assign_user_success_new_assignment(split_service):
    with patch.object(
        split_service.experiment_repo,
        "get_experiment_with_variations",
        return_value=ACTIVE_EXP_TEMPLATE,
    ), patch.object(
        split_service.assignment_repo, "get_assignment", return_value=None
    ), patch.object(
        split_service.assignment_repo, "create_assignment", AsyncMock()
    ) as mock_create:
        variation = await split_service.assign_user("exp-1", "new_user")
        assert variation in ["v1", "v2"]
        mock_create.assert_called_once_with("exp-1", "new_user", variation)



@pytest.fixture
def client(mock_db_session):
    async def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_split_db] = override_get_db
    with TestClient(app=app) as c:
        yield c
    app.dependency_overrides.clear()


def test_assign_endpoint_success(client, mock_http_client):
    exp_data = ACTIVE_EXP_TEMPLATE.copy()
    with patch(
        "split_integration.service.ExperimentApiRepository.get_experiment_with_variations",
        return_value=exp_data,
    ), patch(
        "split_integration.service.AssignmentRepository.get_assignment",
        return_value=None,
    ), patch(
        "split_integration.service.AssignmentRepository.create_assignment",
        new_callable=AsyncMock,
    ) as mock_create:
        response = client.post("/split/assign?test_id=exp-1&user_id=u1")
        assert response.status_code == 200
        data = response.json()
        assert data["test_id"] == "exp-1"
        assert data["user_id"] == "u1"
        assert data["variation_id"] in ["v1", "v2"]
        mock_create.assert_called_once()


def test_get_assignment_not_found(client, mock_db_session):
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = result_mock

    response = client.get("/split/assignment?test_id=t1&user_id=u1")
    assert response.status_code == 404
    assert "не найдено" in response.json()["detail"]