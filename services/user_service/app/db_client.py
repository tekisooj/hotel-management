import json
from uuid import UUID

import boto3
from fastapi import HTTPException
from schemas import UserCreate, UserResponse, UserUpdate
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, User


class HotelManagementDBClient:
    def __init__(
        self,
        hotel_management_database_secret_name: str | None,
        region: str,
        db_proxy_endpoint: str | None = None,
    ) -> None:
        if not hotel_management_database_secret_name:
            raise ValueError("Secret name must be provided or set in environment variables.")


        self.db_url = self.build_db_url_from_secret(
            hotel_management_database_secret_name,
            region,
            db_proxy_endpoint,
        )

        if not self.db_url:
            raise ValueError("Unable to build DB URL.")

        self.engine = create_engine(self.db_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def get_secret_by_name(self, secret_name: str, region_name: str = "us-east-1") -> dict:
        client = boto3.client("secretsmanager", region_name=region_name)
        try:
            response = client.get_secret_value(SecretId=secret_name)
            return json.loads(response["SecretString"])
        except client.exceptions.ResourceNotFoundException:
            raise Exception(f"Secret {secret_name} not found.")
        except client.exceptions.ClientError as e:
            raise Exception(f"Error retrieving secret: {str(e)}")

    def build_db_url_from_secret(
        self,
        secret_name: str,
        region: str,
        db_proxy_endpoint: str | None = None,
    ) -> str:
        secret = self.get_secret_by_name(secret_name, region)

        username = str(secret.get("username", "")).strip()
        password = str(secret.get("password", "")).strip()
        port = str(secret.get("port", "")).strip()
        dbname = str(secret.get("dbname", "")).strip()

        host = db_proxy_endpoint or str(secret.get("host", "")).strip()

        if not all([username, password, host, port, dbname]):
            raise ValueError("Database secret is missing required fields.")

        return f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{dbname}"

    def get_session(self) -> Session:
        return self.SessionLocal()

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

            update_fields = update_data.model_dump(exclude_none=True)
            for field, value in update_fields.items():
                setattr(user, field, value)

            session.commit()
            session.refresh(user)
            return UserResponse.model_validate(user)
        finally:
            session.close()
