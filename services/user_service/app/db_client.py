import os
import json
import time
import logging
import socket
import ssl
from pathlib import Path
from typing import Optional
from uuid import UUID

import boto3
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
        self.ssl_cert_path = self._discover_cert_bundle()

        if not self.ssl_cert_path:
            logger.error("❌ Missing RDS SSL cert bundle (e.g., global-bundle.pem)")
            raise RuntimeError("RDS cert bundle not found. Set SSL_CERT_PATH or include it in your Lambda package.")
        else:
            logger.info(f"✅ Using RDS trust store at: {self.ssl_cert_path}")

    def _discover_cert_bundle(self) -> Optional[str]:
        candidates = [
            os.getenv("SSL_CERT_PATH"),
            "/var/task/global-bundle.pem",  # default path inside Lambda
            str(Path(__file__).resolve().with_name("global-bundle.pem")),
            "/etc/pki/tls/certs/ca-bundle.crt",  # fallback Linux path
        ]
        for path in candidates:
            if path and os.path.exists(path):
                return path
        return None

    def _get_secret(self) -> dict:
        client = boto3.client("secretsmanager", region_name=self.region)
        response = client.get_secret_value(SecretId=self.secret_name)
        return json.loads(response["SecretString"])

    def _verify_proxy_certificate(self, host: str, port: int) -> None:
        try:
            context = ssl.create_default_context(cafile=self.ssl_cert_path)
            with socket.create_connection((host, port), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
                    logger.info(f"🔐 Verified RDS proxy cert for {host}, issuer: {cert.get('issuer')}")
        except Exception as e:
            logger.exception(f"❌ Failed to verify SSL certificate for {host}:{port}")
            raise

    def _build_db_config(self) -> tuple[URL, str, int]:
        secret = self._get_secret()
        host = (self.proxy_endpoint or secret["host"]).strip()
        port = int(secret.get("port", 5432))
        url = URL.create(
            drivername="postgresql+psycopg2",
            username=secret["username"].strip(),
            password=secret["password"].strip(),
            host=host,
            port=port,
            database=secret["dbname"].strip(),
        )
        return url, host, port

    def _init_engine(self):
        if self._engine:
            return

        for attempt in range(1, 4):
            try:
                url, host, port = self._build_db_config()
                logger.info(f"🔄 Attempting DB connection to {host}:{port} (attempt {attempt})")

                # 🔐 Validate cert chain before connecting
                # self._verify_proxy_certificate(host, port)

                connect_args = {
                    "sslmode": "require",
                    "sslrootcert": self.ssl_cert_path,
                }

                self._engine = create_engine(
                    url,
                    connect_args=connect_args,
                    pool_pre_ping=True,
                )
                self._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)

                with self._engine.connect() as _:
                    logger.info("✅ DB connection established.")
                return

            except Exception as e:
                logger.exception(f"❌ DB connection failed on attempt {attempt}")
                time.sleep(2)

        raise RuntimeError("❌ All attempts to connect to the DB failed.")

    def get_session(self) -> Session:
        self._init_engine()
        return self._SessionLocal()

    def create_user(self, user: UserCreate) -> UUID:
        with self.get_session() as session:
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

    def get_user(self, user_uuid: UUID) -> UserResponse | None:
        with self.get_session() as session:
            user = session.query(User).filter(User.uuid == user_uuid).first()
            return UserResponse.model_validate(user) if user else None

    def delete_user(self, user_uuid: UUID) -> None:
        with self.get_session() as session:
            user = session.query(User).filter(User.uuid == user_uuid).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            session.delete(user)
            session.commit()

    def update_user(self, user_uuid: UUID, update_data: UserUpdate) -> UserResponse | None:
        with self.get_session() as session:
            user = session.query(User).filter(User.uuid == user_uuid).first()
            if not user:
                return None
            for field, value in update_data.model_dump(exclude_none=True).items():
                setattr(user, field, value)
            session.commit()
            session.refresh(user)
            return UserResponse.model_validate(user)
