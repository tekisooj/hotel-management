import logging
import os
import socket
import sys
from fastapi import FastAPI
from routes import router
from db_client import HotelManagementDBClient
from config import AppMetadata, booking_service_int_configuration, booking_service_prod_configuration
from mangum import Mangum


logger = logging.getLogger()

if not logger.hasHandlers():
    logger.addHandler(logging.StreamHandler())

logger.setLevel(logging.INFO)


host = os.getenv("DB_PROXY_ENDPOINT")
logger.info(f"Trying to connect to: {host}")
logger.info("DNS resolved to: {socket.gethostbyname(host)}")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5)
sock.connect((host, 5432))
logger.info("TCP connection succeeded")
sock.close()

    
def create_app() -> FastAPI:
    app_metadata = AppMetadata()
    app_config = booking_service_prod_configuration if app_metadata.booking_service_env == "prod" else booking_service_int_configuration
    app = FastAPI(
        title=app_metadata.app_title,
        description=app_metadata.app_description
    )
    app.state.app_metadata = app_metadata
    app.state.user_table_client = HotelManagementDBClient(app_config.hotel_management_database_secret_name, app_config.region, app_config.db_proxy_endpoint)

    app.include_router(router)

    return app

app = create_app()
handler = Mangum(app, lifespan="off")
