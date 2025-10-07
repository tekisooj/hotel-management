import aws_cdk as cdk
from ui_stack import HostUiStack

app = cdk.App()

env_name = app.node.try_get_context("env") or "int"
pr_number = app.node.try_get_context("pr_number")

stack_id = f"HostUiStack-pr-{pr_number}" if env_name == "pr" and pr_number else f"HostUiStack-{env_name}"

HostUiStack(
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

