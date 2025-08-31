from uuid import UUID, uuid4

from fastapi import HTTPException
from services.user_service.app.schemas import UserCreate, UserResponse, UserUpdate
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, User

class UserDBClient:
    def __init__(
            self, db_url: str | None
    ) -> None:

        if not db_url:
            raise ValueError("Database url must be provided or set in environment variables.")
        
        self.db_url = db_url
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        return self.SessionLocal()
    
    def create_user(self, user: UserCreate) -> UserResponse:
        session = self.get_session()

        try:
            user_obj = User(
                uuid=uuid4(),
                name=user.name,
                last_name=user.last_name,
                email=user.email,
                user_type=user.user_type
            )
            session.add(user_obj)
            session.commit()
            session.refresh(user_obj)

            return UserResponse.model_validate(user_obj)
        finally: 
            session.close()
    
    def get_user(self, user_uuid: UUID) -> UserResponse | None:
        session = self.get_session()
        try:
            user = session.query(User).filter(User.uuid == user_uuid).first()
            if not user:
                return None
            return UserResponse.model_validate(user)
        finally:        
            session.close()


    def delete_user(self, user_uuid: UUID) -> None:
        session = self.get_session()
        user = session.query(User).filter(User.uuid == user_uuid).first()
        if not user:
            session.close()
            raise HTTPException(status_code=404, detail="User not found")
        session.delete(user)
        session.commit()
        session.close()
        return
    
    def update_user(self, user_uuid: UUID, update_data: UserUpdate) -> UserResponse | None:
        session = self.get_session()
        user = session.query(User).filter(User.uuid == user_uuid).first()

        if not user:
            session.close()
            return None
        
        update_fields = update_data.model_dump(exclude_none=True)
        for field, value in update_fields.items():
            setattr(user, field, value)

        session.commit()
        session.refresh(user)
        session.close()

        return UserResponse.model_validate(user)