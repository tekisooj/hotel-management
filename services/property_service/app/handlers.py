from uuid import UUID
from fastapi import Depends, HTTPException, Request, Response
from services.property_service.app.schemas import Property
from services.property_service.app.db_client import HotelManagementDBClient

def get_hotel_management_db_client(request: Request) -> HotelManagementDBClient:
    return request.app.state.hotel_management_db_client

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

async def add_property(property: Property, hotel_management_db_client: HotelManagementDBClient = Depends(get_hotel_management_db_client)) -> UUID:
    
    set_property_full_address(property)
    latitude, longitude = get_coordinates_of_a_property(property)
    property.latitude = latitude
    property.longitude = longitude
    return hotel_management_db_client.add_property(property)