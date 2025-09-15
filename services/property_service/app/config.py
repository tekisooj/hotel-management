import os
from pydantic_settings import BaseSettings

class AppMetadata(BaseSettings):
    property_service_env: str = "local"
    app_version: str = "local"
    app_title: str = "Property Service APP"
    app_description: str = "Property management service"

class AppConfiguration(BaseSettings):
    property_table_name: str | None = None
    room_table_name: str | None = None

property_service_prod_configuration = AppConfiguration(
    property_table_name=os.environ.get("PROPERTY_TABLE_NAME", None),
    room_table_name=os.environ.get("ROOM_TABLE_NAME", None),
)

property_service_int_configuration = AppConfiguration(
    property_table_name=os.environ.get("PROPERTY_TABLE_NAME", "property_table_int"),
    room_table_name=os.environ.get("ROOM_TABLE_NAME", "room_table_int"),
)
