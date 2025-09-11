from aws_cdk import (
    Stack,
    Duration,
)
from aws_cdk.aws_lambda import Function, Runtime, Code
from aws_cdk.aws_apigateway import RestApi, LambdaIntegration, EndpointType
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

        api = RestApi(
            self, f"BookingServiceApi-{env_name}{f'-{pr_number}' if pr_number else ''}",
            rest_api_name=f"booking-service-api-{env_name}{f'-{pr_number}' if pr_number else ''}",
            description="API Gateway exposing booking service Lambda",
            endpoint_types=[EndpointType.REGIONAL],
        )
        integration = LambdaIntegration(lambda_function, proxy=True) # typing: ignore

        resource_booking = api.root.add_resource("booking")
        resource_booking.add_method("POST", integration)
        resource_booking.add_method("PATCH", integration)

        resource_booking_id = resource_booking.add_resource("{booking_uuid}")
        resource_booking_id.add_method("GET", integration)

        resource_booking_cancel = resource_booking_id.add_resource("cancel")
        resource_booking_cancel.add_method("PATCH", integration)

        resource_bookings = api.root.add_resource("bookings")
        resource_bookings.add_method("GET", integration)

        resource_availability = api.root.add_resource("availability")
        resource_availability.add_method("GET", integration)
