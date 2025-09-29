import os
import json
import time
import logging
import boto3
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
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
        self.proxy_endpoint = proxy_endpoint
        self._engine = None
        self._SessionLocal = None
        self._ssl_args = {}

    def _get_secret(self) -> dict:
        logger.info("🕵️ About to call boto3.get_secret_value()")
        start = time.time()
        client = boto3.client("secretsmanager", region_name=self.region)
        logger.info(f"🔐 Fetching secret {self.secret_name} from Secrets Manager...")
        response = client.get_secret_value(SecretId=self.secret_name)
        elapsed = time.time() - start
        logger.info(f"✅ Secret fetched in {elapsed:.2f}s")
        return json.loads(response["SecretString"])

    def _build_db_url(self) -> URL:
        secret = self._get_secret()
        username = secret["username"].strip()
        password = secret["password"].strip()
        dbname = secret["dbname"].strip()
        host = self.proxy_endpoint or secret["host"].strip()
        port = secret.get("port", 5432)

        # ✅ Path to AWS global RDS CA bundle
        rds_cert_path = os.path.join(os.path.dirname(__file__), "global-bundle.pem")

        if not os.path.exists(rds_cert_path):
            raise FileNotFoundError(f"❌ RDS cert not found at: {rds_cert_path}")

        logger.info(f"🔗 Using DB Host: {host}:{port}")
        logger.info(f"🔐 Using SSL cert: {rds_cert_path}")

        # ✅ SSL verification args
        self._ssl_args = {
            "sslmode": "verify-full",
            "sslrootcert": rds_cert_path,
        }

        return URL.create(
            "postgresql+psycopg2",
            username=username,
            password=password,
            host=host,
            port=port,
            database=dbname,
        )

    def _init_engine(self):
        if not self._engine:
            start = time.time()
            logger.info("⚙️ Creating SQLAlchemy engine with SSL...")
            try:
                url = self._build_db_url()
                self._engine = create_engine(
                    url,
                    connect_args=self._ssl_args,
                    pool_pre_ping=True,
                )
                self._SessionLocal = sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=self._engine,
                )
                logger.info(f"✅ Engine created in {time.time() - start:.2f}s")
            except Exception:
                logger.exception("❌ Failed to create SQLAlchemy engine")
                raise

    def get_session(self) -> Session:
        self._init_engine()
        try:
            session = self._SessionLocal()
            logger.info("✅ DB session opened")
            return session
        except Exception:
            logger.exception("❌ Failed to open DB session")
            raise

    def create_user(self, user: UserCreate) -> UUID:
        logger.info("🧩 Creating user...")
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
            logger.info(f"✅ User created UUID={user_obj.uuid}")
            return UserResponse.model_validate(user_obj).uuid
        finally:
            session.close()
            logger.info("🔒 Session closed after create_user")

    def get_user(self, user_uuid: UUID) -> UserResponse | None:
        start = time.time()
        logger.info(f"🔍 Fetching user {user_uuid}")
        session = self.get_session()
        try:
            user = session.query(User).filter(User.uuid == user_uuid).first()
            elapsed = time.time() - start
            if user:
                logger.info(f"✅ User found ({user.email}) in {elapsed:.2f}s")
                return UserResponse.model_validate(user)
            logger.info(f"⚠️ User {user_uuid} not found after {elapsed:.2f}s")
            return None
        except Exception:
            logger.exception(f"❌ Error fetching user {user_uuid}")
            raise
        finally:
            session.close()
            logger.info("🔒 Session closed after get_user")

    def delete_user(self, user_uuid: UUID) -> None:
        logger.info(f"🗑️ Deleting user {user_uuid}")
        session = self.get_session()
        try:
            user = session.query(User).filter(User.uuid == user_uuid).first()
            if not user:
                logger.warning(f"⚠️ User {user_uuid} not found for deletion")
                raise HTTPException(status_code=404, detail="User not found")
            session.delete(user)
            session.commit()
            logger.info(f"✅ User {user_uuid} deleted")
        finally:
            session.close()
            logger.info("🔒 Session closed after delete_user")

    def update_user(self, user_uuid: UUID, update_data: UserUpdate) -> UserResponse | None:
        logger.info(f"✏️ Updating user {user_uuid}")
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
            logger.info(f"✅ User {user_uuid} updated")
            return UserResponse.model_validate(user)
        finally:
            session.close()
            logger.info("🔒 Session closed after update_user")
