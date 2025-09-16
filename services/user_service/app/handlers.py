from uuid import UUID
from fastapi import Depends, HTTPException, Request, Response
from models import User
from schemas import SignUpRequest, UserCreate, UserResponse, UserUpdate
from db_client import HotelManagementDBClient
from services.user_service.app.cognito_client import CognitoClient

def get_hotel_management_db_client(request: Request) -> HotelManagementDBClient:
    return request.app.state.hotel_management_db_client

def get_cognito_client(request: Request) -> CognitoClient:
    return request.app.state.cognito_client

def get_current_user_uuid(request: Request) -> UUID:
    user_claims = request.state.user
    if not user_claims or "sub" not in user_claims:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return UUID(user_claims["sub"])

async def get_logged_in_user(
    hotel_management_db_client: HotelManagementDBClient = Depends(get_hotel_management_db_client),
    user_uuid: UUID = Depends(get_current_user_uuid)
) -> UserResponse | None:
    user = hotel_management_db_client.get_user(user_uuid)
    return user

async def register_user(
    sign_up_data: SignUpRequest,
    db_client: HotelManagementDBClient = Depends(get_hotel_management_db_client),
    cognito_client: CognitoClient = Depends(get_cognito_client),
    user_uuid: UUID = Depends(get_current_user_uuid)
) -> UUID:

    cognito_client.sign_up(sign_up_data)

    user_data = UserCreate(**sign_up_data.model_dump())

    return db_client.create_user(user_data)

async def get_user(user_uuid: UUID, hotel_management_db_client: HotelManagementDBClient = Depends(get_hotel_management_db_client)) -> UserResponse | None:
    return hotel_management_db_client.get_user(user_uuid)

async def delete_user(user_uuid: UUID, hotel_management_db_client: HotelManagementDBClient = Depends(get_hotel_management_db_client)) -> None:
    return hotel_management_db_client.delete_user(user_uuid)

async def update_user(
    user_uuid: UUID,
    user_data: UserUpdate,
    db_client: HotelManagementDBClient = Depends(get_hotel_management_db_client)
) -> UserResponse | None:
    updated = db_client.update_user(user_uuid, user_data)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    return updated