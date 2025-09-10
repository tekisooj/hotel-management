from uuid import UUID
from fastapi import APIRouter

from services.property_service.app.handlers import add_property
from services.review_service.app.handlers import add_review, get_property_reviews, get_user_reviews
from services.review_service.app.schemas import Review

router = APIRouter()


router.add_api_route(
    path="/review/{property_uuid}",
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