import os
import json
import time
import logging
import hashlib
import ssl as pyssl
import boto3
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import create_engine, text
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

        # --- TLS / SSL settings ---
        # default to verify-full; can temporarily set to 'require' to isolate trust issues
        self.sslmode = os.getenv("SSLMODE", "verify-full").strip()
        # expect bundle to be baked into /var/task (Lambda code root)
        self.ssl_cert_path = os.getenv(
            "SSL_CERT_PATH",
            os.path.join(os.path.dirname(__file__), "rds-combined-ca-bundle.pem"),
        )

        logger.info(f"🔐 SSLMODE env: {self.sslmode}")
        logger.info(f"📦 Python OpenSSL: {pyssl.OPENSSL_VERSION}")
        logger.info(f"📂 SSL_CERT_PATH env: {self.ssl_cert_path}")

        exists = os.path.exists(self.ssl_cert_path)
        logger.info(f"📄 Exists(local_bundle): {exists} at {self.ssl_cert_path}")
        if exists:
            try:
                with open(self.ssl_cert_path, "rb") as f:
                    pem_bytes = f.read()
                sha256 = hashlib.sha256(pem_bytes).hexdigest()
                logger.info(f"🔎 PEM sha256: {sha256}")
                # quick sanity: file is non-trivial in size
                logger.info(f"📏 PEM size: {len(pem_bytes)} bytes")
            except Exception:
                logger.exception("⚠️ Could not read PEM file")

    # ---- Secrets ----
    def _get_secret(self) -> dict:
        logger.info("🕵️ Fetching DB credentials from Secrets Manager...")
        start = time.time()
        client = boto3.client("secretsmanager", region_name=self.region)
        response = client.get_secret_value(SecretId=self.secret_name)
        logger.info(f"✅ Secret fetched in {time.time() - start:.2f}s")
        return json.loads(response["SecretString"])

    # ---- URL builder (disable hstore OID lookup) ----
    def _build_db_url(self) -> str:
        secret = self._get_secret()
        username = secret["username"].strip()
        password = secret["password"].strip()
        dbname = secret["dbname"].strip()
        host = (self.proxy_endpoint or secret["host"]).strip()

        # IMPORTANT: disable psycopg2 native hstore OID probe (causes an extra query on connect)
        # also keep URL free of ssl params; we pass those via connect_args
        url = f"postgresql+psycopg2://{username}:{password}@{host}/{dbname}?use_native_hstore=0"
        logger.info(f"🔗 Built DB URL (host): {host}")
        return url

    # ---- Engine init with retry & SELECT 1 ----
    def _init_engine(self):
        if self._engine:
            return

        retries = 3
        delay = 2.0
        last_err = None

        for attempt in range(1, retries + 1):
            logger.info(f"⚙️ Creating SQLAlchemy engine (attempt {attempt})...")

            try:
                connect_args = {
                    # TLS controls go here (not in the URL)
                    "sslmode": self.sslmode,                # 'verify-full' or 'require' (for testing)
                    "sslrootcert": self.ssl_cert_path,      # path we packaged with the Lambda
                    # TCP keepalives (helps with proxies/NAT)
                    "keepalives": 1,
                    "keepalives_idle": 30,
                    "keepalives_interval": 10,
                    "keepalives_count": 5,
                }

                engine = create_engine(
                    self._build_db_url(),
                    pool_pre_ping=True,
                    pool_size=1,
                    max_overflow=2,
                    pool_recycle=300,
                    connect_args=connect_args,
                )

                # Establish connection AND run a minimal query
                with engine.connect() as conn:
                    logger.info("🔌 Connected. Running sanity query...")
                    conn.execute(text("SELECT 1"))
                    logger.info("✅ Database connection test succeeded (SELECT 1).")

                # If we got here, keep the engine
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

    # ---- CRUD ----
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
