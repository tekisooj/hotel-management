from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
)
from aws_cdk.aws_apigateway import EndpointType, LambdaIntegration, RestApi
from aws_cdk.aws_dynamodb import Attribute, AttributeType, BillingMode, Table, TableEncryption
from aws_cdk.aws_iam import ManagedPolicy, Role, ServicePrincipal
from aws_cdk.aws_lambda import Code, Function, Runtime
from aws_cdk.aws_s3 import BlockPublicAccess, Bucket, BucketEncryption, CorsRule, HttpMethods
from constructs import Construct


class PropertyServiceStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str, pr_number: str | None = None, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        self.env_name = env_name
        suffix = f"-{pr_number}" if pr_number else ""

        lambda_role = Role(
            self,
            f"PropertyServiceLambdaRole-{env_name}{suffix}",
            assumed_by=ServicePrincipal("lambda.amazonaws.com"),  # type: ignore
            managed_policies=[
                ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
            ],
        )

        property_table = Table(
            self,
            "property_table",
            table_name=f"property_table_{env_name}{suffix}",
            partition_key=Attribute(name="uuid", type=AttributeType.STRING),
            encryption=TableEncryption.AWS_MANAGED,
            billing_mode=BillingMode.PAY_PER_REQUEST,
        )

        property_table.add_global_secondary_index(
            index_name="user_index",
            partition_key=Attribute(name="user_uuid", type=AttributeType.STRING),
            sort_key=Attribute(name="created_at", type=AttributeType.STRING),
        )

        property_table.add_global_secondary_index(
            index_name="city_index",
            partition_key=Attribute(name="city_key", type=AttributeType.STRING),
            sort_key=Attribute(name="created_at", type=AttributeType.STRING),
        )

        room_table = Table(
            self,
            "room_table",
            table_name=f"room_table_{env_name}{suffix}",
            partition_key=Attribute(name="uuid", type=AttributeType.STRING),
            encryption=TableEncryption.AWS_MANAGED,
            billing_mode=BillingMode.PAY_PER_REQUEST,
        )

        room_table.add_global_secondary_index(
            index_name="property_uuid_index",
            partition_key=Attribute(name="property_uuid", type=AttributeType.STRING),
        )

        assets_bucket = Bucket(
            self,
            "property_assets_bucket",
            bucket_name=f"property-assets-{env_name}{suffix}",
            block_public_access=BlockPublicAccess.BLOCK_ALL,
            encryption=BucketEncryption.S3_MANAGED,
            cors=[
                CorsRule(
                    allowed_methods=[HttpMethods.POST, HttpMethods.PUT],
                    allowed_origins=["*"],
                    allowed_headers=["*"],
                    exposed_headers=["ETag"],
                    max_age=3000,
                )
            ],
            removal_policy=RemovalPolicy.RETAIN if env_name == "prod" else RemovalPolicy.DESTROY,
            auto_delete_objects=env_name != "prod",
        )

        lambda_function = Function(
            self,
            f"PropertyServiceFunction-{env_name}{suffix}",
            runtime=Runtime.PYTHON_3_11,
            handler="main.handler",
            code=Code.from_asset("services/property_service/app"),
            role=lambda_role,  # type: ignore
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "PROPERTY_SERVICE_ENV": self.env_name,
                "PROPERTY_TABLE_NAME": property_table.table_name,
                "ROOM_TABLE_NAME": room_table.table_name,
                "ASSET_BUCKET_NAME": assets_bucket.bucket_name,
            },
        )

        property_table.grant_read_write_data(lambda_function)
        room_table.grant_read_write_data(lambda_function)
        assets_bucket.grant_read_write(lambda_function)

        api = RestApi(
            self,
            f"PropertyServiceApi-{env_name}{suffix}",
            rest_api_name=f"property-service-api-{env_name}{suffix}",
            description="API Gateway exposing property service Lambda",
            endpoint_types=[EndpointType.REGIONAL],
        )
        integration = LambdaIntegration(lambda_function, proxy=True)  # typing: ignore

        resource_assets = api.root.add_resource("assets")
        resource_assets_upload = resource_assets.add_resource("upload-url")
        resource_assets_upload.add_method("POST", integration)

        resource_property = api.root.add_resource("property")
        resource_property.add_method("POST", integration)

        resource_property_id = resource_property.add_resource("{property_uuid}")
        resource_property_id.add_method("GET", integration)

        resource_user = api.root.add_resource("user")
        resource_user_id = resource_user.add_resource("{user_uuid}")
        resource_user_properties = resource_user_id.add_resource("properties")
        resource_user_properties.add_method("GET", integration)

        resource_room = api.root.add_resource("room")
        resource_room.add_method("POST", integration)

        resource_room_id = resource_room.add_resource("{room_uuid}")
        resource_room_id.add_method("GET", integration)

        resource_rooms = api.root.add_resource("rooms")
        resource_rooms.add_method("GET", integration)

        resource_rooms_property = resource_rooms.add_resource("{property_uuid}")
        resource_rooms_property.add_method("GET", integration)

        resource_properties = api.root.add_resource("properties")
        resource_properties_city = resource_properties.add_resource("city")
        resource_properties_city.add_method("GET", integration)

        resource_properties_near = resource_properties.add_resource("near")
        resource_properties_near.add_method("GET", integration)
