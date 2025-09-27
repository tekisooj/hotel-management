import os
from pydantic_settings import BaseSettings

class AppMetadata(BaseSettings):
    user_service_env: str = "local"
    app_version: str = "local"
    app_title: str = "User Service APP"
    app_description: str = "User management service"

class AppConfiguration(BaseSettings):
    user_table_name: str | None = None
    hotel_management_database_secret_name: str | None = None
    region: str = "us-east-1"
    app_client_id: str | None = None
    audience: str | None = None
    jwks_url: str | None = None
    db_proxy_endpoint: str | None = None

user_service_prod_configuration = AppConfiguration(
    user_table_name=os.environ.get("USER_SERVICE_ENV", None),
    hotel_management_database_secret_name=os.environ.get("HOTEL_MANAGEMENT_DATABASE_SECRET_NAME", None),
    audience=os.environ.get("AUDIENCE", None),
    jwks_url=os.environ.get("JWKS_URL", None),
    app_client_id=os.environ.get("APP_CLIENT_ID", None),
    db_proxy_endpoint=os.environ.get("DB_PROXY_ENDPOINT", None)
)

user_service_int_configuration = AppConfiguration(
    user_table_name=os.environ.get("USER_SERVICE_ENV", None),
    hotel_management_database_secret_name=os.environ.get("HOTEL_MANAGEMENT_DATABASE_SECRET_NAME", None),
    audience=os.environ.get("AUDIENCE", None),
    jwks_url=os.environ.get("JWKS_URL", None),
    app_client_id=os.environ.get("APP_CLIENT_ID", None),
    db_proxy_endpoint=os.environ.get("DB_PROXY_ENDPOINT", None)
)