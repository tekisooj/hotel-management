

from datetime import datetime
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, Field


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Booking(BaseModel):
    uuid: UUID = Field(description="Booking UUID")
    user_uuid: UUID = Field(description="User UUID")
    room_uuid: UUID = Field(description="Room UUID")
    check_in: datetime = Field(description="Check in time")
    check_out: datetime = Field(description="Check in time")
    total_price: float = Field(description="Total price for the booking")
    status: BookingStatus = Field(description="Status of the booking")
    created_at: datetime = Field(description="Created at")
    updated_at: datetime = Field(description="Updated at")
    
    class Config:
        from_attributes = True

class BookingUpdateRequest(BaseModel):
    booking_uuid: UUID = Field(description="Booking uuid")
    check_in: datetime | None = Field(default=None)
    check_out: datetime | None = Field(default=None)
    total_price: float | None = Field(default=None)
    status: BookingStatus | None = Field(default=None)

class AvailabilityBulkRequest(BaseModel):
    room_uuids: list[UUID] = Field(default_factory=list)
    check_in: datetime = Field(description="Check in time")
    check_out: datetime = Field(description="Check out time")
