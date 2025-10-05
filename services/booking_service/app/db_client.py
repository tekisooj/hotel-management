import os
import json
from datetime import datetime
from uuid import UUID
import boto3
from sqlalchemy import and_, create_engine
from sqlalchemy.orm import sessionmaker, Session
from schemas import Booking, BookingStatus, BookingUpdateRequest
from models import BookingDB
import logging

logger = logging.getLogger()

class HotelManagementDBClient:
    def __init__(self, hotel_management_database_secret_name: str | None, region: str, proxy_endpoint: str | None) -> None:
        if not hotel_management_database_secret_name:
            raise ValueError("Secret name must be provided or set in environment variables.")
        
        logger.info("INITIALIZING")

        self.secret_name = hotel_management_database_secret_name
        self.region = region
        self._engine = None
        self._SessionLocal = None
        self.proxy_endpoint = proxy_endpoint


    def _get_secret(self) -> dict:
        client = boto3.client("secretsmanager", region_name=self.region)
        response = client.get_secret_value(SecretId=self.secret_name)
        logger.info("GETTING SECRET")
        return json.loads(response["SecretString"])

    def _build_db_url(self) -> str:
        secret = self._get_secret()
        username = secret["username"].strip()
        password = secret["password"].strip()
        port = str(secret["port"]).strip()
        dbname = secret["dbname"].strip()

        host = self.proxy_endpoint if self.proxy_endpoint else secret["host"].strip()

        logger.info("BUILDING DB URL ")
        logger.info(f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{dbname}")

        return f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{dbname}"

    def _init_engine(self):
        if not self._engine:
            self._engine = create_engine(self._build_db_url())
            self._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)

    def get_session(self) -> Session:
        self._init_engine()
        logger.info("GETTING SESSION")
        return self._SessionLocal() # type: ignore

    def add_booking(self, booking: Booking) -> UUID:
        logger.info("ADDING BOOKING")
        session = self.get_session()
        try:
            booking_obj = BookingDB(
                user_uuid=booking.user_uuid,
                room_uuid=booking.room_uuid,
                check_in=booking.check_in,
                check_out=booking.check_out,
                total_price=booking.total_price,
                status=booking.status,
            )
            session.add(booking_obj)
            session.commit()
            session.refresh(booking_obj)
            logger.info("ADDED BOOKING")
            return Booking.model_validate(booking_obj).uuid
        finally:
            session.close()

    def get_booking(self, booking_uuid: UUID) -> Booking | None:
        session = self.get_session()
        logger.info("GETTING BOOKING")
        try:
            booking = session.query(BookingDB).filter(BookingDB.uuid == booking_uuid).first()
            logger.info("GOT BOOKING")
            return Booking.model_validate(booking) if booking else None
        finally:
            session.close()

    def get_filtered_bookings(self, user_uuid: UUID | None = None,
                              room_uuid: UUID | None = None,
                              status: str | None = None,
                              check_in: datetime | None = None,
                              check_out: datetime | None = None) -> list[Booking]:
        logger.info("SESSION FILTERED BOOKING")
        session = self.get_session()
        logger.info("GETTING FILTERED BOOKING")
        try:
            query = session.query(BookingDB)
            if user_uuid:
                query = query.filter(BookingDB.user_uuid == user_uuid)
            if room_uuid:
                query = query.filter(BookingDB.room_uuid == room_uuid)
            if status:
                query = query.filter(BookingDB.status == status)
            if check_in and check_out:
                query = query.filter(
                    and_(BookingDB.check_in <= check_out, BookingDB.check_out >= check_in)
                )
            logger.info("FILTERED BOOKING")
            return [Booking.model_validate(b) for b in query.all()]
        finally:
            session.close()

    def update_booking(self, update_request: BookingUpdateRequest) -> Booking:
        session = self.get_session()
        try:
            booking = session.query(BookingDB).filter(BookingDB.uuid == update_request.booking_uuid).first()
            if not booking:
                raise ValueError("Booking not found")

            for field, value in update_request.model_dump(exclude_none=True).items():
                setattr(booking, field, value)

            session.commit()
            session.refresh(booking)
            return Booking.model_validate(booking)
        finally:
            session.close()

    def cancel_booking(self, booking_uuid: UUID) -> Booking:
        session = self.get_session()
        try:
            booking = session.query(BookingDB).filter(BookingDB.uuid == booking_uuid).first()
            if not booking:
                raise ValueError("Booking not found")

            booking.status = BookingStatus.CANCELLED  # type: ignore
            session.commit()
            session.refresh(booking)
            return Booking.model_validate(booking)
        finally:
            session.close()

    def check_availability(self, room_uuid: UUID, check_in: datetime, check_out: datetime) -> bool:
        session = self.get_session()
        try:
            overlapping = session.query(BookingDB).filter(
                BookingDB.room_uuid == room_uuid,
                BookingDB.status != "canceled",
                BookingDB.check_in < check_out,
                BookingDB.check_out > check_in,
            ).first()
            return overlapping is None
        finally:
            session.close()
    def check_availability_bulk(self, room_uuids: list[UUID], check_in: datetime, check_out: datetime) -> dict[UUID, bool]:
        if not room_uuids:
            return {}
        logger.info("GETTING BULK BOOKING")
        session = self.get_session()
        logger.info("SESSION GOT")
        try:
            overlapping = session.query(BookingDB.room_uuid).filter(
                BookingDB.room_uuid.in_(room_uuids),
                BookingDB.status != "canceled",
                BookingDB.check_in < check_out,
                BookingDB.check_out > check_in,
            ).all()
            occupied = {getattr(row, "room_uuid", row[0]) for row in overlapping}
            logger.info("BULK BOOKING")
            return {room_uuid: room_uuid not in occupied for room_uuid in room_uuids}
        finally:
            session.close()

