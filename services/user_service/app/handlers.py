from uuid import UUID
from fastapi import Depends, HTTPException, Request
from schemas import SignUpRequest, UserCreate, UserResponse, UserUpdate
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
    logger.info(f"🔥 /me endpoint invoked, starting processing UUID={user_uuid}")

    start = time.time()
    logger.info(f"➡️ /me called UUID={user_uuid}")
    try:
        logger.info("🏁 Entering HotelManagementDBClient.get_user()")
        user = hotel_management_db_client.get_user(user_uuid)
        if not user:
            logger.warning("⚠️ User not found")
            raise HTTPException(status_code=404, detail="User not found")
        elapsed = time.time() - start
        logger.info(f"✅ /me completed in {elapsed:.2f}s")
        return user
    except Exception as e:
        logger.exception(f"❌ Error fetching user {user_uuid}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def register_user(
    sign_up_data: SignUpRequest,
    db_client: HotelManagementDBClient = Depends(get_hotel_management_db_client),
    cognito_client: CognitoClient = Depends(get_cognito_client),
) -> UUID:
    start = time.time()
    try:
        logger.info("🧠 Registering user in Cognito...")
        cognito_client.sign_up(sign_up_data)
        user_data = UserCreate(**sign_up_data.model_dump())
        user_id = db_client.create_user(user_data)
        logger.info(f"✅ User registered in {time.time() - start:.2f}s")
        return user_id
    except Exception as e:
        logger.exception("❌ Registration failed")
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
        logger.info(f"✅ get_user finished in {time.time() - start:.2f}s")
        return user
    except Exception:
        logger.exception(f"❌ get_user failed for {user_uuid}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def delete_user(
    user_uuid: UUID,
    hotel_management_db_client: HotelManagementDBClient = Depends(get_hotel_management_db_client),
) -> None:
    start = time.time()
    try:
        hotel_management_db_client.delete_user(user_uuid)
        logger.info(f"✅ delete_user finished in {time.time() - start:.2f}s")
    except Exception:
        logger.exception(f"❌ delete_user failed for {user_uuid}")
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
        logger.info(f"✅ update_user finished in {time.time() - start:.2f}s")
        return updated
    except Exception:
        logger.exception(f"❌ update_user failed for {user_uuid}")
        raise HTTPException(status_code=500, detail="User update failed")
