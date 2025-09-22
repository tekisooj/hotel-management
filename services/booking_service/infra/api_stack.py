from aws_cdk import (
    Stack,
    Duration,
    CfnOutput
)
from aws_cdk.aws_lambda import Function, Runtime, Code
from aws_cdk.aws_apigateway import RestApi, LambdaIntegration, EndpointType
from aws_cdk.aws_iam import Role, ServicePrincipal, ManagedPolicy
from aws_cdk.aws_secretsmanager import Secret
from constructs import Construct
from aws_cdk.aws_ec2 import Vpc, SecurityGroup, SubnetSelection, SubnetType

class BookingServiceStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str, pr_number: str | None = None, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        self.env_name = env_name

        vpc = Vpc.from_lookup(self, "HotelManagementVpc", vpc_id="vpc-0b28dea117c8220de")

        db_sg = SecurityGroup.from_security_group_id(
            self, "HotelManagementDbSG",
            security_group_id="sg-030e54916d52c0bd0"
        )

        lambda_role = Role(
            self, f"BookingServiceLambdaRole-{env_name}{f'-{pr_number}' if pr_number else ''}",
            assumed_by=ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                ManagedPolicy.from_aws_managed_policy_name("AmazonRDSDataFullAccess"),
                ManagedPolicy.from_aws_managed_policy_name("SecretsManagerReadWrite"),
                ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
            ]
        )

        db_name = f"hotel-management-database-{self.env_name if self.env_name == 'prod' else 'int'}"
        db_secret = Secret.from_secret_name_v2(self, "DbSecret", secret_name=db_name)

        
        if self.env_name=="prod":
            proxy_role_arn="arn:aws:iam::914242301564:role/service-role/rds-proxy-role-1758401519769"
        else:
            proxy_role_arn="arn:aws:iam::914242301564:role/service-role/rds-proxy-role-1758401469124"
        
        proxy_role = Role.from_role_arn(self, "ImportedProxyRole", proxy_role_arn)

        db_secret.grant_read(proxy_role)

        if self.env_name == "prod":
            proxy_endpoint = "hotel-management-db-proxy-prod.proxy-capkwmowwxnt.us-east-1.rds.amazonaws.com"
        else:
            proxy_endpoint = "hotel-management-db-proxy-int.proxy-capkwmowwxnt.us-east-1.rds.amazonaws.com"

        lambda_function = Function(
            self, f"BookingServiceFunction-{env_name}{f'-{pr_number}' if pr_number else ''}",
            runtime=Runtime.PYTHON_3_11,
            handler="main.handler",
            code=Code.from_asset("services/booking_service/app"),
            role=lambda_role,
            timeout=Duration.seconds(30),
            memory_size=1024,
            environment={
                "BOOKING_SERVICE_ENV": self.env_name,
                "HOTEL_MANAGEMENT_DATABASE_SECRET_NAME": db_name,
                "DB_PROXY_ENDPOINT": proxy_endpoint,
            },
            vpc=vpc,
            security_groups=[db_sg],
            vpc_subnets=SubnetSelection(
                subnet_type=SubnetType.PRIVATE_WITH_EGRESS
            )
        )

        api = RestApi(
            self, f"BookingServiceApi-{env_name}{f'-{pr_number}' if pr_number else ''}",
            rest_api_name=f"booking-service-api-{env_name}{f'-{pr_number}' if pr_number else ''}",
            description="API Gateway exposing booking service Lambda",
            endpoint_types=[EndpointType.REGIONAL],
        )
        integration = LambdaIntegration(lambda_function, proxy=True)

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

        resource_availability_id = resource_availability.add_resource("{room_uuid}")
        resource_availability_id.add_method("GET", integration)

        resource_availability_batch = resource_availability.add_resource("batch")
        resource_availability_batch.add_method("POST", integration)

        CfnOutput(self, "DbProxyEndpoint", value=proxy_endpoint)
