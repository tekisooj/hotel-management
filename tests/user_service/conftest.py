import os
import pytest
from fastapi.testclient import TestClient
from services.user_service.app.main import app  # type: ignore
from tests.conftest import _create_ddb_table


@pytest.fixture
def user_env(aws_resources, monkeypatch):
    dynamodb, _ = aws_resources
    USER_TABLE = "user_table_test"
    _create_ddb_table(dynamodb, USER_TABLE, partition_key="uuid", sort_key=None)
    monkeypatch.setenv("USER_TABLE_NAME", USER_TABLE)
    monkeypatch.setenv("USER_SERVICE_ENV", "test")
    yield


@pytest.fixture
def user_client(user_env):
    return TestClient(app)
