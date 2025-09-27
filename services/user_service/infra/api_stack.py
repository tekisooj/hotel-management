from aws_cdk import (
    Stack,
    Duration,
    CfnOutput
)
from aws_cdk.aws_lambda import Function, Runtime, Code
from aws_cdk.aws_apigateway import RestApi, LambdaIntegration, EndpointType, MockIntegration, IntegrationResponse, MethodResponse, PassthroughBehavior
from aws_cdk.aws_iam import Role, ServicePrincipal, ManagedPolicy
from aws_cdk.aws_secretsmanager import Secret
from constructs import Construct
from aws_cdk.aws_ec2 import Vpc, SecurityGroup, SubnetSelection, SubnetType, Port


def add_cors_options(resource):
    resource.add_method(
        "OPTIONS",
        MockIntegration(
            integration_responses=[
                IntegrationResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Headers": "'*'",
                        "method.response.header.Access-Control-Allow-Origin": "'*'",
                        "method.response.header.Access-Control-Allow-Methods": "'OPTIONS,GET,POST,DELETE,PATCH'",
                    },
                )
            ],
            passthrough_behavior=PassthroughBehavior.WHEN_NO_MATCH,
            request_templates={"application/json": '{"statusCode": 200}'},
        ),
        method_responses=[
            MethodResponse(
                status_code="200",
                response_parameters={
                    "method.response.header.Access-Control-Allow-Headers": True,
                    "method.response.header.Access-Control-Allow-Methods": True,
                    "method.response.header.Access-Control-Allow-Origin": True,
                },
            )
        ],
    )


class UserServiceStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str, pr_number: str | None = None, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        self.env_name = env_name

        vpc = Vpc.from_lookup(self, "HotelManagementVpc", vpc_id="vpc-0b28dea117c8220de")

        db_sg = SecurityGroup.from_security_group_id(
            self, "HotelManagementDbSG",
            security_group_id="sg-030e54916d52c0bd0"
        )

        lambda_sg = SecurityGroup(
            self,
            f"UserServiceLambdaSG-{env_name}{f'-{pr_number}' if pr_number else ''}",
            vpc=vpc,
            allow_all_outbound=True,
            description="Security group for UserService Lambda",
        )

        db_sg.add_ingress_rule(
            peer=lambda_sg,
            connection=Port.tcp(5432),
            description="Allow Lambda to connect to RDS Proxy/Postgres"
        )

        lambda_role = Role(
            self, f"UserServiceLambdaRole-{env_name}{f'-{pr_number}' if pr_number else ''}",
            assumed_by=ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                ManagedPolicy.from_aws_managed_policy_name("AmazonRDSDataFullAccess"),
                ManagedPolicy.from_aws_managed_policy_name("SecretsManagerReadWrite"),
                ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
            ]
        )

        db_name = f"hotel-management-database-{self.env_name if self.env_name == 'prod' else 'int'}"
        db_secret = Secret.from_secret_name_v2(self, "DbSecret", secret_name=db_name)

        if self.env_name == "prod":
            proxy_role_arn = "arn:aws:iam::914242301564:role/service-role/rds-proxy-role-1758401519769"
            proxy_endpoint = "hotel-management-db-proxy-prod.proxy-capkwmowwxnt.us-east-1.rds.amazonaws.com"
            user_pool_id = "us-east-1_Wtvh2rdSQ"
            audience = "7226gqpnghn0q22ec2ill399lv"
            app_client_id = "7226gqpnghn0q22ec2ill399lv"
        else:
            proxy_role_arn = "arn:aws:iam::914242301564:role/service-role/rds-proxy-role-1758401469124"
            proxy_endpoint = "hotel-management-db-proxy-int.proxy-capkwmowwxnt.us-east-1.rds.amazonaws.com"
            user_pool_id = "us-east-1_DDS5D565p"
            audience = "la13fgbn7avmni0f84pu5lk79"
            app_client_id = "la13fgbn7avmni0f84pu5lk79"

        proxy_role = Role.from_role_arn(self, "ImportedProxyRole", proxy_role_arn)
        db_secret.grant_read(proxy_role)

        jwks_url = f"https://cognito-idp.us-east-1.amazonaws.com/{user_pool_id}/.well-known/jwks.json"

        lambda_function = Function(
            self, f"UserServiceFunction-{env_name}{f'-{pr_number}' if pr_number else ''}",
            runtime=Runtime.PYTHON_3_11,
            handler="main.handler",
            code=Code.from_asset("services/user_service/app"),
            role=lambda_role,
            timeout=Duration.seconds(60),
            memory_size=1024,
            environment={
                "USER_SERVICE_ENV": self.env_name,
                "HOTEL_MANAGEMENT_DATABASE_SECRET_NAME": db_name,
                "AUDIENCE": audience,
                "JWKS_URL": jwks_url,
                "APP_CLIENT_ID": app_client_id,
                "DB_PROXY_ENDPOINT": proxy_endpoint,
            },
            vpc=vpc,
            security_groups=[lambda_sg],
            vpc_subnets=SubnetSelection(subnet_type=SubnetType.PRIVATE_WITH_EGRESS),
        )

        api = RestApi(
            self, f"UserServiceApi-{env_name}{f'-{pr_number}' if pr_number else ''}",
            rest_api_name=f"user-service-api-{env_name}{f'-{pr_number}' if pr_number else ''}",
            description="API Gateway exposing user service Lambda",
            endpoint_types=[EndpointType.REGIONAL],
        )

        integration = LambdaIntegration(lambda_function, proxy=True)

        resource_me = api.root.add_resource("me")
        resource_user = api.root.add_resource("user")
        resource_user_id = resource_user.add_resource("{user_uuid}")

        resource_me.add_method("GET", integration)
        add_cors_options(resource_me)

        resource_user.add_method("POST", integration)
        add_cors_options(resource_user)

        resource_user_id.add_method("GET", integration)
        resource_user_id.add_method("DELETE", integration)
        resource_user_id.add_method("PATCH", integration)
        add_cors_options(resource_user_id)

        CfnOutput(self, "DbProxyEndpoint", value=proxy_endpoint)
