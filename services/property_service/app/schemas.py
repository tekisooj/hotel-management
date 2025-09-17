from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class Amenity(BaseModel):
    name: str = Field(description="Name of an amenity")


class Image(BaseModel):
    key: str = Field(description="S3 object key for the image")
    url: str | None = Field(default=None, description="Temporary URL exposing the image")


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
    images: list[Image] | None = Field(description="List of room images stored in S3", default=[])


class Property(BaseModel):

    uuid: UUID | None = Field(description="UUID of a property", default=None)
    user_uuid: UUID = Field(description="UUID of a property owner")
    place_id: str | None = Field(description="External place provider id (e.g., AWS Location Places)", default=None)
    name: str = Field(description="Property name")
    description: str | None = Field(description="Property description", default=None)
    country: str = Field(description="Country the property is in")
    state: str | None = Field(description="State the property is in", default=None)
    city: str = Field(description="City the property is in")
    county: str | None = Field(description="County or municipality the property is in", default=None)
    address: str = Field(description="Address of the property - street name and number")
    full_address: str | None = Field(description="Full address of the property", default=None)
    latitude: Decimal | None = Field(description="Latitude of the property", default=None)
    longitude: Decimal | None = Field(description="Longitude of the property", default=None)
    city_key: str | None = Field(description="Computed city key COUNTRY#STATE#CITY", default=None)
    created_at: datetime | None = Field(description="Property created at", default=None)
    updated_at: datetime | None = Field(description="Property updated at", default=None)
    stars: int | None = Field(description="Number of stard", default=1)
    place_id: str | None = Field(description="AWS location place id", default=None)
    images: list[Image] | None = Field(description="List of property images stored in S3", default=[])


class PresignedUploadRequest(BaseModel):
    prefix: str = Field(description="Folder prefix under which the asset will be stored")
    content_type: str = Field(description="Content type of the asset being uploaded")
    extension: str | None = Field(default=None, description="Optional file extension to append to the generated key")


class PresignedUploadResponse(BaseModel):
    key: str = Field(description="Generated S3 object key")
    upload_url: str = Field(description="Pre-signed URL to upload the asset")
    fields: dict[str, str] = Field(description="Form fields required when performing the upload")
