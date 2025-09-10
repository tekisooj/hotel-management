from aws_cdk import (
    Stack,
    Duration,
)
from aws_cdk.aws_lambda import Function, Runtime, Code
from aws_cdk.aws_apigateway import LambdaRestApi
from aws_cdk.aws_iam import Role, ServicePrincipal, ManagedPolicy, PolicyStatement
from aws_cdk.aws_events import Rule, EventPattern
from aws_cdk.aws_events_targets import LambdaFunction

from constructs import Construct


class NotificationServiceStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str, pr_number: str | None = None, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        self.env_name = env_name

        self.lambda_function = Function(
            self, f"NotificationLambda-{env_name}{f'-{pr_number}' if pr_number else ''}",
            runtime=Runtime.PYTHON_3_11,
            handler="main.handler",
            code=Code.from_asset("services/notification_service/app"),
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "NOTIFICATION_SERVICE_ENV": self.env_name,
            }
        )

        self.lambda_function.add_to_role_policy(PolicyStatement(
            actions=["ses:SendEmail", "ses:SendRawEmail"],
            resources=["*"]
        ))

        self.booking_rule = Rule(self, "BookingConfirmedEventRule",
            event_pattern=EventPattern(
                source=["booking-service"],
                detail_type=["booking.confirmed"]
            ))
        
        self.booking_rule.add_target(LambdaFunction(self.lambda_function)) # type: ignore

        self.review_rule = Rule(self, "ReviewCreatedEventRule",
            event_pattern=EventPattern(
                source=["review-service"],
                detail_type=["review.created"]
            ))

        self.review_rule.add_target(LambdaFunction(self.lambda_function)) # type: ignore
        