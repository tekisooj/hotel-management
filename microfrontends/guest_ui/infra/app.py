import aws_cdk as cdk
from ui_stack import GuestUiStack

app = cdk.App()

env_name = app.node.try_get_context("env") or "int"
pr_number = app.node.try_get_context("pr_number")

stack_id = f"GuestUiStack-pr-{pr_number}" if env_name == "pr" and pr_number else f"GuestUiStack-{env_name}"

GuestUiStack(app, stack_id, env_name=env_name, pr_number=pr_number)
app.synth()

