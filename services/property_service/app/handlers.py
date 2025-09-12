from datetime import date
from uuid import UUID
from fastapi import Depends, HTTPException, Request, Response
from services.property_service.app.schemas import Amenity, Property, Room
from services.property_service.app.db_clients import PropertyTableClient, RoomTableClient
from decimal import Decimal

def get_property_table_client(request: Request) -> PropertyTableClient:
    return request.app.state.property_table_client

def get_room_table_client(request: Request) -> RoomTableClient:
    return request.app.state.room_table_client


def build_city_key(country: str, state: str | None, city: str) -> str:
    parts = [country.strip().upper()]
    parts.append(state.strip().upper() if state else "")
    parts.append(city.strip().upper())
    return "#".join(parts)


def set_property_full_address(property: Property)-> None:
    full_address = f"{property.address}"
    if property.county:
        full_address+=f",{property.county}"
    full_address+=f",{property.city}"
    if property.state:
        full_address+=f",{property.state}"
    full_address+=f",{property.country}"
    property.full_address=full_address
    property.city_key = build_city_key(property.country, property.state, property.city)

def get_coordinates_of_a_property(property: Property) -> tuple[float, float]:
    #TODO ADD THIS
    return 0, 0

async def add_property(
    property: Property,
    property_table_client: PropertyTableClient = Depends(get_property_table_client),
) -> UUID:
    
    set_property_full_address(property)
    # Latitude/longitude are provided by frontend; do not override here
    return property_table_client.add_property(property)

async def get_property(property_uuid: UUID, property_table_client: PropertyTableClient = Depends(get_property_table_client)) -> Property:

    return property_table_client.get_property(property_uuid)


async def get_properties_by_city(
    country: str,
    city: str,
    state: str | None = None,
    property_table_client: PropertyTableClient = Depends(get_property_table_client),
) -> list[Property]:
    city_key = build_city_key(country, state, city)
    return property_table_client.get_properties_by_city_key(city_key)


async def get_properties_near(
    latitude: float,
    longitude: float,
    delta: float,
    country: str | None = None,
    state: str | None = None,
    city: str | None = None,
    property_table_client: PropertyTableClient = Depends(get_property_table_client),
) -> list[Property]:
    return property_table_client.get_properties_in_bbox(
        Decimal(str(latitude)),
        Decimal(str(longitude)),
        delta,
        country=country,
        state=state,
        city=city,
    )


async def add_room(room: Room, room_table_client: RoomTableClient = Depends(get_room_table_client)) -> UUID:
    
    return room_table_client.add_room(room)

async def get_room(room_uuid: UUID, room_table_client: RoomTableClient = Depends(get_room_table_client)) -> Room:
    
    return room_table_client.get_room(room_uuid)

async def get_property_rooms(property_uuid: UUID, room_table_client: RoomTableClient = Depends(get_room_table_client)) -> list[Room]:

    return room_table_client.get_property_rooms(property_uuid)

async def get_filtered_rooms(
        property_uuid: UUID | None = None,
        capacity: int | None = None, 
        max_price_per_night: float | None = None, 
        amenities: list[Amenity] | None = None, 
        room_table_client: RoomTableClient = Depends(get_room_table_client)
    ) -> list[Room]:

    if property_uuid:
        return room_table_client.get_filtered_property_rooms(property_uuid, capacity, max_price_per_night, amenities)
    return room_table_client.get_filtered_rooms(capacity, max_price_per_night, amenities)
