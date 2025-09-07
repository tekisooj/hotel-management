from aws_cdk import (
    Stack,
    Duration,
)
from aws_cdk.aws_lambda import Function, Runtime, Code
from aws_cdk.aws_apigateway import LambdaRestApi
from aws_cdk.aws_iam import Role, ServicePrincipal, ManagedPolicy
from aws_cdk.aws_secretsmanager import Secret
from constructs import Construct

class BookingServiceStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str, pr_number: str | None = None, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        self.env_name = env_name

        lambda_role = Role(
            self, f"BookingServiceLambdaRole-{env_name}{f'-{pr_number}' if pr_number else ''}",
            assumed_by=ServicePrincipal("lambda.amazonaws.com"), # type: ignore
            managed_policies=[
                ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                ManagedPolicy.from_aws_managed_policy_name("AmazonRDSDataFullAccess"),
                ManagedPolicy.from_aws_managed_policy_name("SecretsManagerReadWrite")
            ]
        )

        secret_name = f"hotel-management-database-{self.env_name if self.env_name == 'prod' else 'int'}"

        lambda_function = Function(
            self, f"BookingServiceFunction-{env_name}{f'-{pr_number}' if pr_number else ''}",
            runtime=Runtime.PYTHON_3_11,
            handler="main.handler",
            code=Code.from_asset("services/booking_service/app"),
            role=lambda_role, # type: ignore
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "BOOKING_SERVICE_ENV": self.env_name,
                "HOTEL_MANAGEMENT_DATABASE_SECRET_NAME": secret_name,
            }
        )

        
        LambdaRestApi(
            self, f"BookingServiceApi-{env_name}{f'-{pr_number}' if pr_number else ''}",
            handler=lambda_function, # type: ignore
            proxy=True,
            rest_api_name="booking-service-api",
            description="API Gateway exposing booking service Lambda"
        )