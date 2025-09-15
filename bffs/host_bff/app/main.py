import logging
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from routes import router
from config import AppMetadata, host_bff_prod_configuration, host_bff_int_configuration
from handlers import JWTVerifier
from httpx import AsyncClient
import time


logger = logging.getLogger()
logger.setLevel(logging.INFO)

if not logger.hasHandlers():
    handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(handler)

    
def create_app() -> FastAPI:
    app_metadata = AppMetadata()
    app_config = host_bff_prod_configuration if app_metadata.host_bff_env == "prod" else host_bff_int_configuration
    app = FastAPI(
        title=app_metadata.app_title,
        description=app_metadata.app_description
    )
    app.state.app_metadata = app_metadata
    app.state.user_service_url = app_config.user_service_url
    app.state.property_service_url = app_config.property_service_url
    app.state.booking_service_url = app_config.booking_service_url
    app.state.review_service_url = app_config.review_service_url
    app.state.user_service_client = AsyncClient(base_url=app_config.user_service_url)
    app.state.property_service_client = AsyncClient(base_url=app_config.property_service_url)
    app.state.booking_service_client = AsyncClient(base_url=app_config.booking_service_url)
    app.state.review_service_client = AsyncClient(base_url=app_config.review_service_url)
    app.state.jwt_verifier = JWTVerifier(jwks_url=app_config.jwks_url, audience=app_config.audience, env=app_metadata.host_bff_env)
    app.state.place_index = app_config.place_index


    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    app.include_router(router)

    @app.middleware("http")
    async def logging_middleware(request, call_next):
        start = time.time()
        ua = request.headers.get("user-agent", "-")
        trace = request.headers.get("x-amzn-trace-id") or request.headers.get("x-request-id") or "-"
        path = request.url.path
        method = request.method
        try:
            response = await call_next(request)
            duration_ms = int((time.time() - start) * 1000)
            logger.info(f"{method} {path} -> {response.status_code} {duration_ms}ms ua={ua} trace={trace}")
            return response
        except Exception:
            duration_ms = int((time.time() - start) * 1000)
            logger.exception(f"Unhandled error for {method} {path} after {duration_ms}ms ua={ua} trace={trace}")
            raise

    return app

app = create_app()
handler = Mangum(app, lifespan="off")
