from uuid import UUID
from fastapi import Depends, HTTPException, Request
from models import User
from schemas import SignUpRequest, UserCreate, UserResponse, UserUpdate
from db_client import HotelManagementDBClient
from cognito_client import CognitoClient
import logging

logger = logging.getLogger()


def get_hotel_management_db_client(request: Request) -> HotelManagementDBClient:
    return request.app.state.user_table_client


def get_cognito_client(request: Request) -> CognitoClient:
    return request.app.state.cognito_client


def get_current_user_uuid(request: Request) -> UUID:
    """Extracts Cognito user UUID from JWT claims."""
    user_claims = getattr(request.state, "user", None)
    if not user_claims or "sub" not in user_claims:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return UUID(user_claims["sub"])


async def get_logged_in_user(
    request: Request,
    hotel_management_db_client: HotelManagementDBClient = Depends(get_hotel_management_db_client),
    user_uuid: UUID = Depends(get_current_user_uuid),
) -> UserResponse:
    """
    Fetches the logged-in user's record from the database.
    """
    try:
        logger.info(f"Fetching user with UUID={user_uuid}")
        user = hotel_management_db_client.get_user(user_uuid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        logger.error(f"Error fetching user {user_uuid}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def register_user(
    sign_up_data: SignUpRequest,
    db_client: HotelManagementDBClient = Depends(get_hotel_management_db_client),
    cognito_client: CognitoClient = Depends(get_cognito_client),
) -> UUID:
    """
    Register user both in Cognito and the local DB.
    """
    try:
        logger.info("Signing up user in Cognito")
        cognito_client.sign_up(sign_up_data)

        user_data = UserCreate(**sign_up_data.model_dump())
        logger.info("Creating user in DB")
        user_id = db_client.create_user(user_data)
        return user_id
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail="User registration failed")


async def get_user(
    user_uuid: UUID,
    hotel_management_db_client: HotelManagementDBClient = Depends(get_hotel_management_db_client),
) -> UserResponse:
    try:
        user = hotel_management_db_client.get_user(user_uuid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        logger.error(f"Error fetching user {user_uuid}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def delete_user(
    user_uuid: UUID,
    hotel_management_db_client: HotelManagementDBClient = Depends(get_hotel_management_db_client),
) -> None:
    try:
        logger.info(f"Deleting user {user_uuid}")
        hotel_management_db_client.delete_user(user_uuid)
    except Exception as e:
        logger.error(f"Error deleting user {user_uuid}: {e}")
        raise HTTPException(status_code=500, detail="User deletion failed")


async def update_user(
    user_uuid: UUID,
    user_data: UserUpdate,
    db_client: HotelManagementDBClient = Depends(get_hotel_management_db_client),
) -> UserResponse:
    try:
        logger.info(f"Updating user {user_uuid}")
        updated = db_client.update_user(user_uuid, user_data)
        if not updated:
            raise HTTPException(status_code=404, detail="User not found")
        return updated
    except Exception as e:
        logger.error(f"Error updating user {user_uuid}: {e}")
        raise HTTPException(status_code=500, detail="User update failed")
