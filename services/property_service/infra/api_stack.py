from aws_cdk import (
    Stack,
    Duration,
)
from aws_cdk.aws_lambda import Function, Runtime, Code
from aws_cdk.aws_apigateway import RestApi, LambdaIntegration, EndpointType
from aws_cdk.aws_iam import Role, ServicePrincipal, ManagedPolicy
from aws_cdk.aws_dynamodb import Attribute, AttributeType, BillingMode, Table, TableEncryption
from constructs import Construct

class PropertyServiceStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str, pr_number: str | None = None, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        self.env_name = env_name

        lambda_role = Role(
            self, f"PropertyServiceLambdaRole-{env_name}{f'-{pr_number}' if pr_number else ''}",
            assumed_by=ServicePrincipal("lambda.amazonaws.com"), # type: ignore
            managed_policies=[
                ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
            ]
        )
        
        property_table = Table(
            self,
            "property_table",
            table_name=f"property_table_{env_name}{f'-{pr_number}' if pr_number else ''}",
            partition_key=Attribute(name="uuid", type=AttributeType.STRING),
            encryption=TableEncryption.AWS_MANAGED,
            billing_mode=BillingMode.PAY_PER_REQUEST,
        )
        
        property_table.add_global_secondary_index(
            index_name="user_index",
            partition_key=Attribute(name="user_uuid", type=AttributeType.STRING),
            sort_key=Attribute(name="created_at", type=AttributeType.STRING),
        )

        room_table = Table(
            self,
            "room_table",
            table_name=f"room_table_{env_name}{f'-{pr_number}' if pr_number else ''}",
            partition_key=Attribute(name="property_uuid", type=AttributeType.STRING),
            sort_key=Attribute(name="uuid", type=AttributeType.STRING),
            encryption=TableEncryption.AWS_MANAGED,
            billing_mode=BillingMode.PAY_PER_REQUEST,
        )

        room_table.add_global_secondary_index(
            index_name="room_uuid_index",
            partition_key=Attribute(name="uuid", type=AttributeType.STRING),
        )

        lambda_function = Function(
            self, f"PropertyServiceFunction-{env_name}{f'-{pr_number}' if pr_number else ''}",
            runtime=Runtime.PYTHON_3_11,
            handler="main.handler",
            code=Code.from_asset("services/property_service/app"),
            role=lambda_role, # type: ignore
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "PROPERTY_SERVICE_ENV": self.env_name,
                "PROPERTY_TABLE_NAME": property_table.table_name,
                "ROOM_TABLE_NAME": room_table.table_name
            }
        )

        property_table.grant_read_write_data(lambda_function)
        room_table.grant_read_write_data(lambda_function)

        api = RestApi(
            self, f"PropertyServiceApi-{env_name}{f'-{pr_number}' if pr_number else ''}",
            rest_api_name=f"property-service-api-{env_name}{f'-{pr_number}' if pr_number else ''}",
            description="API Gateway exposing property service Lambda",
            endpoint_types=[EndpointType.REGIONAL],
        )
        integration = LambdaIntegration(lambda_function, proxy=True) #typing: ignore

        resource_property = api.root.add_resource("property")
        resource_property.add_method("POST", integration)

        resource_property_id = resource_property.add_resource("{property_uuid}")
        resource_property_id.add_method("GET", integration)

        resource_room = api.root.add_resource("room")
        resource_room.add_method("POST", integration)

        resource_room_id = resource_room.add_resource("{room_uuid}")
        resource_room_id.add_method("GET", integration)

        resource_rooms = api.root.add_resource("rooms")
        resource_rooms.add_method("GET", integration)

        resource_rooms_property = resource_rooms.add_resource("{property_uuid}")
        resource_rooms_property.add_method("GET", integration)
