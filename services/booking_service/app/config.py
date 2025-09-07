import os
from pydantic_settings import BaseSettings

class AppMetadata(BaseSettings):
    booking_service_env: str = "local"
    app_version: str = "local"
    app_title: str = "Booking Service APP"
    app_description: str = "Booking management service"

class AppConfiguration(BaseSettings):
    booking_table_name: str | None = None
    hotel_management_database_secret_name: str | None = None
    region: str = "us-east-1"

booking_service_prod_configuration = AppConfiguration(
    booking_table_name=os.environ.get("BOOKING_SERVICE_ENV", None),
    hotel_management_database_secret_name=os.environ.get("HOTEL_MANAGEMENT_DATABASE_SECRET_NAME", None),
)

booking_service_int_configuration = AppConfiguration(
    booking_table_name=os.environ.get("BOOKING_SERVICE_ENV", None),
    hotel_management_database_secret_name=os.environ.get("HOTEL_MANAGEMENT_DATABASE_SECRET_NAME", None),
)