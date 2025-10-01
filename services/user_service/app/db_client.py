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

        # Look for the correct SSL bundle
        cert_candidates = [
            os.getenv("SSL_CERT_PATH"),
            os.path.join(os.path.dirname(__file__), "rds-combined-ca-bundle.pem"),
        ]
        self.ssl_cert_path = next((p for p in cert_candidates if p and os.path.exists(p)), None)
        if self.ssl_cert_path:
            logger.info(f"📂 Using SSL cert: {self.ssl_cert_path}")
        else:
            logger.warning("⚠️ No SSL cert found. Connection may fail.")

    def _get_secret(self) -> dict:
        client = boto3.client("secretsmanager", region_name=self.region)
        secret = client.get_secret_value(SecretId=self.secret_name)
        return json.loads(secret["SecretString"])

    def _build_db_url(self) -> URL:
        secret = self._get_secret()
        return URL.create(
            drivername="postgresql+psycopg2",
            username=secret["username"].strip(),
            password=secret["password"].strip(),
            host=(self.proxy_endpoint or secret["host"]).strip(),
            port=int(secret.get("port", 5432)),
            database=secret["dbname"].strip(),
        )

    def _init_engine(self):
        if self._engine:
            return

        for attempt in range(1, 4):
            try:
                logger.info(f"🔌 Connecting to DB (attempt {attempt})")
                connect_args = {"sslmode": "verify-full"}
                if self.ssl_cert_path:
                    connect_args["sslrootcert"] = self.ssl_cert_path

                    with open(self.ssl_cert_path, "r") as f:
                        cert_lines = f.readlines()
                        logger.info(f"🔐 First few lines of cert:\n{''.join(cert_lines[:5])}")

                self._engine = create_engine(
                    self._build_db_url(),
                    connect_args=connect_args,
                    pool_pre_ping=True,
                    use_native_hstore=False,  # must be passed as dialect kwarg
                )
                self._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)

                # Quick connection test
                with self._engine.connect() as _:
                    logger.info("✅ DB connection successful")
                return

            except Exception as e:
                logger.exception(f"❌ Connection failed: {e}")
                time.sleep(2)

        raise RuntimeError("All connection attempts failed.")

    def get_session(self) -> Session:
        self._init_engine()
        return self._SessionLocal()

    def create_user(self, user: UserCreate) -> UUID:
        session = self.get_session()
        try:
            new_user = User(
                name=user.name,
                last_name=user.last_name,
                email=user.email,
                user_type=user.user_type,
            )
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            return UserResponse.model_validate(new_user).uuid
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
