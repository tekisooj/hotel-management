import json
from uuid import UUID
from typing import Optional

import boto3
from botocore.config import Config as BotoConfig
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from schemas import UserCreate, UserResponse, UserUpdate
from models import User


class HotelManagementDBClient:
    """
    DB client with:
      - fast Secrets Manager timeouts
      - fast Postgres connect timeout
      - connection liveness checks (pool_pre_ping)
      - clear logging on engine init
    """

    def __init__(self, hotel_management_database_secret_name: Optional[str], region: str, proxy_endpoint: Optional[str]) -> None:
        if not hotel_management_database_secret_name:
            raise ValueError("Secret name must be provided or set in environment variables.")

        self.secret_name = hotel_management_database_secret_name
        self.region = region
        self.proxy_endpoint = proxy_endpoint

        self._engine = None
        self._SessionLocal = None
        self._cached_secret: Optional[dict] = None

        self._boto = boto3.client(
            "secretsmanager",
            region_name=self.region,
            config=BotoConfig(connect_timeout=3, read_timeout=3, retries={"max_attempts": 2})
        )

    def _get_secret(self) -> dict:
        if self._cached_secret:
            return self._cached_secret
        try:
            resp = self._boto.get_secret_value(SecretId=self.secret_name)
            self._cached_secret = json.loads(resp["SecretString"])
            return self._cached_secret
        except Exception as e:
            raise RuntimeError(f"Failed to read DB secret '{self.secret_name}' in {self.region}: {e}")

    def _build_db_url(self) -> str:
        secret = self._get_secret()
        username = str(secret["username"]).strip()
        password = str(secret["password"]).strip()
        port = str(secret["port"]).strip()
        dbname = str(secret["dbname"]).strip()

        host = self.proxy_endpoint or str(secret["host"]).strip()

        print(f"[DB] Connecting to postgresql://{username}@{host}:{port}/{dbname}")

        return f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{dbname}"

    def _init_engine(self):
        if self._engine:
            return
        try:
            db_url = self._build_db_url()
            self._engine = create_engine(
                db_url,
                pool_pre_ping=True,
                pool_recycle=300,
                connect_args={"connect_timeout": 5},
            )
            self._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
        except Exception as e:
            print(f"[DB] Engine init failed: {e}")
            raise

    def get_session(self) -> Session:
        self._init_engine()
        return self._SessionLocal()  # type: ignore


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

    def get_user(self, user_uuid: UUID) -> Optional[UserResponse]:
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

    def update_user(self, user_uuid: UUID, update_data: UserUpdate) -> Optional[UserResponse]:
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
