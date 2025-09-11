from datetime import date
from uuid import UUID
from fastapi import Depends, HTTPException, Request, Response
from services.property_service.app.schemas import Amenity, Property, Room
from services.property_service.app.db_clients import PropertyTableClient, RoomTableClient

def get_property_table_client(request: Request) -> PropertyTableClient:
    return request.app.state.property_table_client

def get_room_table_client(request: Request) -> RoomTableClient:
    return request.app.state.room_table_client


def set_property_full_address(property: Property)-> None:
    full_address = f"{property.address}"
    if property.county:
        full_address+=f",{property.county}"
    full_address+=f",{property.city}"
    if property.state:
        full_address+=f",{property.state}"
    full_address+=f",{property.country}"
    property.full_address=full_address

def get_coordinates_of_a_property(property: Property) -> tuple[float, float]:
    #TODO ADD THIS
    return 0, 0

async def add_property(property: Property, property_table_client: PropertyTableClient = Depends(get_property_table_client)) -> UUID:
    
    set_property_full_address(property)
    latitude, longitude = get_coordinates_of_a_property(property)
    property.latitude = latitude
    property.longitude = longitude
    return property_table_client.add_property(property)

async def get_property(property_uuid: UUID, property_table_client: PropertyTableClient = Depends(get_property_table_client)) -> Property:

    return property_table_client.get_property(property_uuid)


async def add_room(room: Room, room_table_client: RoomTableClient = Depends(get_room_table_client)) -> UUID:
    
    return room_table_client.add_room(room)

async def get_room(room_uuid: UUID, room_table_client: RoomTableClient = Depends(get_room_table_client)) -> Room:
    
    return room_table_client.get_room(room_uuid)

async def get_property_rooms(property_uuid: UUID, room_table_client: RoomTableClient = Depends(get_room_table_client)) -> list[Room]:

    return room_table_client.get_property_rooms(property_uuid)

async def get_filtered_rooms(
        capacity: int | None = None, 
        max_price_per_night: float | None = None, 
        amenities: list[Amenity] | None = None, 
        room_table_client: RoomTableClient = Depends(get_room_table_client)
    ) -> list[Room]:

    return room_table_client.get_filtered_rooms(capacity, max_price_per_night, amenities)