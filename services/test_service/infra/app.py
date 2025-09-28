from aws_cdk import App
from api_stack import TestServiceStack

app = App()
TestServiceStack(app, "TestServiceStack-int", env_name="int")
app.synth()
