import os
import json
import pytest
from moto import mock_aws
import boto3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

AWS_REGION = "us-east-1"


@pytest.fixture(scope="session", autouse=True)
def set_region():
    os.environ.setdefault("AWS_DEFAULT_REGION", AWS_REGION)
    yield


@pytest.fixture
def moto_aws():
    with mock_aws():
        yield


def _create_ddb_table(dynamodb, name, partition_key, sort_key=None, gsi_defs=None):
    key_schema = [{"AttributeName": partition_key, "KeyType": "HASH"}]
    attr_defs = [{"AttributeName": partition_key, "AttributeType": "S"}]
    if sort_key:
        key_schema.append({"AttributeName": sort_key, "KeyType": "RANGE"})
        attr_defs.append({"AttributeName": sort_key, "AttributeType": "S"})

    params = {
        "TableName": name,
        "KeySchema": key_schema,
        "AttributeDefinitions": attr_defs,
        "BillingMode": "PAY_PER_REQUEST",
    }

    if gsi_defs:
        gsis = []
        for g in gsi_defs:
            gsis.append({
                "IndexName": g["name"],
                "KeySchema": [
                    {"AttributeName": g["partition"], "KeyType": "HASH"},
                    *([{"AttributeName": g["sort"], "KeyType": "RANGE"}] if g.get("sort") else []),
                ],
                "Projection": {"ProjectionType": "ALL"},
            })
            if not any(a["AttributeName"] == g["partition"] for a in params["AttributeDefinitions"]):
                params["AttributeDefinitions"].append({"AttributeName": g["partition"], "AttributeType": "S"})
            if g.get("sort") and not any(a["AttributeName"] == g["sort"] for a in params["AttributeDefinitions"]):
                params["AttributeDefinitions"].append({"AttributeName": g["sort"], "AttributeType": "S"})
        params["GlobalSecondaryIndexes"] = gsis

    tbl = dynamodb.create_table(**params)
    tbl.wait_until_exists()
    return tbl


@pytest.fixture
def aws_resources(moto_aws):
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    s3 = boto3.client("s3", region_name=AWS_REGION)
    yield dynamodb, s3
