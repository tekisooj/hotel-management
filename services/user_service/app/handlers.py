from uuid import UUID
from fastapi import Depends, HTTPException, Request, Response
from services.user_service.app.models import User
from services.user_service.app.schemas import UserCreate, UserResponse, UserUpdate
from app.db_client import UserDBClient

def get_user_db_client(request: Request) -> UserDBClient:
    return request.app.state.user_db_client

def get_current_user_uuid(request: Request) -> UUID:
    user_claims = request.state.user
    if not user_claims or "sub" not in user_claims:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return UUID(user_claims["sub"])

async def get_logged_in_user(
    user_db_client: UserDBClient = Depends(get_user_db_client),
    user_uuid: UUID = Depends(get_current_user_uuid)
) -> UserResponse | None:
    user = user_db_client.get_user(user_uuid)
    return user

async def register_user(
    user_data: UserCreate,
    db_client: UserDBClient = Depends(get_user_db_client),
    user_uuid: UUID = Depends(get_current_user_uuid)
) -> UserResponse:
    return db_client.create_user(user_data)

async def get_user(user_uuid: UUID, user_db_client: UserDBClient = Depends(get_user_db_client)) -> UserResponse | None:
    return user_db_client.get_user(user_uuid)

async def delete_user(user_uuid: UUID, user_db_client: UserDBClient = Depends(get_user_db_client)) -> None:
    return user_db_client.delete_user(user_uuid)

async def update_user(
    user_uuid: UUID,
    user_data: UserUpdate,
    db_client: UserDBClient = Depends(get_user_db_client)
) -> UserResponse | None:
    updated = db_client.update_user(user_uuid, user_data)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    return updated