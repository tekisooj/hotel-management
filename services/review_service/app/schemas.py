from pydantic import BaseModel, Field
from uuid import UUID

class Review(BaseModel):
    uuid: UUID = Field(description="Review uuid")
    property_uuid: UUID = Field(description="Property uuid")
    user_uuid: UUID = Field(description="User uuid")
    rating: float = Field(description="Property rating", le=5, ge=1)
    commet: str = Field(description="Review comment")
    timestamp: str | None = Field(description="Timestamp")