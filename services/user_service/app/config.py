import os
from pydantic_settings import BaseSettings

class AppMetadata(BaseSettings):
    user_service_env: str = "local"
    app_version: str = "local"
    app_title: str = "User Service APP"
    app_description: str = "User management service"