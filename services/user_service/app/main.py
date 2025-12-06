import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from routes import router
from db_client import HotelManagementDBClient
from config import (
    AppMetadata,
    user_service_int_configuration,
    user_service_prod_configuration,
)
from cognito_client import CognitoClient
from auth import CognitoAuthMiddleware


logger = logging.getLogger()
if not logger.hasHandlers():
    logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)



def create_app() -> FastAPI:
    app_metadata = AppMetadata()
    app_config = (
        user_service_prod_configuration
        if app_metadata.user_service_env == "prod"
        else user_service_int_configuration
    )

    app = FastAPI(
        title=app_metadata.app_title,
        description=app_metadata.app_description,
    )

    allowed_origins = [
        "https://dz5wjcpk0b8gl.cloudfront.net",  # Auth UI (new)
        "https://d373zu2tukknza.cloudfront.net",  # INT Auth UI
        "https://d2ecdgwxri75mv.cloudfront.net",  # PROD Auth UI
        "https://demfm8bnd6dtk.cloudfront.net",   # Guest INT
        "https://dsfjwq83frzww.cloudfront.net",   # Guest PROD
        "https://d2hx3vlqyzz4bv.cloudfront.net",  # Host INT
        "https://djb3c9odb1pg2.cloudfront.net",   # Host PROD
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.app_metadata = app_metadata
    app.state.user_table_client = HotelManagementDBClient(
        hotel_management_database_secret_name=app_config.hotel_management_database_secret_name,
        region=app_config.region,
        proxy_endpoint=app_config.db_proxy_endpoint,
    )

    app.state.audience = app_config.audience
    app.state.jwks_url = app_config.jwks_url
    app.state.cognito_client = CognitoClient(
        aws_region=app_config.region,
        app_client_id=app_config.app_client_id,
    )

    app.add_middleware(CognitoAuthMiddleware)
    app.include_router(router)

    @app.middleware("http")
    async def log_requests(request: Request, call_next):

        auth_header = request.headers.get("Authorization")
        if auth_header:
            logger.info(f"Authorization header received")
        else:
            logger.warning("No Authorization header found")

        response = await call_next(request)

        logger.info(
            f"Response: {response.status_code} for {request.method} {request.url.path}"
        )
        return response

    return app


app = create_app()

handler = Mangum(app, lifespan="off")
