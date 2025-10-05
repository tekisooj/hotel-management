from uuid import UUID
from fastapi import APIRouter
from handlers import (
    delete_user,
    get_logged_in_user,
    get_user,
    register_user,
    update_user,
    upsert_logged_in_user,
)
from schemas import UserResponse

router = APIRouter(prefix="")

router.add_api_route(
    path="/me",
    methods=["GET"],
    response_model=UserResponse,
    endpoint=get_logged_in_user,
    description="Returns the currently logged-in user's data",
    tags=["User"]
)

router.add_api_route(
    path="/me",
    methods=["POST"],
    response_model=UserResponse,
    endpoint=upsert_logged_in_user,
    description="Creates or updates the currently logged-in user's data",
    tags=["User"]
)

router.add_api_route(
    path="/user/{user_uuid}",
    methods=["GET"],
    response_model=UserResponse,
    endpoint=get_user,
    description="Fetch a user by UUID",
    tags=["User"]
)

router.add_api_route(
    path="/user",
    methods=["POST"],
    response_model=UUID,
    endpoint=register_user,
    description="Register a new user",
    tags=["User"]
)

router.add_api_route(
    path="/user/{user_uuid}",
    methods=["DELETE"],
    response_model=None,
    endpoint=delete_user,
    description="Delete a user by UUID",
    tags=["User"]
)

router.add_api_route(
    path="/user/{user_uuid}",
    methods=["PATCH"],
    response_model=UserResponse | None,
    endpoint=update_user,
    description="Update a user by UUID",
    tags=["User"]
)
