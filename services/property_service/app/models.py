from uuid import uuid4
from sqlalchemy import Column, ForeignKey, Integer, Numeric, String, UUID, Table, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from sqlalchemy import Enum as SqlEnum
from services.property_service.app.schemas import RoomType

Base = declarative_base()


class PropertyDB(Base):
    __tablename__ = "property"
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    user_uuid = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    country = Column(String, nullable=False)
    state = Column(String)
    city = Column(String, nullable=False)
    county = Column(String)
    address = Column(String, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    rooms = relationship("Room", back_populates="property")


room_amenities_table = Table(
    "room_amenities",
    Base.metadata,
    Column("room_uuid", UUID(as_uuid=True), ForeignKey("rooms.uuid"), primary_key=True, index=True),
    Column("amenity_uuid", UUID(as_uuid=True), ForeignKey("amenities.uuid"), primary_key=True)
)


class AmenityDB(Base):
    __tablename__ = "amenity"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, unique=True, nullable=False)

    rooms = relationship("Room", secondary=room_amenities_table, back_populates="amenities")

class RoomDB(Base):
    __tablename__ = "room"

    uuid = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    property_uuid = Column(UUID(as_uuid=True), ForeignKey("property.uuid"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    capacity = Column(Integer)
    room_type = Column(SqlEnum(RoomType), nullable=False)
    price_per_night = Column(Float)
    min_price_per_night = Column(Float)
    max_price_per_night = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    property = relationship("Property", back_populates="rooms")
    amenities = relationship("Amenity", secondary=room_amenities_table, back_populates="rooms")

