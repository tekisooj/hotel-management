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
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import OperationalError, DisconnectionError

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

        # ✅ Path to SSL certificate
        self.ssl_cert_path = os.getenv(
            "SSL_CERT_PATH",
            os.path.join(os.path.dirname(__file__), "AmazonRootCA1.pem")
        )

        logger.info(f"📂 SSL cert path: {self.ssl_cert_path}")
        logger.info(f"📄 PEM file exists: {os.path.exists(self.ssl_cert_path)}")

        if not os.path.exists(self.ssl_cert_path):
            logger.warning("⚠️ SSL certificate not found — secure connection may fail.")

    # ✅ Fetch DB credentials
    def _get_secret(self) -> dict:
        logger.info("🕵️ Fetching DB credentials from Secrets Manager...")
        start = time.time()
        client = boto3.client("secretsmanager", region_name=self.region)
        response = client.get_secret_value(SecretId=self.secret_name)
        elapsed = time.time() - start
        logger.info(f"✅ Secret fetched in {elapsed:.2f}s")
        return json.loads(response["SecretString"])

    # ✅ Build PostgreSQL URL
    def _build_db_url(self) -> str:
        secret = self._get_secret()
        username = secret["username"].strip()
        password = secret["password"].strip()
        dbname = secret["dbname"].strip()
        # Ensure host uses the Proxy endpoint if provided
        host = self.proxy_endpoint if self.proxy_endpoint else secret["host"].strip()

        url = f"postgresql+psycopg2://{username}:{password}@{host}/{dbname}"
        logger.info(f"🔗 Built DB URL for host {host}")
        return url

    # ✅ Create SQLAlchemy engine (without connection test and retry)
    def _init_engine(self):
        if self._engine:
            return

        # 🔑 No retry loop here. It belongs in the calling functions or get_session().
        
        logger.info(f"⚙️ Creating SQLAlchemy engine with NullPool...")

        try:
            connect_args = {
                "sslmode": "verify-full", 
                "sslrootcert": self.ssl_cert_path
            }

            self._engine = create_engine(
                self._build_db_url(),
                poolclass=NullPool,         # 🔑 FIX: Disables SQLAlchemy-side pooling
                pre_ping=True,              # 🔑 Ensures connection is tested right before use
                connect_args=connect_args
            )

            # 🛑 REMOVED: Immediate connection test (with engine.connect() as conn: conn.execute("SELECT 1"))
            # This is where the stale connection issue often originates.
            
            self._SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self._engine
            )
            logger.info("✅ Database engine initialized with NullPool.")
            return

        except Exception as e:
            logger.exception(f"❌ DB connection initialization failed.")
            # Re-raise the error to halt the cold start initialization
            raise

    # ✅ Session manager with retry logic for transient connection errors
    def get_session(self) -> Session:
        self._init_engine()
        start = time.time()
        
        # 🔑 Resilience for connection failures (OperationalError/DisconnectionError)
        MAX_RETRIES = 2
        for attempt in range(MAX_RETRIES):
            try:
                session = self._SessionLocal()
                logger.info(f"✅ DB session opened in {time.time() - start:.2f}s")
                return session
            
            # Catch the common database operational errors
            except (OperationalError, DisconnectionError) as e:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"⚠️ DB connection error on session open (attempt {attempt+1}). Disposing engine and retrying.")
                    
                    # 🔑 CRITICAL: Dispose the engine to force a brand new connection attempt
                    self._engine.dispose() 
                    time.sleep(0.5)
                else:
                    logger.exception("❌ Failed to open DB session after all retries.")
                    raise e
            except Exception:
                logger.exception("❌ Failed to open DB session")
                raise

    # ✅ Create user
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

    # ✅ Get user
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

    # ✅ Delete user
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

    # ✅ Update user
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