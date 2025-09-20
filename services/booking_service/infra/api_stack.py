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
from aws_cdk.aws_ec2 import Vpc, SecurityGroup, SubnetSelection, SubnetType, Port
from aws_cdk.aws_rds import (
    DatabaseInstance,
    DatabaseInstanceAttributes,
    DatabaseProxy,
    ProxyTarget
)

class BookingServiceStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str, pr_number: str | None = None, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        self.env_name = env_name

        vpc = Vpc.from_lookup(self, "HotelManagementVpc", vpc_id="vpc-00688d23d81374471")

        db_sg = SecurityGroup.from_security_group_id(
            self, "HotelManagementDbSG",
            security_group_id="sg-018c80394ac5a0590"
        )

        lambda_role = Role(
            self, f"BookingServiceLambdaRole-{env_name}{f'-{pr_number}' if pr_number else ''}",
            assumed_by=ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                ManagedPolicy.from_aws_managed_policy_name("AmazonRDSDataFullAccess"),
                ManagedPolicy.from_aws_managed_policy_name("SecretsManagerReadWrite"),
                ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")
            ]
        )

        db_name = f"hotel-management-database-{self.env_name if self.env_name == 'prod' else 'int'}"
        db_secret = Secret.from_secret_name_v2(self, "DbSecret", secret_name=db_name)

        if self.env_name=="prod":
            db_endpoint="hotel-management-database-prod.cluster-capkwmowwxnt.us-east-1.rds.amazonaws.com"
        else:
            db_endpoint="hotel-management-database-int.cluster-capkwmowwxnt.us-east-1.rds.amazonaws.com"

        db_instance = DatabaseInstance.from_database_instance_attributes(
            self, "ImportedDbInstance",
            instance_endpoint_address=f"{db_name}.cluster-xxxxxx.us-east-1.rds.amazonaws.com",
            instance_identifier=db_endpoint,
            port=5432,
            security_groups=[db_sg]
        )

        db_proxy = DatabaseProxy(
            self, f"BookingDbProxy-{env_name}{f'-{pr_number}' if pr_number else ''}",
            proxy_target=ProxyTarget.from_instance(db_instance),
            vpc=vpc,
            secrets=[db_secret],
            require_tls=True,
            idle_client_timeout=Duration.minutes(30),
            max_connections_percent=50,
            vpc_subnets=SubnetSelection(subnet_type=SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[db_sg]
        )

        lambda_function = Function(
            self, f"BookingServiceFunction-{env_name}{f'-{pr_number}' if pr_number else ''}",
            runtime=Runtime.PYTHON_3_11,
            handler="main.handler",
            code=Code.from_asset("services/booking_service/app"),
            role=lambda_role,
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "BOOKING_SERVICE_ENV": self.env_name,
                "HOTEL_MANAGEMENT_DATABASE_SECRET_NAME": db_name,
                "DB_PROXY_ENDPOINT": db_proxy.endpoint, 
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

        CfnOutput(self, "DbProxyEndpoint", value=db_proxy.endpoint)
