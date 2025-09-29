import os
import json
import time
import logging
import boto3
from uuid import UUID
from urllib.parse import quote_plus

from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from schemas import UserCreate, UserResponse, UserUpdate
from models import User

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class HotelManagementDBClient:
    """
    Connects to Postgres through RDS Proxy with enforced TLS.

    Key points:
    - Pulls DB creds from Secrets Manager.
    - Uses the RDS global CA bundle to validate TLS.
    - sslmode defaults to 'verify-full' (best practice). Falls back to 'verify-ca' if needed.
    - Uses pool_pre_ping + small pool to be Lambda-friendly.
    """

    def __init__(
        self,
        hotel_management_database_secret_name: str | None,
        region: str,
        proxy_endpoint: str | None,
    ) -> None:
        if not hotel_management_database_secret_name:
            raise ValueError("Secret name must be provided or set in environment variables.")
        if not region:
            raise ValueError("AWS region must be provided.")
        if not proxy_endpoint:
            raise ValueError("DB proxy endpoint must be provided.")

        self.secret_name = hotel_management_database_secret_name
        self.region = region
        self.proxy_endpoint = proxy_endpoint.strip()

        self._engine = None
        self._SessionLocal = None

        # Optional override via env. Defaults are safe.
        self._sslmode_env = os.getenv("RDS_SSLMODE", "verify-full").strip()
        self._connect_timeout = int(os.getenv("DB_CONNECT_TIMEOUT", "10"))
        self._pool_recycle = int(os.getenv("DB_POOL_RECYCLE_SECONDS", "300"))

        # Locate CA bundle shipped with the Lambda package.
        self._ca_bundle_path = os.getenv(
            "RDS_CA_PATH",
            os.path.join(os.path.dirname(__file__), "global-bundle.pem"),
        )

    # --------------------------
    # Internal helpers
    # --------------------------

    def _get_secret(self) -> dict:
        logger.info("🕵️ Fetching DB secret from Secrets Manager...")
        start = time.time()
        client = boto3.client("secretsmanager", region_name=self.region)
        response = client.get_secret_value(SecretId=self.secret_name)
        elapsed = time.time() - start
        logger.info(f"✅ Secret fetched in {elapsed:.2f}s")
        return json.loads(response["SecretString"])

    def _build_db_url(self) -> str:
        """
        Build a clean SQLAlchemy URL without query string ssl params
        (we pass SSL params via connect_args to psycopg2).
        """
        secret = self._get_secret()

        username = quote_plus(secret["username"].strip())
        password = quote_plus(secret["password"].strip())
        dbname = secret["dbname"].strip()
        port = str(secret.get("port", 5432)).strip()

        host = self.proxy_endpoint  # always prefer the proxy endpoint
        url = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{dbname}"

        logger.info(f"🔗 Built DB URL host={host} port={port} db={dbname}")
        return url

    def _create_engine_with_ssl(self, sslmode: str):
        """
        Create an engine using the given sslmode and our CA bundle.
        """
        logger.info(f"🔐 Creating engine with sslmode={sslmode} ca={self._ca_bundle_path}")
        engine = create_engine(
            self._build_db_url(),
            pool_pre_ping=True,
            pool_recycle=self._pool_recycle,
            pool_size=2,          # tiny pool for Lambda
            max_overflow=0,       # avoid growing pools across invocations
            connect_args={
                "sslmode": sslmode,                     # verify-full (preferred) or verify-ca
                "sslrootcert": self._ca_bundle_path,    # Amazon RDS CA bundle
                "connect_timeout": self._connect_timeout,
                "application_name": "user-service-lambda",
            },
        )
        return engine

    def _init_engine(self):
        """
        Initialize the SQLAlchemy engine once per Lambda runtime.
        Try verify-full first; if we hit hostname/verify issues, fall back to verify-ca.
        """
        if self._engine:
            return

        start = time.time()
        sslmode_try_order = [self._sslmode_env]
        if self._sslmode_env != "verify-full":
            # still try verify-full first if the env was changed
            sslmode_try_order.insert(0, "verify-full")
        if "verify-ca" not in sslmode_try_order:
            sslmode_try_order.append("verify-ca")

        last_err = None
        for mode in sslmode_try_order:
            try:
                eng = self._create_engine_with_ssl(mode)
                # Do a quick sanity check connection
                with eng.connect() as conn:
                    conn.execute(text("SELECT 1"))
                self._engine = eng
                self._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
                logger.info(f"✅ Engine created with sslmode={mode} in {time.time() - start:.2f}s")
                return
            except Exception as e:
                last_err = e
                msg = str(e)
                logger.warning(f"⚠️ Engine test failed with sslmode={mode}: {msg}")

        logger.exception("❌ Failed to create a working SQLAlchemy engine with any sslmode.")
        # Re-raise the last error for visibility
        raise last_err if last_err else RuntimeError("Unable to initialize DB engine.")

    def get_session(self) -> Session:
        self._init_engine()
        t0 = time.time()
        try:
            session = self._SessionLocal()
            logger.info(f"✅ DB session opened in {time.time() - t0:.2f}s")
            return session
        except Exception:
            logger.exception("❌ Failed to open DB session")
            raise

    # --------------------------
    # Public methods
    # --------------------------

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
        t0 = time.time()
        logger.info(f"🔍 Fetching user {user_uuid}")
        session = self.get_session()
        try:
            user = session.query(User).filter(User.uuid == user_uuid).first()
            elapsed = time.time() - t0
            if user:
                # Optional: confirm SSL is indeed enabled
                try:
                    ssl_state = session.execute(text("SHOW ssl;")).scalar()
                    logger.info(f"🔒 SSL Enabled: {ssl_state}")
                except Exception:
                    logger.debug("ℹ️ Could not query SHOW ssl (not critical).")
                logger.info(f"✅ User found ({user.email}) in {elapsed:.2f}s")
                return UserResponse.model_validate(user)
            logger.info(f"⚠️ User {user_uuid} not found after {elapsed:.2f}s")
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
