import os
import aws_cdk as cdk
from api_stack import HostBffStack

app = cdk.App()

env_name = app.node.try_get_context("env") or "int"
pr_number = app.node.try_get_context("pr_number")

stack_id = f"HostBffStack-pr-{pr_number}" if env_name == "pr" and pr_number else f"HostBffStack-{env_name}"

HostBffStack(app, stack_id, env_name=env_name, pr_number=pr_number)
app.synth()