from uuid import UUID
from fastapi import Depends, HTTPException, Request
from schemas import (
    CurrentUserUpsertRequest,
    SignUpRequest,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from db_client import HotelManagementDBClient
from cognito_client import CognitoClient
import time, logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_hotel_management_db_client(request: Request) -> HotelManagementDBClient:
    return request.app.state.user_table_client

def get_cognito_client(request: Request) -> CognitoClient:
    return request.app.state.cognito_client

def get_current_user_uuid(request: Request) -> UUID:
    user_claims = getattr(request.state, "user", None)
    if not user_claims or "sub" not in user_claims:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return UUID(user_claims["sub"])

async def get_logged_in_user(
    request: Request,
    hotel_management_db_client: HotelManagementDBClient = Depends(get_hotel_management_db_client),
    user_uuid: UUID = Depends(get_current_user_uuid),
) -> UserResponse:

    start = time.time()
    try:
        user = hotel_management_db_client.get_user(user_uuid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        elapsed = time.time() - start
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def upsert_logged_in_user(
    payload: CurrentUserUpsertRequest,
    hotel_management_db_client: HotelManagementDBClient = Depends(get_hotel_management_db_client),
    user_uuid: UUID = Depends(get_current_user_uuid),
) -> UserResponse:

    existing_user = hotel_management_db_client.get_user(user_uuid)
    if existing_user:
        update_payload = UserUpdate(
            name=payload.name,
            last_name=payload.last_name,
            email=payload.email,
            user_type=payload.user_type,
        )
        updated_user = hotel_management_db_client.update_user(user_uuid, update_payload)
        return updated_user or existing_user

    user_create = UserCreate(
        name=payload.name,
        last_name=payload.last_name,
        email=payload.email,
        user_type=payload.user_type,
    )

    try:
        hotel_management_db_client.create_user(user_create, user_uuid=user_uuid)
    except HTTPException as exc:
        if exc.status_code == 409:
            logger.warning("User already exists, returning current data")
            existing_user = hotel_management_db_client.get_user(user_uuid)
            if existing_user:
                return existing_user
        raise

    created_user = hotel_management_db_client.get_user(user_uuid)
    if not created_user:
        raise HTTPException(status_code=500, detail="Failed to persist user")

    return created_user


async def register_user(
    sign_up_data: SignUpRequest,
    db_client: HotelManagementDBClient = Depends(get_hotel_management_db_client),
    cognito_client: CognitoClient = Depends(get_cognito_client),
) -> UUID:
    start = time.time()
    try:
        cognito_client.sign_up(sign_up_data)
        user_data = UserCreate(**sign_up_data.model_dump())
        user_id = db_client.create_user(user_data)
        return user_id
    except Exception as e:
        raise HTTPException(status_code=500, detail="User registration failed")

async def get_user(
    user_uuid: UUID,
    hotel_management_db_client: HotelManagementDBClient = Depends(get_hotel_management_db_client),
) -> UserResponse:
    start = time.time()
    try:
        user = hotel_management_db_client.get_user(user_uuid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def delete_user(
    user_uuid: UUID,
    hotel_management_db_client: HotelManagementDBClient = Depends(get_hotel_management_db_client),
) -> None:
    start = time.time()
    try:
        hotel_management_db_client.delete_user(user_uuid)
    except Exception:
        raise HTTPException(status_code=500, detail="User deletion failed")

async def update_user(
    user_uuid: UUID,
    user_data: UserUpdate,
    db_client: HotelManagementDBClient = Depends(get_hotel_management_db_client),
) -> UserResponse:
    start = time.time()
    try:
        updated = db_client.update_user(user_uuid, user_data)
        if not updated:
            raise HTTPException(status_code=404, detail="User not found")
        return updated
    except Exception:
        raise HTTPException(status_code=500, detail="User update failed")
