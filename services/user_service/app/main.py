import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from routes import router
from db_client import HotelManagementDBClient
from config import AppMetadata, user_service_int_configuration, user_service_prod_configuration
from cognito_client import CognitoClient

logger = logging.getLogger()
if not logger.hasHandlers():
    logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)
logger.info("🚀 Starting User Service Lambda...")

def create_app() -> FastAPI:
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
        "https://d3h3g1mttxpuc6.cloudfront.net",  # INT Auth UI
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

    logger.info("🧭 Testing Secrets Manager connectivity...")
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

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info(f"📥 Incoming request: {request.method} {request.url.path}")
        response = await call_next(request)
        logger.info(f"📤 Response: {response.status_code} for {request.method} {request.url.path}")
        return response

    logger.info("✅ App initialized successfully.")
    return app


app = create_app()

logger.info("⚙️ Wrapping FastAPI with Mangum...")
handler = Mangum(app, lifespan="off")
logger.info("✅ Handler ready for API Gateway.")
