import logging
import os
from fastapi import FastAPI
from app.routes import router
from db_client import UserDBClient
from services.user_service.app.auth import CognitoAuthMiddleware
from services.user_service.app.config import AppMetadata
from mangum import Mangum

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def create_app() -> FastAPI:
    app_metadata = AppMetadata()
    
    app = FastAPI(
        title="User Service APP",
        description="Service for user management"
    )
    app.state.app_metadata = app_metadata
    user_table_name = os.getenv("USER_TABLE_NAME", None)
    app.state.user_table_client = UserDBClient(user_table_name)

    app.include_router(router)

    app.add_middleware(CognitoAuthMiddleware)

    return app

app = create_app()
handler = Mangum(app, lifespan="off")