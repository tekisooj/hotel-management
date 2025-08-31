import os
import aws_cdk as cdk
from user_service_stack import UserServiceStack

app = cdk.App()
UserServiceStack(app, "UserServiceStack", env_name=os.getenv("USER_SERVICE_ENV_NAME", "int"))
app.synth()