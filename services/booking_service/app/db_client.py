from datetime import datetime
import json
from uuid import UUID

import boto3
from schemas import Booking, BookingStatus, BookingUpdateRequest
from sqlalchemy import and_, create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, BookingDB

class HotelManagementDBClient:
    def __init__(
            self,  hotel_management_database_secret_name: str | None, region: str
    ) -> None:

        if not hotel_management_database_secret_name:
            raise ValueError("Secret name must be provided or set in environment variables.")
        
        self.db_url = self.build_db_url_from_secret(hotel_management_database_secret_name, region)
        
        if not self.db_url:
            raise ValueError("Unable to get db url.")

        
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def get_secret_by_name(self, secret_name: str, region_name: str = "us-east-1") -> dict:
        client = boto3.client("secretsmanager", region_name=region_name)
        
        try:
            response = client.get_secret_value(SecretId=secret_name)
            secret_string = response["SecretString"]
            return json.loads(secret_string)
        except client.exceptions.ResourceNotFoundException:
            raise Exception(f"Secret {secret_name} not found.")
        except client.exceptions.ClientError as e:
            raise Exception(f"Error retrieving secret: {str(e)}")

    def build_db_url_from_secret(self, secret_name: str, region: str) -> str:
        secret = self.get_secret_by_name(secret_name, region)

        username = str(secret.get('username', '')).strip()
        password = str(secret.get('password', '')).strip()
        host = str(secret.get('host', '')).strip()
        port = str(secret.get('port', '')).strip()
        dbname = str(secret.get('dbname', '')).strip()

        if not all([username, password, host, port, dbname]):
            raise ValueError('Database secret is missing required fields.')

        return (
            f"postgresql+psycopg2://{username}:{password}"
            f"@{host}:{port}/{dbname}"
        )

    def get_session(self) -> Session:
        return self.SessionLocal()
    
    def add_booking(self, booking: Booking) -> UUID:
        session = self.get_session()

        try:
            booking_obj = BookingDB(
                user_uuid=booking.user_uuid,
                room_uuid=booking.room_uuid,
                check_in = booking.check_in,
                check_out = booking.check_out,
                total_price=booking.total_price,
                status=booking.status             
            )
            session.add(booking_obj)
            session.commit()
            session.refresh(booking_obj)

            return Booking.model_validate(booking_obj).uuid
        finally:
            session.close()

    def get_booking(self, booking_uuid: UUID) -> Booking | None:
        session = self.get_session()

        try:
            booking = session.query(BookingDB).filter(BookingDB.uuid == booking_uuid).first()
            if not booking:
                return None
            return Booking.model_validate(booking)
        finally:
            session.close()

    
    def get_filtered_bookings(
        self,
        user_uuid: UUID | None = None,
        room_uuid: UUID | None = None,
        status: str | None = None,
        check_in: datetime | None = None,
        check_out: datetime | None = None
    ) -> list[Booking]:
        session = self.get_session()
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
                    and_(
                        BookingDB.check_in <= check_out,
                        BookingDB.check_out >= check_in
                    )
                )

            bookings = query.all()
            return [Booking.model_validate(b) for b in bookings]
        finally:
            session.close()
    
    def update_booking(self, update_request: BookingUpdateRequest) -> Booking:
        session = self.get_session()
        try:
            booking = session.query(BookingDB).filter(BookingDB.uuid == update_request.booking_uuid).first()
            if not booking:
                raise ValueError("Booking not found")

            if update_request.check_in:
                setattr(booking, "check_in", update_request.check_in)

            if update_request.check_out:
                setattr(booking, "check_out", update_request.check_out)

            if update_request.total_price:
                setattr(booking, "total_price", update_request.total_price)

            if update_request.status:
                setattr(booking, "status", update_request.status)

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
            
            booking.status = BookingStatus.CANCELLED # type: ignore
            session.commit()
            session.refresh(booking)
            return Booking.model_validate(booking)
        finally:
            session.close()

    def check_availability(self, room_uuid: UUID, check_in: datetime, check_out: datetime) -> bool:
        session = self.get_session()
        try:
            overlapping_booking_exists = session.query(BookingDB).filter(
                BookingDB.room_uuid == room_uuid,
                BookingDB.status != "canceled",
                BookingDB.check_in < check_out,
                BookingDB.check_out > check_in
            ).first()

            return overlapping_booking_exists is None
        finally:
            session.close()




