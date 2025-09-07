from uuid import UUID
from fastapi import APIRouter

from services.booking_service.app.handlers import add_booking, cancel_booking, check_availability, get_booking, get_filtered_bookings, update_booking
from services.booking_service.app.schemas import Booking

router = APIRouter()


router.add_api_route(
    path="/booking",
    methods=["POST"],
    response_model=UUID,
    endpoint=add_booking,
    description="Add a new booking"
)

router.add_api_route(
    path="/booking/{booking_uuid}",
    methods=["GET"],
    response_model=Booking,
    endpoint=get_booking,
    description="Get a booking by uuid"
)

router.add_api_route(
    path="/bookings",
    methods=["GET"],
    response_model=list[Booking],
    endpoint=get_filtered_bookings,
    description="Get filtered bookings"
)

router.add_api_route(
    path="/booking",
    methods=["PATCH"],
    response_model=Booking,
    endpoint=update_booking,
    description="Update booking"
)

router.add_api_route(
    path="/booking/{booking_uuid}/cancel",
    methods=["PATCH"],
    response_model=Booking,
    endpoint=cancel_booking,
    description="Cancel booking"
)

router.add_api_route(
    path="/availability",
    methods=["GET"],
    response_model=bool,
    endpoint=check_availability,
    description="Check room availability"
)