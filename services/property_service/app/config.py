import os
from pydantic_settings import BaseSettings


def _get_int_env(var_name: str, default: int) -> int:
    raw_value = os.environ.get(var_name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


class AppMetadata(BaseSettings):
    property_service_env: str = "local"
    app_version: str = "local"
    app_title: str = "Property Service APP"
    app_description: str = "Property management service"


class AppConfiguration(BaseSettings):
    region: str = "us-east-1"
    property_table_name: str | None = None
    room_table_name: str | None = None
    asset_bucket_name: str | None = None
    asset_url_ttl_seconds: int = 3600


property_service_prod_configuration = AppConfiguration(
    property_table_name=os.environ.get("PROPERTY_TABLE_NAME", None),
    room_table_name=os.environ.get("ROOM_TABLE_NAME", None),
    asset_bucket_name=os.environ.get("ASSET_BUCKET_NAME", None),
)

property_service_int_configuration = AppConfiguration(
    property_table_name=os.environ.get("PROPERTY_TABLE_NAME", "property_table_int"),
    room_table_name=os.environ.get("ROOM_TABLE_NAME", "room_table_int"),
    asset_bucket_name=os.environ.get("ASSET_BUCKET_NAME", "property-assets-int"),
)
