from aws_cdk import App, Environment
from api_stack import TestServiceStack

app = App()

# Define your AWS account and region explicitly
env = Environment(account="914242301564", region="us-east-1")

# Create the stack with the environment
TestServiceStack(app, "TestServiceStack-int", env_name="int", env=env)

app.synth()
