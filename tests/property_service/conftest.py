import os
import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

# Adjust import below to your actual app entrypoint
# e.g., services/property_service/app/main.py exposes FastAPI app as `app`
from services.property_service.app.main import app  # type: ignore


@pytest.fixture
def property_env(aws_resources, monkeypatch):
    dynamodb, s3 = aws_resources

    # match your CDK stack names
    PROPERTY_TABLE = "property_table_test"
    ROOM_TABLE = "room_table_test"
    BUCKET = "property-assets-test"

    from tests.conftest import _create_ddb_table
    _create_ddb_table(
        dynamodb,
        PROPERTY_TABLE,
        partition_key="uuid",
        gsi_defs=[
            {"name": "user_index", "partition": "user_uuid", "sort": "created_at"},
            {"name": "city_index", "partition": "city_key", "sort": "created_at"},
        ],
    )
    _create_ddb_table(
        dynamodb,
        ROOM_TABLE,
        partition_key="uuid",
        gsi_defs=[{"name": "property_uuid_index", "partition": "property_uuid"}],
    )

    s3.create_bucket(Bucket=BUCKET)

    monkeypatch.setenv("PROPERTY_TABLE_NAME", PROPERTY_TABLE)
    monkeypatch.setenv("ROOM_TABLE_NAME", ROOM_TABLE)
    monkeypatch.setenv("ASSET_BUCKET_NAME", BUCKET)
    monkeypatch.setenv("PROPERTY_SERVICE_ENV", "test")

    yield


@pytest.fixture
def property_client(property_env):
    return TestClient(app)
