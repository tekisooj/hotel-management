import boto3

from schemas import SignUpRequest


class CognitoClient:
    def __init__(self, aws_region: str | None = None, app_client_id: str | None = None) -> None:
        if not aws_region or not app_client_id:
            raise ValueError("Failed to initialize cognito client")
        self.cognito_client = boto3.client("cognito-idp", region_name=aws_region)
        self.app_client_id = app_client_id

    def sign_up(self, sign_up_request: SignUpRequest) -> None:
        self.cognito_client.sign_up(
            ClientId=self.app_client_id,
            Username=sign_up_request.email,
            Password=sign_up_request.password,
            UserAttributes=[
                {"Name": "email", "Value": sign_up_request.email},
                {"Name": "given_name", "Value": sign_up_request.name},
                {"Name": "family_name", "Value": sign_up_request.last_name}
            ]
        )