import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router
from db_client import HotelManagementDBClient
from auth import CognitoAuthMiddleware
from config import AppMetadata, user_service_int_configuration, user_service_prod_configuration
from mangum import Mangum
from cognito_client import CognitoClient


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
        "https://d3h3g1mttxpuc6.cloudfront.net",  # INT (auth UI)
        "https://d2ecdgwxri75mv.cloudfront.net",  # PROD (auth UI)
        "https://demfm8bnd6dtk.cloudfront.net",   # guest INT
        "https://dsfjwq83frzww.cloudfront.net",   # guest PROD
        "https://d2hx3vlqyzz4bv.cloudfront.net",  # host INT
        "https://djb3c9odb1pg2.cloudfront.net",   # host PROD
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
    app.state.cognito_client = CognitoClient(app_config.region, app_config.app_client_id)

    app.include_router(router)
    app.add_middleware(CognitoAuthMiddleware)

    return app


app = create_app()
handler = Mangum(app, lifespan="off")
