import logging
from fastapi import FastAPI
from mangum import Mangum
from app.routes import router
from app.config import AppMetadata, guest_bff_prod_configuration, guest_bff_int_configuration
logger = logging.getLogger()
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
    app.state.notification_service_url = app_config.notification_service_url

    app.include_router(router)

    return app

app = create_app()
handler = Mangum(app, lifespan="off")