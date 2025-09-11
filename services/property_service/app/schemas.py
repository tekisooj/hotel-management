from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID


class Amenity(BaseModel):
    name: str = Field(description="Name of an amenity")

class RoomType(str, Enum):
    SINGLE = "single"
    DOUBLE = "double"
    SUITE = "suite"
    FAMILY = "family"
    DELUXE = "deluxe"
    STUDIO = "studio"


class Room(BaseModel):

    uuid: UUID | None = Field(description="UUID of a room", default=None)
    property_uuid: UUID = Field(description="UUID of a property")
    name: str = Field(description="Room name")
    description: str = Field(description="Room description", default=None)
    capacity: int = Field(description="Room capacity")
    room_type: RoomType = Field(description="Room type")
    price_per_night: float = Field(description="Price per night")
    min_price_per_night: float = Field(description="Min price per night")
    max_price_per_night: float = Field(description="Max price per night")
    created_at: datetime | None = Field(description="Room created at", default=None)
    updated_at: datetime | None = Field(description="Room updated at", default=None)
    amenities: list[Amenity] | None = Field(description="List of all room amenities", default=[])


class Property(BaseModel):

    uuid: UUID | None = Field(description="UUID of a property", default=None)
    user_uuid: UUID = Field(description="UUID of a property owner")
    name: str = Field(description="Property name")
    description: str | None = Field(description="Property description", default=None)
    country: str = Field(description="Country the property is in")
    state: str | None = Field(description="State the property is in", default=None)
    city: str = Field(description="City the property is in")
    county: str | None = Field(description="County or municipality the property is in", default=None)
    address: str = Field(description="Address of the property - street name and number")
    full_address: str | None = Field(description="Full address of the property", default=None)
    latitude: float | None = Field(description="Latitude of the property", default=None)
    longitude: float | None = Field(description="Longitude of the property", default=None)
    created_at: datetime | None = Field(description="Property created at", default=None)
    updated_at: datetime | None = Field(description="Property updated at", default=None)
