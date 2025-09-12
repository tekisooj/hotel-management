from uuid import UUID
from fastapi import APIRouter

from bffs.guest_bff.app.handlers import (
    add_booking,
    add_review,
    cancel_user_booking,
    get_filtered_rooms,
    get_property_reviews,
    get_user_bookings,
    get_user_reviews,
    get_current_user,
    update_current_user,
)
from bffs.guest_bff.app.models.booking import Booking
from bffs.guest_bff.app.models.property import PropertyDetail
from bffs.guest_bff.app.models.user import UserResponse
from bffs.guest_bff.app.models.review import Review


router = APIRouter()


router.add_api_route(
    path="/review",
    methods=["POST"],
    response_model=UUID,
    endpoint=add_review,
    description="Add a new review for property"
)

router.add_api_route(
    path="/reviews/{property_uuid}",
    methods=["GET"],
    response_model=list[Review],
    endpoint=get_property_reviews,
    description="Get all property reviews"
)

router.add_api_route(
    path="/reviews/{user_uuid}",
    methods=["GET"],
    response_model=list[Review],
    endpoint=get_user_reviews,
    description="Get all user reviews"
)

router.add_api_route(
    path="/booking",
    methods=["POST"],
    response_model=UUID,
    endpoint=add_booking,
    description="Add a new booking"
)

router.add_api_route(
    path="/my/bookings",
    methods=["GET"],
    response_model=list[Booking],
    endpoint=get_user_bookings,
    description="Get all user bookings"
)

router.add_api_route(
    path="/my/booking/{booking_uuid}",
    methods=["DELETE"],
    response_model=UUID,
    endpoint=cancel_user_booking,
    description="Cancel user booking"
)

router.add_api_route(
    path="/rooms",
    methods=["GET"],
    response_model=PropertyDetail,
    endpoint=get_filtered_rooms,
    description="Get filtered rooms"
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
