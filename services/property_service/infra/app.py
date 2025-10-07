import os
import aws_cdk as cdk
from api_stack import PropertyServiceStack

app = cdk.App()

env_name = app.node.try_get_context("env") or "int"
pr_number = app.node.try_get_context("pr_number")

stack_id = f"PropertyServiceStack-pr-{pr_number}" if env_name == "pr" and pr_number else f"PropertyServiceStack-{env_name}"

PropertyServiceStack(
    app, 
    stack_id, 
    env=cdk.Environment(
        account="914242301564",
        region="us-east-1",
    ), 
    env_name=env_name, 
    pr_number=pr_number
)
app.synth()