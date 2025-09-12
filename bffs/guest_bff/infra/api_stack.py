from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy
)
from aws_cdk.aws_lambda import Function, Runtime, Code
from aws_cdk.aws_apigateway import LambdaRestApi, EndpointType, Cors
from aws_cdk.aws_events import EventBus
from aws_cdk.aws_iam import Role, ServicePrincipal, ManagedPolicy
from constructs import Construct

class GuestBffStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str, pr_number: str | None = None, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        self.env_name = env_name

        self.lambda_role = Role(
            self, f"GuestBffLambdaRole-{env_name}{f'-{pr_number}' if pr_number else ''}",
            assumed_by=ServicePrincipal("lambda.amazonaws.com"), # type: ignore
            managed_policies=[
                ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
            ]
        )

        self.lambda_function = Function(
            self, f"GuestBffFunction-{env_name}{f'-{pr_number}' if pr_number else ''}",
            runtime=Runtime.PYTHON_3_11,
            handler="main.handler",
            code=Code.from_asset("bffs/guest_bff/app"),
            role=self.lambda_role, # type: ignore
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "GUEST_BFF_ENV": self.env_name,
                "EVENT_BUS_NAME": "hotel-event-bus",
            }
        )

        self.gateway = LambdaRestApi(
            self, f"GuestBffApi-{env_name}{f'-{pr_number}' if pr_number else ''}",
            handler=self.lambda_function, # type: ignore
            proxy=True,
            rest_api_name=f"guest-bff-api-{env_name}{f'-{pr_number}' if pr_number else ''}",
            description="Public API Gateway exposing Guest BFF Lambda",
            endpoint_types=[EndpointType.REGIONAL],
            default_cors_preflight_options={
                "allow_origins": Cors.ALL_ORIGINS,
                "allow_methods": Cors.ALL_METHODS,
                "allow_headers": Cors.DEFAULT_HEADERS,
            },
        )

        event_bus = EventBus.from_event_bus_name(self, "SharedEventBus", "hotel-event-bus")
        event_bus.grant_put_events_to(self.lambda_function)  # type: ignore
