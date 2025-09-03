import os
from pydantic_settings import BaseSettings

class AppMetadata(BaseSettings):
    property_service_env: str = "local"
    app_version: str = "local"
    app_title: str = "Property Service APP"
    app_description: str = "Property management service"

class AppConfiguration(BaseSettings):
    property_table_name: str | None = None
    hotel_management_database_secret_name: str | None = None
    region: str = "us-east-1"

property_service_prod_configuration = AppConfiguration(
    property_table_name=os.environ.get("PROPERTY_SERVICE_ENV", None),
    hotel_management_database_secret_name=os.environ.get("HOTEL_MANAGEMENT_DATABASE_SECRET_NAME", None),
)

property_service_int_configuration = AppConfiguration(
    property_table_name=os.environ.get("PROPERTY_SERVICE_ENV", None),
    hotel_management_database_secret_name=os.environ.get("HOTEL_MANAGEMENT_DATABASE_SECRET_NAME", None),
)