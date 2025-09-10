import logging
import os
from fastapi import FastAPI
from app.routes import router
from db_client import ReviewDBClient
from services.review_service.app.config import AppMetadata, review_service_int_configuration, review_service_prod_configuration
from mangum import Mangum

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def create_app() -> FastAPI:
    app_metadata = AppMetadata()
    app_config = review_service_prod_configuration if app_metadata.review_service_env == "prod" else review_service_int_configuration
    app = FastAPI(
        title=app_metadata.app_title,
        description=app_metadata.app_description
    )
    app.state.app_metadata = app_metadata
    app.state.review_db_client = ReviewDBClient(app_config.review_table_name)

    app.include_router(router)

    return app

app = create_app()
handler = Mangum(app, lifespan="off")