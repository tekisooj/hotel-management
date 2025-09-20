from aws_cdk import (
    Stack,
    Duration,
    CfnOutput
)
from aws_cdk.aws_lambda import Function, Runtime, Code
from aws_cdk.aws_apigateway import RestApi, LambdaIntegration, EndpointType
from aws_cdk.aws_iam import Role, ServicePrincipal, ManagedPolicy
from aws_cdk.aws_secretsmanager import Secret
from constructs import Construct
from aws_cdk.aws_ec2 import Vpc, SecurityGroup, SubnetSelection, SubnetType


class UserServiceStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str, pr_number: str | None = None, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        self.env_name = env_name

        vpc = Vpc.from_lookup(self, "HotelManagementVpc", vpc_id="vpc-00688d23d81374471")

        db_sg = SecurityGroup.from_security_group_id(
            self, "HotelManagementDbSG",
            security_group_id="sg-018c80394ac5a0590"
        )

        lambda_role = Role(
            self, f"UserServiceLambdaRole-{env_name}{f'-{pr_number}' if pr_number else ''}",
            assumed_by=ServicePrincipal("lambda.amazonaws.com"), # type: ignore
            managed_policies=[
                ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                ManagedPolicy.from_aws_managed_policy_name("AmazonRDSDataFullAccess"),
                ManagedPolicy.from_aws_managed_policy_name("SecretsManagerReadWrite"),
                ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
            ]
        )


        db_name = f"hotel-management-database-{self.env_name if self.env_name == 'prod' else 'int'}"
        db_secret = Secret.from_secret_name_v2(self, "DbSecret", secret_name=db_name)

        if self.env_name=="prod":
            proxy_role_arn="arn:aws:iam::914242301564:role/service-role/rds-proxy-role-1758401519769"
        else:
            proxy_role_arn="arn:aws:iam::914242301564:role/service-role/rds-proxy-role-1758401469124"
        
        proxy_role = Role.from_role_arn(self, "ImportedProxyRole", proxy_role_arn)

        db_secret.grant_read(proxy_role)

        if self.env_name == "prod":
            proxy_endpoint = "hotel-management-db-proxy-prod.proxy-capkwmowwxnt.us-east-1.rds.amazonaws.com"
        else:
            proxy_endpoint = "hotel-management-db-proxy-int.proxy-capkwmowwxnt.us-east-1.rds.amazonaws.com"

        if self.env_name == "prod":
            user_pool_id = "us-east-1_Wtvh2rdSQ"
            audience = "7226gqpnghn0q22ec2ill399lv"
        else:
            user_pool_id = "us-east-1_DDS5D565p"
            audience = "la13fgbn7avmni0f84pu5lk79"

        jwks_url = f"https://cognito-idp.us-east-1.amazonaws.com/{user_pool_id}/.well-known/jwks.json"

        app_client_id = "7226gqpnghn0q22ec2ill399lv" if self.env_name == "prod" else "la13fgbn7avmni0f84pu5lk79"

        lambda_function = Function(
            self, f"UserServiceFunction-{env_name}{f'-{pr_number}' if pr_number else ''}",
            runtime=Runtime.PYTHON_3_11,
            handler="main.handler",
            code=Code.from_asset("services/user_service/app"),
            role=lambda_role, # type: ignore
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "USER_SERVICE_ENV": self.env_name,
                "HOTEL_MANAGEMENT_DATABASE_SECRET_NAME": db_name,
                "AUDIENCE": audience,
                "JWKS_URL": jwks_url,
                "APP_CLIENT_ID": app_client_id,
                "DB_PROXY_ENDPOINT": proxy_endpoint,
            },
            vpc=vpc,
            security_groups=[db_sg],
            vpc_subnets=SubnetSelection(
                subnet_type=SubnetType.PRIVATE_WITH_EGRESS
            )
        )

        api = RestApi(
            self, f"UserServiceApi-{env_name}{f'-{pr_number}' if pr_number else ''}",
            rest_api_name=f"user-service-api-{env_name}{f'-{pr_number}' if pr_number else ''}",
            description="API Gateway exposing user service Lambda",
            endpoint_types=[EndpointType.REGIONAL],
        )
        integration = LambdaIntegration(lambda_function, proxy=True) #typing: ignore

        resource_me = api.root.add_resource("me")
        resource_me.add_method("GET", integration)

        resource_user = api.root.add_resource("user")
        resource_user.add_method("POST", integration)

        resource_user_id = resource_user.add_resource("{user_uuid}")
        resource_user_id.add_method("GET", integration)
        resource_user_id.add_method("DELETE", integration)
        resource_user_id.add_method("PATCH", integration)

        CfnOutput(self, "DbProxyEndpoint", value=proxy_endpoint)
