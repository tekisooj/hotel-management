from pydantic import BaseModel, Field, EmailStr
from uuid import UUID
from enum import Enum

class UserType(str, Enum):
    STAFF = "staff"
    GUEST = "guest"

class UserCreate(BaseModel):
    name: str = Field(description="Name of a user")
    last_name: str = Field(description="Last name of a user")
    email: EmailStr = Field(description="Email of a user")
    password: str = Field(description="Password")
    user_type: UserType = Field(description="User type", default=UserType.GUEST)

    class Config:
        from_attributes = True

        
class UserResponse(BaseModel):
    uuid: UUID = Field(description="UUID of a user")
    name: str = Field(description="Name of a user")
    last_name: str = Field(description="Last name of a user")
    email: EmailStr = Field(description="Email of a user")
    user_type: UserType = Field(description="User type", default=UserType.GUEST)

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, description="Name of a user")
    last_name: str | None = Field(default=None, description="Last name of a user")
    email: EmailStr | None = Field(default=None, description="Email of a user")
    password: str | None = Field(default=None, description="Password")
    user_type: UserType | None = Field(default=None, description="User type")

    class Config:
        from_attributes = True