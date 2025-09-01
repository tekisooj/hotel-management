import os
import aws_cdk as cdk
from infra.cdk.stacks.user_service.api_stack import UserServiceStack

app = cdk.App()

env_name = app.node.try_get_context("env") or "int"
pr_number = app.node.try_get_context("pr_number")

stack_id = f"UserServiceStack-pr-{pr_number}" if env_name == "pr" and pr_number else f"UserServiceStack-{env_name}"

UserServiceStack(app, stack_id, env_name=env_name, pr_number=pr_number)
app.synth()