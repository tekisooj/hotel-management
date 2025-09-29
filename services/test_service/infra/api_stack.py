from aws_cdk import (
    Stack,
    Duration,
    CfnOutput
)
from aws_cdk.aws_lambda import Function, Runtime, Code
from aws_cdk.aws_apigateway import RestApi, LambdaIntegration, EndpointType
from aws_cdk.aws_iam import Role, ServicePrincipal, ManagedPolicy
from aws_cdk.aws_secretsmanager import Secret
from aws_cdk.aws_ec2 import Vpc, SecurityGroup, SubnetSelection, SubnetType, Port
from constructs import Construct
import os


class TestServiceStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # ✅ Use existing default VPC (same one as DB Proxy)
        vpc = Vpc.from_lookup(self, "Vpc", vpc_id="vpc-0b28dea117c8220de")

        # ✅ Reuse RDS SG and allow Lambda → DB traffic
        db_sg = SecurityGroup.from_security_group_id(
            self, "DbSG",
            "sg-030e54916d52c0bd0"
        )

        lambda_sg = SecurityGroup(
            self, f"TestServiceLambdaSG-{env_name}",
            vpc=vpc,
            allow_all_outbound=True,
            description="Security group for Test Service Lambda"
        )

        db_sg.add_ingress_rule(
            lambda_sg,
            Port.tcp(5432),
            "Allow Lambda to access DB proxy"
        )

        # ✅ IAM Role with Secrets + RDS + VPC permissions
        lambda_role = Role(
            self, f"TestServiceLambdaRole-{env_name}",
            assumed_by=ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                ManagedPolicy.from_aws_managed_policy_name("AmazonRDSDataFullAccess"),
                ManagedPolicy.from_aws_managed_policy_name("SecretsManagerReadWrite"),
                ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
            ]
        )

        # ✅ Select DB secret and proxy
        db_secret_name = f"hotel-management-database-{env_name if env_name == 'prod' else 'int'}"
        db_secret = Secret.from_secret_name_v2(self, "DbSecret", secret_name=db_secret_name)

        proxy_endpoint = (
            "hotel-management-db-proxy-prod.proxy-capkwmowwxnt.us-east-1.rds.amazonaws.com"
            if env_name == "prod"
            else "hotel-management-db-proxy-int.proxy-capkwmowwxnt.us-east-1.rds.amazonaws.com"
        )

        # ✅ Bundle PEM file for SSL connection
        pem_path = os.path.join("services", "test_service", "app", "global-bundle.pem")
        if not os.path.exists(pem_path):
            print(f"⚠️ Warning: PEM file not found at {pem_path}. Make sure it exists before deploy.")

        # ✅ Lambda Function definition
        lambda_function = Function(
            self, f"TestServiceFunction-{env_name}",
            runtime=Runtime.PYTHON_3_11,
            handler="main.app",
            code=Code.from_asset(
                "services/test_service/app",
                exclude=["__pycache__"],
                # PEM file will be included automatically since it's in the folder
            ),
            role=lambda_role,
            timeout=Duration.seconds(20),
            memory_size=512,
            environment={
                "REGION": "us-east-1",
                "DB_SECRET_NAME": db_secret_name,
                "DB_PROXY_ENDPOINT": proxy_endpoint,
                "SSL_CERT_PATH": "/var/task/global-bundle.pem"  # ✅ Path inside Lambda container
            },
            vpc=vpc,
            security_groups=[lambda_sg],
            vpc_subnets=SubnetSelection(subnet_type=SubnetType.PRIVATE_WITH_EGRESS)
        )

        # ✅ API Gateway setup
        api = RestApi(
            self, f"TestServiceApi-{env_name}",
            rest_api_name=f"test-service-api-{env_name}",
            description="API Gateway for DB connectivity test",
            endpoint_types=[EndpointType.REGIONAL],
        )

        integration = LambdaIntegration(lambda_function, proxy=True)
        api.root.add_method("GET", integration)

        CfnOutput(self, "TestServiceApiUrl", value=api.url)
