from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy
)
from aws_cdk.aws_lambda import Function, Runtime, Code
from aws_cdk.aws_apigateway import RestApi, LambdaIntegration, EndpointType
from aws_cdk.aws_iam import Role, ServicePrincipal, ManagedPolicy
from aws_cdk.aws_dynamodb import Attribute, AttributeType, BillingMode, Table, TableEncryption
from constructs import Construct

class ReviewServiceStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str, pr_number: str | None = None, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        self.env_name = env_name

        suffix = f"-{pr_number}" if pr_number else ""


        self.lambda_role = Role(
            self, f"ReviewServiceLambdaRole-{env_name}{suffix}",
            assumed_by=ServicePrincipal("lambda.amazonaws.com"), # type: ignore
            managed_policies=[
                ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                ManagedPolicy.from_aws_managed_policy_name("SecretsManagerReadWrite"),
            ]
        )

        self.review_table = Table(
            self,
            "review_table",
            table_name=f"review_table_{env_name}{suffix}",
            partition_key=Attribute(name="uuid", type=AttributeType.STRING),
            encryption=TableEncryption.AWS_MANAGED,
            billing_mode=BillingMode.PAY_PER_REQUEST
        )

        self.review_table.add_global_secondary_index(
            index_name="property_index",
            partition_key=Attribute(name="property_uuid", type=AttributeType.STRING),
            sort_key=Attribute(name="timestamp", type=AttributeType.STRING)
        )

        self.review_table.add_global_secondary_index(
            index_name="user_index",
            partition_key=Attribute(name="user_uuid", type=AttributeType.STRING),
            sort_key=Attribute(name="timestamp", type=AttributeType.STRING)
        )

        self.lambda_function = Function(
            self, f"ReviewServiceFunction-{env_name}{suffix}",
            runtime=Runtime.PYTHON_3_11,
            handler="main.handler",
            code=Code.from_asset("services/review_service/app"),
            role=self.lambda_role, # type: ignore
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "REVIEW_SERVICE_ENV": self.env_name,
                "REVIEW_TABLE_NAME": self.review_table.table_name,
            }
        )

        self.review_table.grant_read_write_data(self.lambda_function)

        self.api = RestApi(
            self, f"ReviewServiceApi-{env_name}{suffix}",
            rest_api_name=f"review-service-api-{env_name}{suffix}",
            description="API Gateway exposing review service Lambda",
            endpoint_types=[EndpointType.REGIONAL],
        )
        self.integration = LambdaIntegration(self.lambda_function, proxy=True) #typing: ignore


        self.resource_review = self.api.root.add_resource("review")
        self.resource_review_id = self.resource_review.add_resource("{property_uuid}")
        self.resource_review_id.add_method("POST", self.integration)

        self.resource_reviews = self.api.root.add_resource("reviews")
        self.resource_reviews_id = self.resource_reviews.add_resource("{id}")
        self.resource_reviews_id.add_method("GET", self.integration)
