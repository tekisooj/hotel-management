import os
import json
import time
import logging
import socket
import ssl
import struct
from pathlib import Path
from typing import Optional

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


def log_cert(host, port):
    context = ssl.create_default_context()
    with socket.create_connection((host, port)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            cert = ssock.getpeercert()
            logger.info(f"🔐 CN: {cert.get('subject')}")
            logger.info(f"🔐 SAN: {cert.get('subjectAltName')}")

class HotelManagementDBClient:
    def __init__(self, hotel_management_database_secret_name: str | None, region: str, proxy_endpoint: str | None) -> None:
        if not hotel_management_database_secret_name:
            raise ValueError("Secret name must be provided or set in environment variables.")

        self.secret_name = hotel_management_database_secret_name
        self.region = region
        self.proxy_endpoint = proxy_endpoint

        self._engine = None
        self._SessionLocal = None
        self._certificate_logged = False
        self.ssl_cert_path = self._discover_cert_bundle()

        if self.ssl_cert_path:
            logger.info("Using RDS trust store at %s", self.ssl_cert_path)
        else:
            logger.warning(
                "No RDS trust store found; falling back to sslmode=require. "
                "Set SSL_CERT_PATH or bundle global-bundle.pem for full verification."
            )

    def _discover_cert_bundle(self) -> Optional[str]:
        bundle_names = ["us-east-1-bundle.pem", "global-bundle.pem", "rds-combined-ca-bundle.pem"]
        task_root_env = os.getenv("LAMBDA_TASK_ROOT", "")
        task_root = Path(task_root_env) if task_root_env else None
        candidates = [os.getenv("SSL_CERT_PATH")]
        for name in bundle_names:
            if task_root:
                candidates.append(str(task_root / name))
                candidates.append(str(task_root / "certs" / name))
            candidates.append(f"/app/{name}")
            candidates.append(str(Path(__file__).resolve().with_name(name)))
            candidates.append(str(Path(__file__).resolve().parent / "certs" / name))
        candidates.append(str(Path("/etc/pki/tls/certs/ca-bundle.crt")))
        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return candidate
        return None

    def _get_secret(self) -> dict:
        client = boto3.client("secretsmanager", region_name=self.region)
        secret = client.get_secret_value(SecretId=self.secret_name)
        return json.loads(secret["SecretString"])

    def _build_db_config(self) -> tuple[URL, str, int]:
        secret = self._get_secret()
        host = (self.proxy_endpoint or secret["host"]).strip()
        logger.info(f"🔍 Connecting to DB host: {host}")

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

    def _verify_proxy_certificate(self, host: str, port: int) -> None:
        if self._certificate_logged:
            return
        try:
            with socket.create_connection((host, port), timeout=5) as sock:
                ssl_request = struct.pack("!II", 8, 80877103)
                sock.sendall(ssl_request)
                response = sock.recv(1)
                if response != b"S":
                    logger.warning(
                        "RDS proxy at %s:%s did not accept SSL negotiation (response=%s)",
                        host,
                        port,
                        response,
                    )
                    return

                context = ssl.create_default_context(cafile=self.ssl_cert_path or None)
                context.check_hostname = True
                context.verify_mode = ssl.CERT_REQUIRED

                with context.wrap_socket(sock, server_hostname=host) as secure_sock:
                    cert = secure_sock.getpeercert()
                    sans = [value for key, value in cert.get("subjectAltName", []) if key == "DNS"]
                    subject = cert.get("subject", [])
                    issuer = cert.get("issuer", [])
                    logger.info(
                        "RDS proxy certificate for %s:%s subject=%s issuer=%s SANs=%s",
                        host,
                        port,
                        subject,
                        issuer,
                        sans,
                    )
                    self._certificate_logged = True
        except Exception:
            logger.exception("Unable to log certificate details for %s:%s", host, port)

    def _init_engine(self):
        if self._engine:
            return

        for attempt in range(1, 4):
            try:
                url, host, port = self._build_db_config()
                self._verify_proxy_certificate(host, port)
                logger.info("Connecting to DB (attempt %s)", attempt)

                connect_args = {
                    "sslmode": "verify-full",
                    "sslrootcert": "/var/task/global-bundle.pem",
                }

                self._engine = create_engine(
                    url,
                    connect_args=connect_args,
                    pool_pre_ping=True,
                    use_native_hstore=False,
                )
                self._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
                log_cert("hotel-management-db-proxy-int.proxy-capkwmowwxnt.us-east-1.rds.amazonaws.com", 5432)

                with self._engine.connect() as _:
                    logger.info("DB connection successful")
                return

            except Exception as e:
                logger.exception("Connection failed: %s", e)
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

