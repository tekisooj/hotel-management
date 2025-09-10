import boto3

class NotificationClient:
    def __init__(sender_email: str, region: str):
        self.sender_email = sender_email
        self.ses_client = boto3.client("ses", region_name=aws_region)
        
    def send_email(to_email: str, subject: str, message: str):
        return self.ses_client.send_email(
            Source=self.sender_email,
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": message}}
            }
        )