import logging
import os

from fastapi import FastAPI
from mangum import Mangum

from config import (
    AppMetadata,
    property_service_int_configuration,
    property_service_prod_configuration,
)
from db_clients import PropertyTableClient, RoomTableClient
from routes import router
from storage import S3AssetStorage

logger = logging.getLogger()

if not logger.hasHandlers():
    logger.addHandler(logging.StreamHandler())

logger.setLevel(logging.INFO)


def create_app() -> FastAPI:
    app_metadata = AppMetadata()
    app_config = (
        property_service_prod_configuration
        if app_metadata.property_service_env == "prod"
        else property_service_int_configuration
    )
    app = FastAPI(
        title=app_metadata.app_title,
        description=app_metadata.app_description,
    )
    app.state.app_metadata = app_metadata
    app.state.property_table_client = PropertyTableClient(
        app_config.property_table_name,
    )
    app.state.room_table_client = RoomTableClient(
        app_config.room_table_name,
    )

    asset_bucket = app_config.asset_bucket_name

    app.state.asset_storage = S3AssetStorage(
        bucket_name=asset_bucket,
        presign_ttl_seconds=app_config.asset_url_ttl_seconds,
        region_name=region,
    )


    app.include_router(router)

    return app


def _main() -> None:
    """Entrypoint when running locally."""
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
        reload=True,
    )


if __name__ == "__main__":
    _main()

app = create_app()
handler = Mangum(app, lifespan="off")
