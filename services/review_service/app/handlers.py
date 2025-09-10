from uuid import UUID
from fastapi import Depends, HTTPException, Request, Response
from services.property_service.app.schemas import Property
from services.property_service.app.db_client import HotelManagementDBClient
from services.review_service.app.db_client import ReviewDBClient
from services.review_service.app.schemas import Review

def get_review_db_client(request: Request) -> ReviewDBClient:
    return request.app.state.review_db_client

async def add_review(review: Review, review_db_client: ReviewDBClient = Depends(get_review_db_client)) -> UUID:
    return review_db_client.add_review(review)

async def get_property_reviews(property_uuid: UUID, review_db_client: ReviewDBClient = Depends(get_review_db_client)) -> list[Review]:
    return review_db_client.get_property_reviews(property_uuid=property_uuid)

async def get_user_reviews(user_uuid: UUID, review_db_client: ReviewDBClient = Depends(get_review_db_client)) -> list[Review]:
    return review_db_client.get_user_reviews(user_uuid=user_uuid)
