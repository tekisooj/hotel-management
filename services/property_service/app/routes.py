from uuid import UUID
from fastapi import APIRouter

from services.property_service.app.handlers import add_property

router = APIRouter()


router.add_api_route(
    path="/property/add",
    methods=["POST"],
    response_model=UUID,
    endpoint=add_property,
    description="Add a new property"
)