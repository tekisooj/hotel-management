import logging
import os
from fastapi import FastAPI
from app.routes import router
from db_client import HotelManagementDBClient
from services.property_service.app.config import AppMetadata, property_service_int_configuration, property_service_prod_configuration
from mangum import Mangum

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def create_app() -> FastAPI:
    app_metadata = AppMetadata()
    app_config = property_service_prod_configuration if app_metadata.property_service_env == "prod" else property_service_int_configuration
    app = FastAPI(
        title=app_metadata.app_title,
        description=app_metadata.app_description
    )
    app.state.app_metadata = app_metadata
    app.state.user_table_client = HotelManagementDBClient(app_config.hotel_management_database_secret_name, app_config.region)

    app.include_router(router)

    return app

app = create_app()
handler = Mangum(app, lifespan="off")