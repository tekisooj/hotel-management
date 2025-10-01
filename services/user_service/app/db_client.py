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

        env_path = os.getenv("SSL_CERT_PATH")
        local_dir = os.path.dirname(__file__)
        default_root = os.path.join(local_dir, "AmazonRootCA1.pem")
        rds_bundle = os.path.join(local_dir, "rds-combined-ca-bundle.pem")

        candidate_paths = [p for p in [env_path, default_root, rds_bundle] if p]
        chosen = None
        for p in candidate_paths:
            if os.path.exists(p):
                chosen = p
                break

        self.ssl_cert_path = chosen
        logger.info(f"📂 SSL_CERT_PATH env: {env_path!r}")
        logger.info(f"📄 AmazonRootCA1.pem exists: {os.path.exists(default_root)} at {default_root}")
        logger.info(f"📄 rds-combined-ca-bundle.pem exists: {os.path.exists(rds_bundle)} at {rds_bundle}")
        logger.info(f"🔐 Using CA file: {self.ssl_cert_path}")

        if not self.ssl_cert_path:
            logger.warning("⚠️ No CA file found. TLS verification will fail with RDS Proxy.")

    def _get_secret(self) -> dict:
        logger.info("🕵️ Fetching DB credentials from Secrets Manager...")
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
        host = (self.proxy_endpoint or secret["host"]).strip()

        url = f"postgresql+psycopg2://{username}:{password}@{host}/{dbname}"
        logger.info(f"🔗 Built DB URL for host {host}")
        return url

    def _init_engine(self):
        if self._engine:
            return

        retries = 3
        delay = 2
        last_err = None

        for attempt in range(1, retries + 1):
            logger.info(f"⚙️ Creating SQLAlchemy engine (attempt {attempt})...")

            try:
                connect_args = {}
                if self.ssl_cert_path:
                    # With RDS Proxy, verify-ca is the most robust choice
                    connect_args = {
                        "sslmode": "verify-ca",
                        "sslrootcert": self.ssl_cert_path,
                    }
                else:
                    # This will almost certainly fail with RDS Proxy,
                    # but we log loudly above if no CA file is present.
                    connect_args = {"sslmode": "require"}

                engine = create_engine(
                    self._build_db_url(),
                    pool_pre_ping=True,
                    connect_args=connect_args,
                )

                # Smoke test: open a connection once
                with engine.connect() as _conn:
                    logger.info("✅ Database connection test succeeded.")

                self._engine = engine
                self._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
                return

            except Exception as e:
                last_err = e
                logger.exception(f"⚠️ DB connection attempt {attempt} failed: {e}")
                time.sleep(delay)

        logger.error("❌ All DB connection attempts failed.")
        raise last_err if last_err else RuntimeError("Unable to initialize DB engine.")

    def get_session(self) -> Session:
        self._init_engine()
        start = time.time()
        try:
            session = self._SessionLocal()
            logger.info(f"✅ DB session opened in {time.time() - start:.2f}s")
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
        logger.info(f"🏁 Entering HotelManagementDBClient.get_user() for {user_uuid}")
        session = self.get_session()
        try:
            user = session.query(User).filter(User.uuid == user_uuid).first()
            if user:
                logger.info(f"✅ User found ({user.email})")
                return UserResponse.model_validate(user)
            logger.warning(f"⚠️ User {user_uuid} not found.")
            return None
        finally:
            session.close()
            logger.info("🔒 Session closed after get_user")

    def delete_user(self, user_uuid: UUID) -> None:
        logger.info(f"🗑️ Deleting user {user_uuid}")
        session = self.get_session()
        try:
            user = session.query(User).filter(User.uuid == user_uuid).first()
            if not user:
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
