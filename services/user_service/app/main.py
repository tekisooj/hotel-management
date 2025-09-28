import os
import json
import logging
import boto3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from routes import router
from db_client import HotelManagementDBClient
from auth import CognitoAuthMiddleware
from cognito_client import CognitoClient
from config import (
    AppMetadata,
    user_service_int_configuration,
    user_service_prod_configuration,
)

logger = logging.getLogger()
if not logger.hasHandlers():
    logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


def create_app() -> FastAPI:
    logger.info("🚀 Starting Lambda initialization")

    app_metadata = AppMetadata()
    app_config = (
        user_service_prod_configuration
        if app_metadata.user_service_env == "prod"
        else user_service_int_configuration
    )

    logger.info(f"🧠 Environment: {app_metadata.user_service_env}")
    logger.info(f"📦 Region: {app_config.region}")
    logger.info(f"🔐 Secret: {app_config.hotel_management_database_secret_name}")
    logger.info(f"🧩 Proxy Endpoint: {app_config.db_proxy_endpoint}")

    app = FastAPI(
        title=app_metadata.app_title,
        description=app_metadata.app_description,
    )

    allowed_origins = [
        "https://d3h3g1mttxpuc6.cloudfront.net",
        "https://d2ecdgwxri75mv.cloudfront.net",
        "https://demfm8bnd6dtk.cloudfront.net",
        "https://dsfjwq83frzww.cloudfront.net",
        "https://d2hx3vlqyzz4bv.cloudfront.net",
        "https://djb3c9odb1pg2.cloudfront.net",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    try:
        logger.info("🧭 Testing Secrets Manager access...")
        sm_client = boto3.client("secretsmanager", region_name=app_config.region)
        sm_client.get_secret_value(
            SecretId=app_config.hotel_management_database_secret_name
        )
        logger.info("✅ Secrets Manager reachable")
    except Exception as e:
        logger.exception("❌ Secrets Manager unreachable")
        raise

    try:
        logger.info("🧠 Initializing DB client...")
        app.state.user_table_client = HotelManagementDBClient(
            hotel_management_database_secret_name=app_config.hotel_management_database_secret_name,
            region=app_config.region,
            proxy_endpoint=app_config.db_proxy_endpoint,
        )
        logger.info("✅ DB client initialized")
    except Exception as e:
        logger.exception("❌ Failed to initialize DB client")
        raise

    try:
        logger.info("🧠 Initializing Cognito client...")
        app.state.cognito_client = CognitoClient(app_config.region, app_config.app_client_id)
        logger.info("✅ Cognito client initialized")
    except Exception as e:
        logger.exception("❌ Failed to initialize Cognito client")
        raise

    app.state.app_metadata = app_metadata
    app.state.audience = app_config.audience
    app.state.jwks_url = app_config.jwks_url

    app.include_router(router)
    app.add_middleware(CognitoAuthMiddleware)

    logger.info("✅ App startup complete")
    return app


app = create_app()
handler = Mangum(app, lifespan="off")
