import os
import pytest
from fastapi.testclient import TestClient
from services.booking_service.app.main import app  # type: ignore
from tests.conftest import _create_ddb_table


@pytest.fixture
def booking_env(aws_resources, monkeypatch):
    dynamodb, _ = aws_resources
    BOOKING_TABLE = "booking_table_test"
    _create_ddb_table(dynamodb, BOOKING_TABLE, partition_key="uuid", sort_key=None)
    monkeypatch.setenv("BOOKING_TABLE_NAME", BOOKING_TABLE)
    monkeypatch.setenv("BOOKING_SERVICE_ENV", "test")
    yield


@pytest.fixture
def booking_client(booking_env):
    return TestClient(app)
