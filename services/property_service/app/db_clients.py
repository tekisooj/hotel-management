from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import boto3
from services.property_service.app.schemas import Amenity, Property, Room
from services.property_service.app.utils import from_dynamodb_item, to_dynamodb_item


class PropertyTableClient:
    def __init__(self, property_table_name: str | None) -> None:

        if not property_table_name:
            raise ValueError("Property table name must be provided.")

        self.property_table_name = property_table_name
        self.property_db_client = boto3.client("dynamodb")

    def add_property(self, property: Property) -> UUID:
        data = property.model_dump()
        if not data.get("uuid"):
            data["uuid"] = uuid4()
        if not data.get("created_at"):
            data["created_at"] = datetime.now()
        if not data.get("updated_at"):
            data["updated_at"] = datetime.now()

        self.property_db_client.put_item(
            TableName=self.property_table_name,
            Item=to_dynamodb_item(data),
        )
        return UUID(str(data["uuid"]))
    
    def get_property(self, property_uuid: UUID) -> Property:
        response = self.property_db_client.get_item(
            TableName = self.property_table_name,
            Key={"uuid": {"S": str(property_uuid)}}

        )
        return Property(**from_dynamodb_item(response))



class RoomTableClient:
    def __init__(self, room_table_name: str | None) -> None:

        if not room_table_name:
            raise ValueError("Room table name must be provided.")

        self.room_table_name = room_table_name
        self.room_db_client = boto3.client("dynamodb")

    def add_room(self, room: Room) -> UUID:
        data = room.model_dump()
        if not data.get("uuid"):
            data["uuid"] = uuid4()
        if not data.get("created_at"):
            data["created_at"] = datetime.now()
        if not data.get("updated_at"):
            data["updated_at"] = datetime.now()

        self.room_db_client.put_item(
            TableName=self.room_table_name,
            Item=to_dynamodb_item(data),
        )
        return UUID(str(data["uuid"]))
    
    def get_room(self, room_uuid: UUID) -> Room:
        response = self.room_db_client.get_item(
            TableName = self.room_table_name,
            IndexName = "room_uuid_index",
            Key={"uuid": {"S": str(room_uuid)}}

        )
        return Room(**from_dynamodb_item(response))
    
    def get_property_rooms(self, property_uuid: UUID) -> list[Room]:

        response = self.room_db_client.query(
            TableName=self.room_table_name,
            KeyConditionExpression="property_uuid=:property_uuid",
            ExpressionAttributeValues={":proeprty_uuid": {"S": str(property_uuid)}}
        )
        
        items = response.get("Items", [])

        return [Room(**from_dynamodb_item(item)) for item in items]

    
    def get_filtered_rooms(
            self,
            capacity: int | None = None, 
            max_price_per_night: float | None = None, 
            amenities: list[Amenity] | None = None
        ) -> list[Room]:

        filters = []
        attribute_values = {}
        if capacity is not None:
            filters.append("capacity >= :cap")
            attribute_values[":cap"] = {"N": str(capacity)}
        
        if max_price_per_night is not None:
            filters.append("price_per_night <= :maxp")
            attribute_values[":maxp"] = {"N": str(max_price_per_night)}

        if amenities:
            for i, amenity in enumerate(amenities):
                key = f":a{i}"
                filters.append(f"contains(amenities, {key})")
                attribute_values[key] = {"S": str(amenity)}

        params = {
            "TableName": self.room_table_name,
        }
        if filters:
            params["FilterExpression"] = " AND ".join(filters)
            params["ExpressionAttributeValues"] = attribute_values # type: ignore

        response = self.room_db_client.scan(**params)

        items = response.get("Items", [])

        return [Room(**from_dynamodb_item(item)) for item in items]
        


        

