
from datetime import datetime
from uuid import UUID
from fastapi import Depends, Request, Response
from services.booking_service.app.db_client import HotelManagementDBClient
from services.booking_service.app.schemas import Booking, BookingUpdateRequest

def get_hotel_management_db_client(request: Request) -> HotelManagementDBClient:
    return request.app.state.hotel_management_db_client

async def add_booking(booking: Booking, hotel_management_db_client: HotelManagementDBClient = Depends(get_hotel_management_db_client)) -> UUID:
    return hotel_management_db_client.add_booking(booking)

async def get_booking(booking_uuid: UUID, hotel_management_db_client: HotelManagementDBClient = Depends(get_hotel_management_db_client)) -> Booking | None:
    return hotel_management_db_client.get_booking(booking_uuid)

async def get_filtered_bookings(
        hotel_management_db_client: HotelManagementDBClient = Depends(get_hotel_management_db_client),
        user_uuid: UUID | None = None,
        room_uuid: UUID | None = None,
        status: str | None = None,
        check_in: datetime | None = None,
        check_out: datetime | None = None) -> list[Booking]:
    return hotel_management_db_client.get_filtered_bookings(user_uuid=user_uuid, room_uuid=room_uuid, status=status, check_in=check_in, check_out=check_out)

async def update_booking(update_request: BookingUpdateRequest, hotel_management_db_client: HotelManagementDBClient = Depends(get_hotel_management_db_client)) -> Booking:
    return hotel_management_db_client.update_booking(update_request)

async def cancel_booking(booking_uuid: UUID, hotel_management_db_client: HotelManagementDBClient = Depends(get_hotel_management_db_client)) -> Booking:
    return hotel_management_db_client.cancel_booking(booking_uuid)

async def check_availability(room_uuid: UUID, check_in: datetime, check_out: datetime, hotel_management_db_client: HotelManagementDBClient = Depends(get_hotel_management_db_client)) -> bool:
    return hotel_management_db_client.check_availability(room_uuid, check_in, check_out)