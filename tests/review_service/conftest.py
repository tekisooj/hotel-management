import os
import pytest
from fastapi.testclient import TestClient
from services.review_service.app.main import app  # type: ignore
from tests.conftest import _create_ddb_table


@pytest.fixture
def review_env(aws_resources, monkeypatch):
    dynamodb, _ = aws_resources
    REVIEW_TABLE = "review_table_test"
    _create_ddb_table(dynamodb, REVIEW_TABLE, partition_key="uuid")
    monkeypatch.setenv("REVIEW_TABLE_NAME", REVIEW_TABLE)
    monkeypatch.setenv("REVIEW_SERVICE_ENV", "test")
    yield


@pytest.fixture
def review_client(review_env):
    return TestClient(app)
