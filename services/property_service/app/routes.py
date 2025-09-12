from uuid import UUID
from fastapi import APIRouter

from services.property_service.app.handlers import (
    add_property,
    delete_property,
    delete_room,
    get_filtered_rooms,
    get_property,
    get_properties_by_city,
    get_properties_near,
    get_property_rooms,
    get_room,
    add_room,
    get_user_properties,
)
from services.property_service.app.schemas import Property, Room

router = APIRouter()


router.add_api_route(
    path="/property",
    methods=["POST", "PUT"],
    response_model=UUID,
    endpoint=add_property,
    description="Add a new property"
)

router.add_api_route(
    path="/property/{property_uuid}",
    methods=["DELETE"],
    response_model=UUID,
    endpoint=delete_property,
    description="Delete property"
)

router.add_api_route(
    path="/property/{property_uuid}",
    methods=["GET"],
    response_model=Property,
    endpoint=get_property,
    description="Get property"
)

router.add_api_route(
    path="/property/{user_uuid}",
    methods=["GET"],
    response_model=list[Property],
    endpoint=get_user_properties,
    description="Get user properties"
)

router.add_api_route(
    path="/properties/city",
    methods=["GET"],
    response_model=list[Property],
    endpoint=get_properties_by_city,
    description="List properties by city/country/state"
)

router.add_api_route(
    path="/properties/near",
    methods=["GET"],
    response_model=list[Property],
    endpoint=get_properties_near,
    description="List properties within approx bbox delta of given lat/lon, optionally filtered by country/state/city"
)

router.add_api_route(
    path="/room",
    methods=["POST", "PUT"],
    response_model=UUID,
    endpoint=add_room,
    description="Add room"
)

router.add_api_route(
    path="/room/{room_uuid}",
    methods=["GET"],
    response_model=Room,
    endpoint=get_room,
    description="Get room"
)

router.add_api_route(
    path="/room/{room_uuid}",
    methods=["DELETE"],
    response_model=UUID,
    endpoint=delete_room,
    description="Delete room"
)

router.add_api_route(
    path="/rooms/{property_uuid}",
    methods=["GET"],
    response_model=list[Room],
    endpoint=get_property_rooms,
    description="Get rooms od a property"
)

router.add_api_route(
    path="/rooms",
    methods=["GET"],
    response_model=list[Room],
    endpoint=get_filtered_rooms,
    description="Get filtered rooms"
)

