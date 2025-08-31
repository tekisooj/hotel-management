import os
import aws_cdk as cdk
from user_service_stack import UserServiceStack

app = cdk.App()
UserServiceStack(app, "UserServiceStack", env_name=os.getenv("DEPLOY_ENV", "int"))
app.synth()