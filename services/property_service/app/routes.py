from uuid import UUID
from fastapi import APIRouter

from services.property_service.app.handlers import (
    add_property,
    get_filtered_rooms,
    get_property,
    get_property_rooms,
    get_room,
    add_room,
)
from services.property_service.app.schemas import Property, Room

router = APIRouter()


router.add_api_route(
    path="/property",
    methods=["POST"],
    response_model=UUID,
    endpoint=add_property,
    description="Add a new property"
)

router.add_api_route(
    path="/property/{property_uuid}",
    methods=["GET"],
    response_model=Property,
    endpoint=get_property,
    description="Get property"
)

router.add_api_route(
    path="/room",
    methods=["POST"],
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

