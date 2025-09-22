import os
from pydantic_settings import BaseSettings

class AppMetadata(BaseSettings):
    guest_bff_env: str = "local"
    app_version: str = "local"
    app_title: str = "Guest BFF Service APP"
    app_description: str = "Guest BFF service"

class AppConfiguration(BaseSettings):
    user_service_url: str
    booking_service_url: str
    property_service_url: str
    review_service_url: str
    event_bus_name: str | None = None
    audience: str | None = None
    jwks_url: str | None = None
    place_index: str | None = None

guest_bff_prod_configuration = AppConfiguration(
    user_service_url="https://9by6xj4b6h.execute-api.us-east-1.amazonaws.com/prod/",
    booking_service_url="https://d604idgdac.execute-api.us-east-1.amazonaws.com/prod/",
    property_service_url="https://ztcr86tzq7.execute-api.us-east-1.amazonaws.com/prod/",
    review_service_url="https://p6fhqo8np0.execute-api.us-east-1.amazonaws.com/prod/",    
    audience=os.environ.get("AUDIENCE", None),
    jwks_url=os.environ.get("JWKS_URL", None),
    event_bus_name=os.getenv("EVENT_BUS_NAME", None),
    place_index=os.environ.get("PLACE_INDEX_NAME", None)
    
)

guest_bff_int_configuration = AppConfiguration(
    user_service_url="https://g8bpnxtiii.execute-api.us-east-1.amazonaws.com/prod/",
    booking_service_url="https://sn2evwp3ub.execute-api.us-east-1.amazonaws.com/prod/",
    property_service_url="https://92znf03thc.execute-api.us-east-1.amazonaws.com/prod/",
    review_service_url="https://vdt7h3agnj.execute-api.us-east-1.amazonaws.com/prod/",    
    audience=os.environ.get("AUDIENCE", None),
    jwks_url=os.environ.get("JWKS_URL", None),
    event_bus_name=os.getenv("EVENT_BUS_NAME", None),
    place_index=os.environ.get("PLACE_INDEX_NAME", None)

)

