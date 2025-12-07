from aws_cdk import (
    Stack,
    Duration,
)
from aws_cdk.aws_lambda import Function, Runtime, Code
from aws_cdk.aws_iam import PolicyStatement
from aws_cdk.aws_events import Rule, EventPattern, EventBus
from aws_cdk.aws_events_targets import LambdaFunction
from aws_cdk.aws_sqs import Queue

from constructs import Construct


class NotificationServiceStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str, pr_number: str | None = None, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        self.env_name = env_name

        bus_name_suffix = f"-{pr_number}" if pr_number else ""
        self.event_bus = EventBus(
            self,
            "SharedEventBus",
            event_bus_name=f"hotel-event-bus-{env_name}{bus_name_suffix}",
        )

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

        self.dead_letter_queue = Queue(self, "NotificationDLQ")

        self.booking_rule = Rule(self, "BookingConfirmedEventRule",
            event_pattern=EventPattern(
                source=["booking-service"],
                detail_type=["BookingConfirmed"]
            ),
            event_bus=self.event_bus,
        )
        
        self.booking_rule.add_target(LambdaFunction(self.lambda_function, retry_attempts=3, dead_letter_queue=self.dead_letter_queue)) # type: ignore

        self.booking_cancelled_rule = Rule(self, "BookingCancelledEventRule",
            event_pattern=EventPattern(
                source=["booking-service"],
                detail_type=["BookingCancelled"]
            ),
            event_bus=self.event_bus,
        )

        self.booking_cancelled_rule.add_target(LambdaFunction(self.lambda_function, retry_attempts=3, dead_letter_queue=self.dead_letter_queue)) # type: ignore

        self.review_rule = Rule(self, "ReviewCreatedEventRule",
            event_pattern=EventPattern(
                source=["review-service"],
                detail_type=["ReviewCreated"]
            ),
            event_bus=self.event_bus,
        )

        self.review_rule.add_target(LambdaFunction(self.lambda_function, retry_attempts=3, dead_letter_queue=self.dead_letter_queue)) # type: ignore

        self.property_unavailable_rule = Rule(self, "PropertyUnavailableEventRule",
            event_pattern=EventPattern(
                source=["property-service"],
                detail_type=["PropertyUnavailable"]
            ),
            event_bus=self.event_bus,
        )

        self.property_unavailable_rule.add_target(LambdaFunction(self.lambda_function, retry_attempts=3, dead_letter_queue=self.dead_letter_queue)) # type: ignore
        
