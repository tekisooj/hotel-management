from uuid import uuid4
from sqlalchemy import Column, Numeric, UUID, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy import Enum as SqlEnum
from services.booking_service.app.schemas import BookingStatus

Base = declarative_base()


class BookingDB(Base):
    __tablename__ = "bookings"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_uuid = Column(UUID(as_uuid=True), nullable=False)
    room_uuid = Column(UUID(as_uuid=True), nullable=False)
    check_in = Column(DateTime)
    check_out = Column(DateTime)
    total_price = Column(Numeric)
    status = Column(SqlEnum(BookingStatus), default=BookingStatus.PENDING)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
