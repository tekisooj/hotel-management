from aws_cdk import (
    Stack,
    Duration,
)
from aws_cdk.aws_lambda import Function, Runtime, Code
from aws_cdk.aws_apigateway import LambdaRestApi
from aws_cdk.aws_iam import Role, ServicePrincipal, ManagedPolicy
from aws_cdk.aws_secretsmanager import Secret
from constructs import Construct

class UserServiceStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        self.env_name = env_name

        lambda_role = Role(
            self, "UserServiceLambdaRole",
            assumed_by=ServicePrincipal("lambda.amazonaws.com"), # type: ignore
            managed_policies=[
                ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                ManagedPolicy.from_aws_managed_policy_name("AmazonRDSDataFullAccess"),
                ManagedPolicy.from_aws_managed_policy_name("SecretsManagerReadWrite")
            ]
        )

        secret_name = f"user_database_{self.env_name}"

        db_secret = Secret.from_secret_name_v2(
            self, "UserServiceDBSecret",
            secret_name=secret_name
        )

        if self.env_name == "prod":
            user_pool_id = "us-east-1_Wtvh2rdSQ"
            audience = "7226gqpnghn0q22ec2ill399lv"
        else:
            user_pool_id = "us-east-1_DDS5D565p"
            audience = "la13fgbn7avmni0f84pu5lk79"

        jwks_url = f"https://cognito-idp.us-east-1.amazonaws.com/{user_pool_id}/.well-known/jwks.json"


        lambda_function = Function(
            self, "UserServiceFunction",
            runtime=Runtime.PYTHON_3_11,
            handler="main.handler",
            code=Code.from_asset("../services/user_service/app"),
            role=lambda_role, # type: ignore
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "USER_SERVICE_ENV": self.env_name,
                "USER_DATABASE_SECRET_NAME": secret_name,
                "AUDIENCE": audience,
                "JWKS_URL": jwks_url
            }
        )

        LambdaRestApi(
            self, "UserServiceApi",
            handler=lambda_function, # type: ignore
            proxy=True,
            rest_api_name="user-service-api",
            description="API Gateway exposing user service Lambda"
        )
