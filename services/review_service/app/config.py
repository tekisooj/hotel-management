import os
from pydantic_settings import BaseSettings

class AppMetadata(BaseSettings):
    review_service_env: str = "local"
    app_version: str = "local"
    app_title: str = "Review Service APP"
    app_description: str = "Review management service"

class AppConfiguration(BaseSettings):
    review_table_name: str | None = None

review_service_prod_configuration = AppConfiguration(
    review_table_name=os.environ.get("REVIEW_TABLE_NAME", None),
)

review_service_int_configuration = AppConfiguration(
    review_table_name=os.environ.get("REVIEW_TABLE_NAME", None),
)