import os
import json
import time
import logging
import boto3
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from schemas import UserCreate, UserResponse, UserUpdate
from models import User

logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
        logger.info("Fetching secret from Secrets Manager...")
        start = time.time()
        client = boto3.client("secretsmanager", region_name=self.region)
        response = client.get_secret_value(SecretId=self.secret_name)
        elapsed = time.time() - start
        logger.info(f"Secret fetched successfully in {elapsed:.2f}s")
        return json.loads(response["SecretString"])

    def _build_db_url(self) -> str:
        secret = self._get_secret()
        username = secret["username"].strip()
        password = secret["password"].strip()
        port = str(secret["port"]).strip()
        dbname = secret["dbname"].strip()
        host = self.proxy_endpoint if self.proxy_endpoint else secret["host"].strip()
        url = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{dbname}"
        logger.info(f"Built DB URL for host {host}:{port}/{dbname}")
        return url

    def _init_engine(self):
        if not self._engine:
            logger.info("Initializing SQLAlchemy engine...")
            start = time.time()
            self._engine = create_engine(self._build_db_url(), pool_pre_ping=True)
            self._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
            logger.info(f"Engine created in {time.time() - start:.2f}s")

    def get_session(self) -> Session:
        self._init_engine()
        logger.info("New DB session started")
        return self._SessionLocal()

    def create_user(self, user: UserCreate) -> UUID:
        logger.info("Creating new user in DB")
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
            logger.info(f"User created with UUID {user_obj.uuid}")
            return UserResponse.model_validate(user_obj).uuid
        finally:
            session.close()
            logger.info("Session closed after user creation")

    def get_user(self, user_uuid: UUID) -> UserResponse | None:
        logger.info(f"Fetching user {user_uuid} from DB")
        session = self.get_session()
        try:
            user = session.query(User).filter(User.uuid == user_uuid).first()
            if user:
                logger.info(f"User found: {user.email}")
                return UserResponse.model_validate(user)
            else:
                logger.info("User not found")
                return None
        finally:
            session.close()
            logger.info("Session closed after user fetch")

    def delete_user(self, user_uuid: UUID) -> None:
        logger.info(f"Deleting user {user_uuid}")
        session = self.get_session()
        try:
            user = session.query(User).filter(User.uuid == user_uuid).first()
            if not user:
                logger.info("User not found for deletion")
                raise HTTPException(status_code=404, detail="User not found")
            session.delete(user)
            session.commit()
            logger.info(f"User {user_uuid} deleted")
        finally:
            session.close()
            logger.info("Session closed after user deletion")

    def update_user(self, user_uuid: UUID, update_data: UserUpdate) -> UserResponse | None:
        logger.info(f"Updating user {user_uuid}")
        session = self.get_session()
        try:
            user = session.query(User).filter(User.uuid == user_uuid).first()
            if not user:
                logger.info("User not found for update")
                return None
            for field, value in update_data.model_dump(exclude_none=True).items():
                setattr(user, field, value)
            session.commit()
            session.refresh(user)
            logger.info(f" User {user_uuid} updated")
            return UserResponse.model_validate(user)
        finally:
            session.close()
            logger.info("Session closed after user update")
