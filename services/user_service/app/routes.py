from uuid import UUID
from fastapi import APIRouter
from app.handlers import get_logged_in_user, get_user, delete_user, register_user, update_user
from services.user_service.app.models import User
from services.user_service.app.schemas import  UserCreate, UserResponse

router = APIRouter()

router.add_api_route(
    path="/me",
    methods=["GET"],
    response_model=UserResponse,
    endpoint=get_logged_in_user,
    description="Get a user based on uuid"
)

router.add_api_route(
    path="/user/{user_uuid}",
    methods=["GET"],
    response_model=UserResponse,
    endpoint=get_user,
    description="Get a user based on uuid"
)

router.add_api_route(
    path="/user",
    methods=["POST"],
    response_model=UUID,
    endpoint=register_user,
    description="Add a new user"
)

router.add_api_route(
    path="/user/{user_uuid}",
    methods=["DELETE"],
    response_model=None,
    endpoint=delete_user,
    description="Delete a user based on uuid"
)

router.add_api_route(
    path="/user/{user_uuid}",
    methods=["PATCH"],
    response_model=UserResponse | None,
    endpoint=update_user,
    description="Delete a user based on uuid"
)