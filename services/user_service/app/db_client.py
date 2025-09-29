import os
import json
import time
import logging
import boto3
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError
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
        self.proxy_endpoint = proxy_endpoint
        self._engine = None
        self._SessionLocal = None

        # ✅ New: Read SSL certificate path from env
        self.ssl_cert_path = os.getenv("SSL_CERT_PATH", "/var/task/global-bundle.pem")
        logger.info(f"🔐 Using SSL cert: {self.ssl_cert_path}")

    def _get_secret(self) -> dict:
        logger.info("🕵️ About to call boto3.get_secret_value()")
        start = time.time()
        client = boto3.client("secretsmanager", region_name=self.region)
        response = client.get_secret_value(SecretId=self.secret_name)
        elapsed = time.time() - start
        logger.info(f"✅ Secret fetched in {elapsed:.2f}s")
        return json.loads(response["SecretString"])

    def _build_db_url(self) -> str:
        secret = self._get_secret()
        username = secret["username"].strip()
        password = secret["password"].strip()
        dbname = secret["dbname"].strip()
        host = self.proxy_endpoint or secret["host"].strip()
        url = f"postgresql+psycopg2://{username}:{password}@{host}/{dbname}"
        logger.info(f"🔗 Built DB URL for host {host}")
        return url

    def _init_engine(self):
        if self._engine:
            return

        db_url = self._build_db_url()
        connect_args = {
            "sslmode": "verify-full",
            "sslrootcert": self.ssl_cert_path
        }

        last_err = None
        for attempt in range(3):
            try:
                logger.info(f"⚙️ Creating SQLAlchemy engine (attempt {attempt + 1})...")
                engine = create_engine(
                    db_url,
                    connect_args=connect_args,
                    pool_pre_ping=True
                )
                # ✅ Test connection
                with engine.connect() as conn:
                    logger.info("✅ Connection test succeeded.")
                self._engine = engine
                self._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                return
            except OperationalError as e:
                logger.error(f"⚠️ DB connection attempt {attempt + 1} failed: {e}")
                last_err = e
                time.sleep(2)

        logger.error("❌ All DB connection attempts failed.")
        raise last_err if last_err else RuntimeError("Unable to initialize DB engine.")

    def get_session(self) -> Session:
        self._init_engine()
        return self._SessionLocal()

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
            logger.info(f"✅ User created: {user_obj.uuid}")
            return UserResponse.model_validate(user_obj).uuid
        finally:
            session.close()

    def get_user(self, user_uuid: UUID) -> UserResponse | None:
        session = self.get_session()
        try:
            logger.info(f"🔍 Fetching user {user_uuid}")
            user = session.query(User).filter(User.uuid == user_uuid).first()
            if not user:
                logger.warning(f"⚠️ User {user_uuid} not found")
                return None
            return UserResponse.model_validate(user)
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
            logger.info(f"🗑️ Deleted user {user_uuid}")
        finally:
            session.close()

    def update_user(self, user_uuid: UUID, update_data: UserUpdate) -> UserResponse | None:
        session = self.get_session()
        try:
            user = session.query(User).filter(User.uuid == user_uuid).first()
            if not user:
                logger.warning(f"⚠️ User {user_uuid} not found for update")
                return None
            for field, value in update_data.model_dump(exclude_none=True).items():
                setattr(user, field, value)
            session.commit()
            session.refresh(user)
            logger.info(f"✅ Updated user {user_uuid}")
            return UserResponse.model_validate(user)
        finally:
            session.close()
