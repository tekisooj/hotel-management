import logging
import os
import sys
from fastapi import FastAPI
from routes import router
from db_client import HotelManagementDBClient
from auth import CognitoAuthMiddleware
from config import AppMetadata, user_service_int_configuration, user_service_prod_configuration
from mangum import Mangum


logger = logging.getLogger()

if not logger.hasHandlers():
    logger.addHandler(logging.StreamHandler())

logger.setLevel(logging.INFO)

    

def create_app() -> FastAPI:
    app_metadata = AppMetadata()
    app_config = user_service_prod_configuration if app_metadata.user_service_env == "prod" else user_service_int_configuration
    app = FastAPI(
        title=app_metadata.app_title,
        description=app_metadata.app_description
    )
    app.state.app_metadata = app_metadata
    app.state.user_table_client = HotelManagementDBClient(app_config.hotel_management_database_secret_name, app_config.region)
    app.state.audience = app_config.audience
    app.state.jwks_url = app_config.jwks_url
    app.include_router(router)

    app.add_middleware(CognitoAuthMiddleware)

    return app

app = create_app()
handler = Mangum(app, lifespan="off")
