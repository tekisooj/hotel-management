import logging
import os
from fastapi import FastAPI
from app.routes import router
from db_client import UserDBClient
from services.user_service.app.auth import CognitoAuthMiddleware
from services.user_service.app.config import AppMetadata, user_service_int_configuration, user_service_prod_configuration
from mangum import Mangum

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def create_app() -> FastAPI:
    app_metadata = AppMetadata()
    app_config = user_service_prod_configuration if app_metadata.user_service_env == "prod" else user_service_int_configuration
    app = FastAPI(
        title="User Service APP",
        description="Service for user management"
    )
    app.state.app_metadata = app_metadata
    app.state.user_table_client = UserDBClient(app_config.user_database_secret_name, app_config.region)
    app.state.audience = app_config.audience
    app.state.jwks_url = app_config.jwks_url
    app.include_router(router)

    app.add_middleware(CognitoAuthMiddleware)

    return app

app = create_app()
handler = Mangum(app, lifespan="off")