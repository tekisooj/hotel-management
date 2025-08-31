from sqlalchemy import Column, String, UUID
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum
from sqlalchemy import Enum as SqlEnum

Base = declarative_base()

class UserType(str, Enum):
    STAFF = "staff"
    GUEST = "guest"

class User(Base):
    __tablename__ = "users"
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, index=True)
    name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    user_type = Column(SqlEnum(UserType), default=UserType.GUEST, nullable=False)