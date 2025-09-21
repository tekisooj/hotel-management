import os
import json
from uuid import UUID
import boto3
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from schemas import UserCreate, UserResponse, UserUpdate
from models import User


class HotelManagementDBClient:
    def __init__(self, hotel_management_database_secret_name: str | None, region: str, proxy_endpoint: str | None) -> None:
        if not hotel_management_database_secret_name:
            raise ValueError("Secret name must be provided or set in environment variables.")

        self.secret_name = hotel_management_database_secret_name
        self.region = region
        self._engine = None
        self._SessionLocal = None
        self.proxy_endpoint = proxy_endpoint

    def _get_secret(self) -> dict:
        client = boto3.client("secretsmanager", region_name=self.region)
        response = client.get_secret_value(SecretId=self.secret_name)
        return json.loads(response["SecretString"])

    def _build_db_url(self) -> str:
        secret = self._get_secret()
        username = secret["username"].strip()
        password = secret["password"].strip()
        port = str(secret["port"]).strip()
        dbname = secret["dbname"].strip()

        host = self.proxy_endpoint if self.proxy_endpoint else secret["host"].strip()

        return f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{dbname}"

    def _init_engine(self):
        if not self._engine:
            self._engine = create_engine(self._build_db_url())
            self._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)

    def get_session(self) -> Session:
        self._init_engine()
        return self._SessionLocal() # type: ignore

    def create_user(self, user: UserCreate) -> UUID:
        session = self.get_session()
        try:
            user_obj = User(
                name=user.name,
                last_name=user.last_name,
                email=user.email,
                user_type=user.user_type,
            )
            session.add(user_obj)
            session.commit()
            session.refresh(user_obj)
            return UserResponse.model_validate(user_obj).uuid
        finally:
            session.close()

    def get_user(self, user_uuid: UUID) -> UserResponse | None:
        session = self.get_session()
        try:
            user = session.query(User).filter(User.uuid == user_uuid).first()
            return UserResponse.model_validate(user) if user else None
        finally:
            session.close()

    def delete_user(self, user_uuid: UUID) -> None:
        session = self.get_session()
        try:
            user = session.query(User).filter(User.uuid == user_uuid).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            session.delete(user)
            session.commit()
        finally:
            session.close()

    def update_user(self, user_uuid: UUID, update_data: UserUpdate) -> UserResponse | None:
        session = self.get_session()
        try:
            user = session.query(User).filter(User.uuid == user_uuid).first()
            if not user:
                return None

            for field, value in update_data.model_dump(exclude_none=True).items():
                setattr(user, field, value)

            session.commit()
            session.refresh(user)
            return UserResponse.model_validate(user)
        finally:
            session.close()
