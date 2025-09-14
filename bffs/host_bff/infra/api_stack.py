from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy
)
from aws_cdk.aws_lambda import Function, Runtime, Code
from aws_cdk.aws_apigateway import LambdaRestApi, EndpointType, Cors, LambdaIntegration
from aws_cdk.aws_events import EventBus
from aws_cdk.aws_iam import Role, ServicePrincipal, ManagedPolicy, PolicyStatement
from constructs import Construct

class HostBffStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str, pr_number: str | None = None, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        self.env_name = env_name

        self.lambda_role = Role(
            self, f"HostBffLambdaRole-{env_name}{f'-{pr_number}' if pr_number else ''}",
            assumed_by=ServicePrincipal("lambda.amazonaws.com"), # type: ignore
            managed_policies=[
                ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
            ]
        )
        
        if self.env_name == "prod":
            self.user_pool_id = "us-east-1_Wtvh2rdSQ"
            self.audience = "7226gqpnghn0q22ec2ill399lv"
        else:
            self.user_pool_id = "us-east-1_DDS5D565p"
            self.audience = "la13fgbn7avmni0f84pu5lk79"

        self.jwks_url = f"https://cognito-idp.us-east-1.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json"


        self.lambda_function = Function(
            self, f"HostBffFunction-{env_name}{f'-{pr_number}' if pr_number else ''}",
            runtime=Runtime.PYTHON_3_11,
            handler="main.handler",
            code=Code.from_asset("bffs/host_bff/app"),
            role=self.lambda_role, # type: ignore
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "HOST_BFF_ENV": self.env_name,
                "AUDIENCE": self.audience,
                "JWKS_URL": self.jwks_url,
                "PLACE_INDEX_NAME": "HotelManagementPlaceIndex",
            }
        )

        self.gateway = LambdaRestApi(
            self, f"HostBffApi-{env_name}{f'-{pr_number}' if pr_number else ''}",
            handler=self.lambda_function, # type: ignore
            proxy=True,
            rest_api_name=f"host-bff-api-{env_name}{f'-{pr_number}' if pr_number else ''}",
            description="Public API Gateway exposing Host BFF Lambda",
            endpoint_types=[EndpointType.REGIONAL],
            default_cors_preflight_options={
                "allow_origins": Cors.ALL_ORIGINS,
                "allow_methods": Cors.ALL_METHODS,
                "allow_headers": Cors.DEFAULT_HEADERS,
            },
        )

        integration = LambdaIntegration(self.lambda_function)

        places = self.gateway.root.add_resource("places")
        places_search = places.add_resource("search-text")
        places_search.add_method("GET", integration)

        properties = self.gateway.root.add_resource("properties")
        properties.add_method("GET", integration)

        property_res = self.gateway.root.add_resource("property")
        property_res.add_method("POST", integration)
        property_res.add_method("PUT", integration)
        property_id = property_res.add_resource("{property_uuid}")
        property_id.add_method("DELETE", integration)

        room = self.gateway.root.add_resource("room")
        room.add_method("POST", integration)
        room.add_method("PUT", integration)
        room_id = room.add_resource("{room_uuid}")
        room_id.add_method("DELETE", integration)

        bookings = self.gateway.root.add_resource("bookings")
        bookings.add_method("GET", integration)

        booking = self.gateway.root.add_resource("booking")
        booking_id = booking.add_resource("{booking_uuid}")
        booking_id.add_method("PATCH", integration)

        reviews = self.gateway.root.add_resource("reviews")
        reviews_property = reviews.add_resource("{property_uuid}")
        reviews_property.add_method("GET", integration)

        me = self.gateway.root.add_resource("me")
        me.add_method("GET", integration)
        me.add_method("PATCH", integration)
        
        self.lambda_function.add_to_role_policy(PolicyStatement(
            actions=["geo:SearchPlaceIndexForText"],
            resources=["*"]
        ))
