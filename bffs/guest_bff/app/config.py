import os
from pydantic_settings import BaseSettings

class AppMetadata(BaseSettings):
    guest_bff_env: str = "local"
    app_version: str = "local"
    app_title: str = "Guest BFF Service APP"
    app_description: str = "Guest BFF service"

class AppConfiguration(BaseSettings):
    user_service_url: str
    booking_service_url: str
    property_service_url: str
    review_service_url: str
    audience: str
    jwks_url: str

guest_bff_prod_configuration = AppConfiguration(
    user_service_url="https://9by6xj4b6h.execute-api.us-east-1.amazonaws.com",
    booking_service_url="https://d604idgdac.execute-api.us-east-1.amazonaws.com",
    property_service_url="https://ztcr86tzq7.execute-api.us-east-1.amazonaws.com",
    review_service_url="https://p6fhqo8np0.execute-api.us-east-1.amazonaws.com",
    audience="7226gqpnghn0q22ec2ill399lv",
    jwks_url="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_Wtvh2rdSQ/.well-known/jwks.json",
)

guest_bff_int_configuration = AppConfiguration(
    user_service_url="https://g8bpnxtiii.execute-api.us-east-1.amazonaws.com",
    booking_service_url="https://1k0qg6e1ld.execute-api.us-east-1.amazonaws.com",
    property_service_url="https://kuquysqcnb.execute-api.us-east-1.amazonaws.com",
    review_service_url="https://vdt7h3agnj.execute-api.us-east-1.amazonaws.com",
    audience="la13fgbn7avmni0f84pu5lk79",
    jwks_url="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_DDS5D565p/.well-known/jwks.json",
)
