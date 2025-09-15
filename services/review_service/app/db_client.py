from datetime import datetime
import json
from uuid import UUID, uuid4

import boto3
from fastapi import HTTPException

from schemas import Review
from utils import from_dynamodb_item, to_dynamodb_item


class ReviewDBClient:
    def __init__(
            self,  review_table_name: str | None
    ) -> None:

        if not review_table_name:
            raise ValueError("Review table name must be provided.")
        
        self.review_table_name = review_table_name
        self.review_table_client = boto3.client("dynamodb")

    
    def add_review(self, review: Review) -> UUID:
        review_dict = review.model_dump(exclude_none=True)
        review_uuid = uuid4()
        review_dict["uuid"] = review_uuid
        if not review_dict["timestamp"]:
            review_dict["timestamp"] = datetime.now()
        self.review_table_client.put_item(
            TableName=self.review_table_name,
            Item=to_dynamodb_item(review_dict)
        )
        return review_uuid
        

    def get_user_reviews(self, user_uuid: UUID) -> list[Review]:
        
        response = self.review_table_client.query(
            TableName=self.review_table_name,
            IndexName="user_index",
            KeyConditionExpression="user_uuid=:user_uuid",
            ExpressionAttributeValues={":user_uuid": {"S": str(user_uuid)}}
        )
        
        items = response.get("Items", [])

        return [Review(**from_dynamodb_item(item)) for item in items]
    

    def get_property_reviews(self, property_uuid: UUID) -> list[Review]:

        response = self.review_table_client.query(
            TableName=self.review_table_name,
            IndexName="property_index",
            KeyConditionExpression="property_uuid=:property_uuid",
            ExpressionAttributeValues={":property_uuid": {"S": str(property_uuid)}}
        )
        
        items = response.get("Items", [])

        return [Review(**from_dynamodb_item(item)) for item in items]