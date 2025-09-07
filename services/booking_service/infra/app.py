import os
import aws_cdk as cdk
from api_stack import BookingServiceStack

app = cdk.App()

env_name = app.node.try_get_context("env") or "int"
pr_number = app.node.try_get_context("pr_number")

stack_id = f"BookingServiceStack-pr-{pr_number}" if env_name == "pr" and pr_number else f"BookingServiceStack-{env_name}"

BookingServiceStack(app, stack_id, env_name=env_name, pr_number=pr_number)
app.synth()