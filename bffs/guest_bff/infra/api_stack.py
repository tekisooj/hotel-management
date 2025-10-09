import os
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
)
from aws_cdk.aws_lambda import Function, Runtime, Code
from aws_cdk.aws_apigateway import LambdaRestApi, EndpointType, Cors, LambdaIntegration
from aws_cdk.aws_events import EventBus
from aws_cdk.aws_iam import Role, ServicePrincipal, ManagedPolicy, PolicyStatement
from constructs import Construct


class GuestBffStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str, pr_number: str | None = None, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        self.env_name = env_name
        suffix = f"-{pr_number}" if pr_number else ""

        self.lambda_role = Role(
            self,
            f"GuestBffLambdaRole-{env_name}{suffix}",
            assumed_by=ServicePrincipal("lambda.amazonaws.com"),  # type: ignore
            managed_policies=[
                ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
            ],
        )

        if self.env_name == "prod":
            self.user_pool_id = "us-east-1_Wtvh2rdSQ"
            self.audience = "7226gqpnghn0q22ec2ill399lv"
        else:
            self.user_pool_id = "us-east-1_DDS5D565p"
            self.audience = "la13fgbn7avmni0f84pu5lk79"

        self.jwks_url = f"https://cognito-idp.us-east-1.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json"

        paypal_env = {
            key: value
            for key, value in {
                "PAYPAL_CLIENT_ID": os.environ.get("PAYPAL_CLIENT_ID"),
                "PAYPAL_CLIENT_SECRET": os.environ.get("PAYPAL_CLIENT_SECRET"),
                "PAYPAL_BASE_URL": os.environ.get("PAYPAL_BASE_URL"),
            }.items()
            if value
        }

        self.lambda_function = Function(
            self,
            f"GuestBffFunction-{env_name}{suffix}",
            runtime=Runtime.PYTHON_3_11,
            handler="main.handler",
            code=Code.from_asset("bffs/guest_bff/app"),
            role=self.lambda_role,  # type: ignore
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "GUEST_BFF_ENV": self.env_name,
                "EVENT_BUS_NAME": "hotel-event-bus",
                "AUDIENCE": self.audience,
                "JWKS_URL": self.jwks_url,
                "PLACE_INDEX_NAME": "HotelManagementPlaceIndex",
                **paypal_env,
            },
        )

        self.gateway = LambdaRestApi(
            self,
            f"GuestBffApi-{env_name}{suffix}",
            handler=self.lambda_function,  # type: ignore
            proxy=True,
            rest_api_name=f"guest-bff-api-{env_name}{suffix}",
            description="Public API Gateway exposing Guest BFF Lambda",
            endpoint_types=[EndpointType.REGIONAL],
            default_cors_preflight_options={
                "allow_origins": Cors.ALL_ORIGINS,
                "allow_methods": Cors.ALL_METHODS,
                "allow_headers": [
                    *Cors.DEFAULT_HEADERS,
                    "X-User-Id",
                    "x-user-id",
                ],
            },
        )

        event_bus = EventBus.from_event_bus_name(self, "SharedEventBus", "hotel-event-bus")
        event_bus.grant_put_events_to(self.lambda_function)  # type: ignore

        self.lambda_function.add_to_role_policy(
            PolicyStatement(actions=["geo:SearchPlaceIndexForText"], resources=["*"])
        )

        integration = LambdaIntegration(self.lambda_function)

        places = self.gateway.root.add_resource("places")
        places_search = places.add_resource("search-text")
        places_search.add_method("GET", integration)

        review = self.gateway.root.add_resource("review")
        review.add_method("POST", integration)

        reviews = self.gateway.root.add_resource("reviews")
        reviews_property = reviews.add_resource("{property_uuid}")
        reviews_property.add_method("GET", integration)

        booking = self.gateway.root.add_resource("booking")
        booking.add_method("POST", integration)

        payment = booking.add_resource("payment")
        payment_order = payment.add_resource("order")
        payment_order.add_method("POST", integration)
        payment_capture = payment.add_resource("capture")
        payment_capture.add_method("POST", integration)

        my = self.gateway.root.add_resource("my")
        my_bookings = my.add_resource("bookings")
        my_bookings.add_method("GET", integration)
        my_booking = my.add_resource("booking")
        my_booking_id = my_booking.add_resource("{booking_uuid}")
        my_booking_id.add_method("DELETE", integration)

        rooms = self.gateway.root.add_resource("rooms")
        rooms.add_method("GET", integration)

        room = self.gateway.root.add_resource("room")
        room_id = room.add_resource("{room_uuid}")
        room_id.add_method("GET", integration)

        property_res = self.gateway.root.add_resource("property")
        property_id = property_res.add_resource("{property_uuid}")
        property_id.add_method("GET", integration)

        me = self.gateway.root.add_resource("me")
        me.add_method("GET", integration)
        me.add_method("PATCH", integration)
