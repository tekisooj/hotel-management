from uuid import UUID
from fastapi import APIRouter

from handlers import add_review, get_property_reviews, get_user_reviews
from schemas import Review

router = APIRouter()


router.add_api_route(
    path="/review",
    methods=["POST"],
    response_model=UUID,
    endpoint=add_review,
    description="Add a new review for property"
)

router.add_api_route(
    path="/reviews/{property_uuid}",
    methods=["GET"],
    response_model=list[Review],
    endpoint=get_property_reviews,
    description="Get all property reviews"
)

router.add_api_route(
    path="/reviews/{user_uuid}",
    methods=["GET"],
    response_model=list[Review],
    endpoint=get_user_reviews,
    description="Get all user reviews"
)