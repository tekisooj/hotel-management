from typing import Any
import boto3

class NotificationClient:
    def __init__(self, sender_email: str, region: str) -> None:
        self.sender_email = sender_email
        self.ses_client = boto3.client("ses", region_name=region)
        
    def send_email(self, to_email: str, subject: str, message: str) -> Any:
        return self.ses_client.send_email(
            Source=self.sender_email,
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": message}}
            }
        )