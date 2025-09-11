import os
from pydantic_settings import BaseSettings

class AppMetadata(BaseSettings):
    guest_bff_env: str = "local"
    app_version: str = "local"
    app_title: str = "Guest BFF Service APP"
    app_description: str = "Guest BFF service"

class AppConfiguration(BaseSettings):
    user_service_url: str | None = None
    booking_service_url: str | None = None
    notification_service_url: str | None = None
    property_service_url: str | None = None
    review_service_url: str | None = None

guest_bff_prod_configuration = AppConfiguration(
    user_service_url="",
    booking_service_url="",
    notification_service_url="",
    property_service_url="",
    review_service_url=""
)

guest_bff_int_configuration = AppConfiguration(
    user_service_url="",
    booking_service_url="",
    notification_service_url="",
    property_service_url="",
    review_service_url=""
)