from datetime import datetime
import logging
from typing import Any
from decimal import Decimal
from uuid import UUID, uuid4

import boto3
from schemas import Amenity, Property, Room
from utils import from_dynamodb_item, to_dynamodb_item

logger = logging.getLogger()

class PropertyTableClient:
    def __init__(self, property_table_name: str | None) -> None:

        if not property_table_name:
            raise ValueError("Property table name must be provided.")

        self.property_table_name = property_table_name
        self.property_db_client = boto3.client("dynamodb")

    def add_property(self, property: Property) -> UUID:
        data = property.model_dump(mode="json")
        if not data.get("uuid"):
            data["uuid"] = uuid4()
        if not data.get("created_at"):
            data["created_at"] = datetime.now()
        data["updated_at"] = datetime.now()

        logger.info("DB CLIENT", self.property_table_name, self.property_db_client)

        self.property_db_client.put_item(
            TableName=self.property_table_name,
            Item=to_dynamodb_item(data),
        )
        return data["uuid"]
    
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


    def delete_property(self, property_uuid: UUID) -> UUID:
        _ = self.property_db_client.delete_item(
            TableName=self.property_table_name,
            Key={"uuid": {"S": str(property_uuid)}}
        )
        return property_uuid

    def get_user_properties(self, user_uuid: UUID) -> list[Property]:
        response = self.property_db_client.query(
            TableName=self.property_table_name,
            IndexName="user_uuid_index",
            KeyConditionExpression="user_uuid = :user_uuid",
            ExpressionAttributeValues={":user_uuid": {"S": user_uuid}},
        )

        items = response.get("Items", [])
        return [Property(**from_dynamodb_item(item)) for item in items]


    def get_properties_by_city_key(self, city_key: str) -> list[Property]:
        response = self.property_db_client.query(
            TableName=self.property_table_name,
            IndexName="city_index",
            KeyConditionExpression="city_key = :ck",
            ExpressionAttributeValues={":ck": {"S": city_key}},
        )
        items = response.get("Items", [])
        return [Property(**from_dynamodb_item(item)) for item in items]


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

    def get_properties_within_radius(
        self,
        latitude: Decimal,
        longitude: Decimal,
        radius_km: float,
        country: str | None = None,
        state: str | None = None,
        city: str | None = None,
    ) -> list[Property]:
        import math
        lat_f = float(latitude)
        lon_f = float(longitude)
        delta_lat = radius_km / 111.0
        delta_lon = radius_km / (111.0 * max(math.cos(math.radians(lat_f)), 1e-6))

        candidates = self.get_properties_in_bbox(
            latitude=latitude,
            longitude=longitude,
            delta=max(delta_lat, delta_lon),
            country=country,
            state=state,
            city=city,
        )

        def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
            R = 6371.0
            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)
            a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return R * c

        results: list[Property] = []
        for p in candidates:
            plat = getattr(p, 'latitude', None)
            plon = getattr(p, 'longitude', None)
            if plat is None or plon is None:
                continue
            try:
                d = haversine(lat_f, lon_f, float(plat), float(plon))
            except Exception:
                continue
            if d <= radius_km:
                results.append(p)
        return results



class RoomTableClient:
    def __init__(self, room_table_name: str | None) -> None:

        if not room_table_name:
            raise ValueError("Room table name must be provided.")

        self.room_table_name = room_table_name
        self.room_db_client = boto3.client("dynamodb")

    def add_room(self, room: Room) -> UUID:
        data = room.model_dump(mode="json")
        if not data.get("uuid"):
            data["uuid"] = uuid4()
        if not data.get("created_at"):
            data["created_at"] = datetime.now()
        
        data["updated_at"] = datetime.now()
    
        self.room_db_client.put_item(
            TableName=self.room_table_name,
            Item=to_dynamodb_item(data),
        )
        return data["uuid"]
    
    def get_room(self, room_uuid: UUID) -> Room:
        response = self.room_db_client.get_item(
            TableName=self.room_table_name,
            Key={"uuid": {"S": str(room_uuid)}},
        )
        item = response.get("Item")
        if not item:
            raise ValueError("Room not found")
        return Room(**from_dynamodb_item(item))
    
    def delete_rooom(self, room_uuid: UUID) -> UUID:
        _ = self.room_db_client.delete_item(
            TableName=self.room_table_name,
            Key={"uuid": {"S": str(room_uuid)}}
        )
        return room_uuid

    def get_property_rooms(self, property_uuid: UUID) -> list[Room]:

        response = self.room_db_client.query(
            TableName=self.room_table_name,
            IndexName="property_uuid_index",
            KeyConditionExpression="property_uuid = :p",
            ExpressionAttributeValues={":p": {"S": str(property_uuid)}},
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
            "IndexName": "property_uuid_index",
            "KeyConditionExpression": "property_uuid = :p",
            "ExpressionAttributeValues": eav,
        }
        if filters:
            params["FilterExpression"] = " AND ".join(filters)
        response = self.room_db_client.query(**params)
        items = response.get("Items", [])
        return [Room(**from_dynamodb_item(it)) for it in items]
        


        

