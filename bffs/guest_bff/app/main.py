import logging
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from routes import router
from config import AppMetadata, guest_bff_prod_configuration, guest_bff_int_configuration
from event_bus import EventBusClient
from handlers import JWTVerifier
from httpx import AsyncClient

logger = logging.getLogger()

if not logger.hasHandlers():
    logger.addHandler(logging.StreamHandler())

logger.setLevel(logging.INFO)

def create_app() -> FastAPI:
    app_metadata = AppMetadata()
    app_config = guest_bff_prod_configuration if app_metadata.guest_bff_env == "prod" else guest_bff_int_configuration
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
    app.state.jwt_verifier = JWTVerifier(jwks_url=app_config.jwks_url, audience=app_config.audience, env=app_metadata.guest_bff_env)
    app.state.event_bus = EventBusClient(app_config.event_bus_name)
    app.state.place_index = app_config.place_index
    app.state.paypal_client_id = app_config.paypal_client_id
    app.state.paypal_client_secret = app_config.paypal_client_secret
    app.state.paypal_base_url = app_config.paypal_base_url or "https://api-m.sandbox.paypal.com"
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    app.include_router(router)

    return app

app = create_app()
handler = Mangum(app, lifespan="off")
