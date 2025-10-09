from uuid import UUID

from fastapi import APIRouter

from handlers import (
    add_property,
    update_property,
    add_room,
    update_room,
    change_booking_status,
    create_asset_upload_url,
    delete_property,
    delete_room,
    get_bookings,
    get_current_user,
    get_property_reviews,
    get_property_detail,
    get_user_properties,
    search_places,
    update_current_user,
)
from models.asset import AssetUploadResponse
from models.booking import Booking
from models.property import Availability, Property, PropertyDetail, Room
from models.review import Review
from models.user import UserResponse


router = APIRouter()

router.add_api_route(
    path="/assets/upload-url",
    methods=["POST"],
    response_model=AssetUploadResponse,
    endpoint=create_asset_upload_url,
    description="Request a pre-signed S3 upload URL for property or room assets",
)

router.add_api_route(
    path="/properties",
    methods=["GET"],
    response_model=list[PropertyDetail],
    endpoint=get_user_properties,
    description="Get all properties of a user",
)

router.add_api_route(
    path="/property/{property_uuid}",
    methods=["GET"],
    response_model=PropertyDetail,
    endpoint=get_property_detail,
    description="Get property details",
)

router.add_api_route(
    path="/property",
    methods=["POST"],
    response_model=UUID,
    endpoint=add_property,
    description="Add a new property",
)

router.add_api_route(
    path="/property/{property_uuid}",
    methods=["PATCH"],
    response_model=PropertyDetail,
    endpoint=update_property,
    description="Update property details",
)

router.add_api_route(
    path="/room",
    methods=["POST"],
    response_model=UUID,
    endpoint=add_room,
    description="Add a new room",
)

router.add_api_route(
    path="/room/{room_uuid}",
    methods=["PUT"],
    response_model=Room,
    endpoint=update_room,
    description="Update user room",
)

router.add_api_route(
    path="/room/{room_uuid}",
    methods=["DELETE"],
    response_model=UUID,
    endpoint=delete_room,
    description="Delete user room",
)

router.add_api_route(
    path="/property/{property_uuid}",
    methods=["DELETE"],
    response_model=UUID,
    endpoint=delete_property,
    description="Delete user property",
)

router.add_api_route(
    path="/bookings",
    methods=["GET"],
    response_model=list[Availability],
    endpoint=get_bookings,
    description="Get bookings",
)

router.add_api_route(
    path="/booking/{booking_uuid}",
    methods=["PATCH"],
    response_model=Booking,
    endpoint=change_booking_status,
    description="Change booking status",
)

router.add_api_route(
    path="/reviews/{property_uuid}",
    methods=["GET"],
    response_model=list[Review],
    endpoint=get_property_reviews,
    description="Get property reviews",
)

router.add_api_route(
    path="/places/search-text",
    methods=["GET"],
    endpoint=search_places,
    description="Search places by free text via Amazon Location",
)

router.add_api_route(
    path="/me",
    methods=["GET"],
    response_model=UserResponse,
    endpoint=get_current_user,
    description="Get current user",
)

router.add_api_route(
    path="/me",
    methods=["PATCH"],
    response_model=UserResponse | None,
    endpoint=update_current_user,
    description="Update current user",
)
