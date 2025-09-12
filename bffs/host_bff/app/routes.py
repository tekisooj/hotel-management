from uuid import UUID
from fastapi import APIRouter

from bffs.host_bff.app.handlers import (
    change_booking_status,
    delete_property,
    delete_room,
    get_bookings,
    get_property_reviews,
    get_user_properties,
    get_current_user,
    put_property,
    put_room,
    update_current_user,
)
from bffs.host_bff.app.models.booking import Booking
from bffs.host_bff.app.models.property import Property, PropertyDetail
from bffs.host_bff.app.models.user import UserResponse
from bffs.host_bff.app.models.review import Review
from bffs.host_bff.app.models.property import Room


router = APIRouter()


router.add_api_route(
    path="/properties",
    methods=["GET"],
    response_model=list[PropertyDetail],
    endpoint=get_user_properties,
    description="Get all properties of a user"
)

router.add_api_route(
    path="/property",
    methods=["PUT"],
    response_model=UUID,
    endpoint=put_property,
    description="Add a new property"
)

router.add_api_route(
    path="/room",
    methods=["PUT"],
    response_model=UUID,
    endpoint=put_room,
    description="Add a new room"
)

router.add_api_route(
    path="/room/{room_uuid}",
    methods=["DELETE"],
    response_model=UUID,
    endpoint=delete_room,
    description="Delete user room"
)

router.add_api_route(
    path="/property/{property_uuid}",
    methods=["DELETE"],
    response_model=UUID,
    endpoint=delete_property,
    description="Delete user property"
)

router.add_api_route(
    path="/bookings",
    methods=["GET"],
    response_model=list[Booking],
    endpoint=get_bookings,
    description="Get bookings"
)

router.add_api_route(
    path="/booking/{booking_uuid}",
    methods=["PATCH"],
    response_model=Booking,
    endpoint=change_booking_status,
    description="Change booking status"
)

router.add_api_route(
    path="/reviews/{property_uuid}",
    methods=["GET"],
    response_model=list[Review],
    endpoint=get_property_reviews,
    description="Get property reviews"
)

router.add_api_route(
    path="/me",
    methods=["GET"],
    response_model=UserResponse,
    endpoint=get_current_user,
    description="Get current user"
)

router.add_api_route(
    path="/me",
    methods=["PATCH"],
    response_model=UserResponse | None,
    endpoint=update_current_user,
    description="Update current user"
)
