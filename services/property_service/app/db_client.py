import json
from uuid import UUID, uuid4

import boto3
from fastapi import HTTPException
from services.property_service.app.schemas import Property, Room, Amenity
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, PropertyDB, RoomDB, AmenityDB

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
        Base.metadata.create_all(bind=self.engine, echo=True)

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

        return (
            f"postgresql+psycopg2://{secret['username']}:{secret['password']}"
            f"@{secret['host']}:{secret['port']}/{secret['dbname']}"
        )

    def get_session(self) -> Session:
        return self.SessionLocal()
    
    def add_property(self, property: Property) -> UUID:
        session = self.get_session()

        try:
            property_obj = PropertyDB(
                user_uuid=property.user_uuid,
                name=property.name,
                description = property.description,
                country = property.country,
                state=property.state,
                city=property.city,
                county=property.county,
                address=property.address,
                latitude=property.latitude,
                longitude=property.longitude                
            )
            session.add(property_obj)
            session.commit()
            session.refresh(property_obj)

            return Property.model_validate(property_obj).uuid
        finally:
            session.close()