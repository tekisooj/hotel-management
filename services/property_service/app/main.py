import logging
import os
from fastapi import FastAPI
from routes import router
from db_clients import PropertyTableClient, RoomTableClient
from config import AppMetadata, property_service_int_configuration, property_service_prod_configuration
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
    app.state.property_table_client = PropertyTableClient(
        app_config.property_table_name,
    )
    app.state.room_table_client = RoomTableClient(
        app_config.room_table_name,
    )

    app.include_router(router)

    return app

app = create_app()
handler = Mangum(app, lifespan="off")
