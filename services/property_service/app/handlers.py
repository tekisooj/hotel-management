from decimal import Decimal
from uuid import UUID

from fastapi import Depends, HTTPException, Request

from db_clients import PropertyTableClient, RoomTableClient
from schemas import (
    Amenity,
    PresignedUploadRequest,
    PresignedUploadResponse,
    Property,
    Room,
)
from services.property_service.app.utils import add_image_url, add_image_urls, strip_image_urls
from storage import S3AssetStorage


def get_property_table_client(request: Request) -> PropertyTableClient:
    return request.app.state.property_table_client


def get_room_table_client(request: Request) -> RoomTableClient:
    return request.app.state.room_table_client


def get_asset_storage(request: Request) -> S3AssetStorage | None:
    return getattr(request.app.state, "asset_storage", None)


def build_city_key(country: str, state: str | None, city: str) -> str:
    parts = [country.strip().upper()]
    parts.append(state.strip().upper() if state else "")
    parts.append(city.strip().upper())
    return "#".join(parts)


def set_property_full_address(property: Property) -> None:
    full_address = f"{property.address}"
    if property.county:
        full_address += f",{property.county}"
    full_address += f",{property.city}"
    if property.state:
        full_address += f",{property.state}"
    full_address += f",{property.country}"
    property.full_address = full_address
    property.city_key = build_city_key(property.country, property.state, property.city)


async def add_property(
    property: Property,
    property_table_client: PropertyTableClient = Depends(get_property_table_client),
) -> UUID:
    set_property_full_address(property)
    strip_image_urls(property.images)
    return property_table_client.add_property(property)


async def get_property(
    property_uuid: UUID,
    property_table_client: PropertyTableClient = Depends(get_property_table_client),
    asset_storage: S3AssetStorage | None = Depends(get_asset_storage),
) -> Property:
    property_obj = property_table_client.get_property(property_uuid)
    return add_image_url(property_obj, asset_storage) # type: ignore


async def get_user_properties(
    user_uuid: UUID,
    property_table_client: PropertyTableClient = Depends(get_property_table_client),
    asset_storage: S3AssetStorage | None = Depends(get_asset_storage),
) -> list[Property]:
    properties = property_table_client.get_user_properties(user_uuid)
    return add_image_urls(properties, asset_storage) # type: ignore


async def delete_property(
    property_uuid: UUID,
    property_table_client: PropertyTableClient = Depends(get_property_table_client),
) -> UUID:
    return property_table_client.delete_property(property_uuid)


async def get_properties_by_city(
    country: str,
    city: str,
    state: str | None = None,
    property_table_client: PropertyTableClient = Depends(get_property_table_client),
    asset_storage: S3AssetStorage | None = Depends(get_asset_storage),
) -> list[Property]:
    city_key = build_city_key(country, state, city)
    properties = property_table_client.get_properties_by_city_key(city_key)
    return add_image_urls(properties, asset_storage) # type: ignore


async def get_properties_near(
    latitude: float,
    longitude: float,
    radius_km: float,
    country: str | None = None,
    state: str | None = None,
    city: str | None = None,
    property_table_client: PropertyTableClient = Depends(get_property_table_client),
    asset_storage: S3AssetStorage | None = Depends(get_asset_storage),
) -> list[Property]:
    properties = property_table_client.get_properties_within_radius(
        Decimal(str(latitude)),
        Decimal(str(longitude)),
        radius_km,
        country=country,
        state=state,
        city=city,
    )
    return add_image_urls(properties, asset_storage) # type: ignore


async def add_room(
    room: Room,
    room_table_client: RoomTableClient = Depends(get_room_table_client),
) -> UUID:
    strip_image_urls(room.images)
    return room_table_client.add_room(room)


async def get_room(
    room_uuid: UUID,
    room_table_client: RoomTableClient = Depends(get_room_table_client),
    asset_storage: S3AssetStorage | None = Depends(get_asset_storage),
) -> Room:
    room_obj = room_table_client.get_room(room_uuid)
    return add_image_url(room_obj, asset_storage) # type: ignore


async def delete_room(
    room_uuid: UUID,
    room_table_client: RoomTableClient = Depends(get_room_table_client),
) -> UUID:
    return room_table_client.delete_rooom(room_uuid)


async def get_property_rooms(
    property_uuid: UUID,
    room_table_client: RoomTableClient = Depends(get_room_table_client),
    asset_storage: S3AssetStorage | None = Depends(get_asset_storage),
) -> list[Room]:
    rooms = room_table_client.get_property_rooms(property_uuid)
    return add_image_urls(rooms, asset_storage) # type: ignore


async def get_filtered_rooms(
    property_uuid: UUID | None = None,
    capacity: int | None = None,
    max_price_per_night: float | None = None,
    amenities: list[Amenity] | None = None,
    room_table_client: RoomTableClient = Depends(get_room_table_client),
    asset_storage: S3AssetStorage | None = Depends(get_asset_storage),
) -> list[Room]:
    if property_uuid:
        rooms = room_table_client.get_filtered_property_rooms(
            property_uuid,
            capacity,
            max_price_per_night,
            amenities,
        )
    else:
        rooms = room_table_client.get_filtered_rooms(
            capacity,
            max_price_per_night,
            amenities,
        )
    return add_image_urls(rooms, asset_storage) # type: ignore


async def create_asset_upload_url(
    payload: PresignedUploadRequest,
    asset_storage: S3AssetStorage | None = Depends(get_asset_storage),
) -> PresignedUploadResponse:
    if not asset_storage:
        raise HTTPException(status_code=503, detail="Asset storage is not configured.")
    upload_payload = asset_storage.create_upload(
        payload.prefix,
        payload.content_type,
        payload.extension,
    )
    return PresignedUploadResponse(
        key=upload_payload["key"],
        upload_url=upload_payload["url"],
        fields=upload_payload["fields"],
    )
