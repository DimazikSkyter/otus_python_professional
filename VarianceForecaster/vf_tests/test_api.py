from datetime import datetime, timedelta
from unittest.mock import Mock

import numpy as np
import pytest
from fastapi.testclient import TestClient
from vf_app.api.endpoints import app, get_config_service, get_model_service
from vf_app.core.services import Config


@pytest.fixture
def mock_services():
    model_mock = Mock()
    config_mock = Mock()
    config_mock.get_config.return_value = Config(
        random_state=1,
        n_estimators=2,
        max_depth=3,
        learning_rate=0.1,
        subsample=1.0,
        colsample_bytree=1.0,
        reg_lambda=0.0,
        reg_alpha=0.0,
        verbosity=0,
        z_score_default=2.5,
        z_score_percentile=95,
    )
    return model_mock, config_mock


@pytest.fixture
def client_with_mocks(mock_services):
    model_mock, config_mock = mock_services

    app.dependency_overrides[get_model_service] = lambda: model_mock
    app.dependency_overrides[get_config_service] = lambda: config_mock

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


def test_get_config(client_with_mocks, mock_services):
    _, config_mock = mock_services
    response = client_with_mocks.get("/model/configuration")
    assert response.status_code == 200
    assert "fields" in response.json()
    assert (
        response.json()["fields"]["random_state"]
        == config_mock.get_config.return_value.random_state
    )


def test_upload_config(client_with_mocks):
    response = client_with_mocks.put(
        "/model/configuration",
        json={
            "fields": {
                "random_state": 123,
                "n_estimators": 10,
                "max_depth": 3,
                "learning_rate": 0.2,
                "subsample": 1.0,
                "colsample_bytree": 0.8,
                "reg_lambda": 0.5,
                "reg_alpha": 0.1,
                "verbosity": 0,
                "z_score_default": 1.5,
                "z_score_percentile": 90,
            }
        },
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_breakpoints_endpoint(client_with_mocks, mock_services):
    model_mock, _ = mock_services
    model_mock.get_break_points.return_value = np.array([5, 15, 42])

    response = client_with_mocks.post(
        "/metrics/break_points",
        json={
            "start": datetime.utcnow().isoformat(),
            "step": "0:00:01",
            "size": 100,
            "seria": [float(i) for i in range(100)],
        },
    )
    assert response.status_code == 200
    assert response.json() == {"break_points": [5, 15, 42]}


def test_predict_endpoint(client_with_mocks, mock_services):
    model_mock, _ = mock_services
    model_mock.predict_single_seria.return_value = np.array([1.0, 2.0, 3.0])

    response = client_with_mocks.post(
        "/metrics/predict/plr",
        json={
            "start": datetime.utcnow().isoformat(),
            "step": "0:00:01",
            "size": 3,
            "seria": [1.0, 2.0, 3.0],
        },
    )
    assert response.status_code == 200
    assert response.json() == {"y_hat": [1.0, 2.0, 3.0]}


def test_calibrate_endpoint(client_with_mocks):
    response = client_with_mocks.post(
        "/metrics/callibrate_model",
        json={
            "start": datetime.utcnow().isoformat(),
            "step": "0:00:01",
            "size": 10,
            "seria": [float(i) for i in range(10)],
            "break_points": [2, 5],
        },
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
