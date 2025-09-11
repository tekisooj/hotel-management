import os
from pydantic_settings import BaseSettings

class AppMetadata(BaseSettings):
    notification_service_env: str = "local"
    app_version: str = "local"
    app_title: str = "Notification Service APP"
    app_description: str = "Notification management service"

class AppConfiguration(BaseSettings):
    sender_email: str = "tekisooj@gmail.com"
    region: str = "us-east-1"

