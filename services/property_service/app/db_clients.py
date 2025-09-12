from datetime import datetime
from typing import Any
from decimal import Decimal
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
            TableName=self.property_table_name,
            Key={"uuid": {"S": str(property_uuid)}},
        )
        item = response.get("Item")
        if not item:
            raise ValueError("Property not found")
        data = from_dynamodb_item(item)
        return Property(**{k: v for k, v in data.items() if k in Property.model_fields})

    def get_properties_by_city_key(self, city_key: str) -> list[Property]:
        response = self.property_db_client.query(
            TableName=self.property_table_name,
            IndexName="city_index",
            KeyConditionExpression="city_key = :ck",
            ExpressionAttributeValues={":ck": {"S": city_key}},
        )
        items = response.get("Items", [])
        out: list[Property] = []
        for it in items:
            data = from_dynamodb_item(it)
            out.append(Property(**{k: v for k, v in data.items() if k in Property.model_fields}))
        return out

    def get_properties_in_bbox(
        self,
        latitude: Decimal,
        longitude: Decimal,
        delta: float,
        country: str | None = None,
        state: str | None = None,
        city: str | None = None,
    ) -> list[Property]:
        min_lat = Decimal(str(float(latitude) - float(delta)))
        max_lat = Decimal(str(float(latitude) + float(delta)))
        min_lon = Decimal(str(float(longitude) - float(delta)))
        max_lon = Decimal(str(float(longitude) + float(delta)))

        filter_expr_parts: list[str] = [
            "latitude BETWEEN :minlat AND :maxlat",
            "longitude BETWEEN :minlon AND :maxlon",
        ]
        eav: dict[str, Any] = {
            ":minlat": {"N": str(min_lat)},
            ":maxlat": {"N": str(max_lat)},
            ":minlon": {"N": str(min_lon)},
            ":maxlon": {"N": str(max_lon)},
        }
        if country:
            filter_expr_parts.append("country = :country")
            eav[":country"] = {"S": country}
        if state:
            filter_expr_parts.append("state = :state")
            eav[":state"] = {"S": state}
        if city:
            filter_expr_parts.append("city = :city")
            eav[":city"] = {"S": city}

        params: dict[str, Any] = {
            "TableName": self.property_table_name,
            "FilterExpression": " AND ".join(filter_expr_parts),
            "ExpressionAttributeValues": eav,
        }

        results: list[Property] = []
        while True:
            resp = self.property_db_client.scan(**params)
            items = resp.get("Items", [])
            for it in items:
                data = from_dynamodb_item(it)
                results.append(Property(**{k: v for k, v in data.items() if k in Property.model_fields}))
            lek = resp.get("LastEvaluatedKey")
            if not lek:
                break
            params["ExclusiveStartKey"] = lek

        return results



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
        response = self.room_db_client.query(
            TableName=self.room_table_name,
            IndexName="room_uuid_index",
            KeyConditionExpression="uuid = :u",
            ExpressionAttributeValues={":u": {"S": str(room_uuid)}},
        )
        items = response.get("Items", [])
        if not items:
            raise ValueError("Room not found")
        return Room(**from_dynamodb_item(items[0]))
    
    def get_property_rooms(self, property_uuid: UUID) -> list[Room]:

        response = self.room_db_client.query(
            TableName=self.room_table_name,
            KeyConditionExpression="property_uuid=:property_uuid",
            ExpressionAttributeValues={":property_uuid": {"S": str(property_uuid)}}
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

    def get_filtered_property_rooms(
        self,
        property_uuid: UUID,
        capacity: int | None = None,
        max_price_per_night: float | None = None,
        amenities: list[Amenity] | None = None,
    ) -> list[Room]:
        eav: dict[str, Any] = {":p": {"S": str(property_uuid)}}
        filters: list[str] = []
        if capacity is not None:
            filters.append("capacity >= :cap")
            eav[":cap"] = {"N": str(capacity)}
        if max_price_per_night is not None:
            filters.append("price_per_night <= :maxp")
            eav[":maxp"] = {"N": str(max_price_per_night)}
        if amenities:
            for i, a in enumerate(amenities):
                key = f":a{i}"
                filters.append(f"contains(amenities, {key})")
                eav[key] = {"S": str(a)}

        params: dict[str, Any] = {
            "TableName": self.room_table_name,
            "KeyConditionExpression": "property_uuid = :p",
            "ExpressionAttributeValues": eav,
        }
        if filters:
            params["FilterExpression"] = " AND ".join(filters)
        response = self.room_db_client.query(**params)
        items = response.get("Items", [])
        return [Room(**from_dynamodb_item(it)) for it in items]
        


        

