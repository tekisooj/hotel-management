from aws_cdk import Stack, CfnOutput, RemovalPolicy, Duration
from constructs import Construct
from aws_cdk import aws_s3 as s3
from aws_cdk.aws_cloudfront import CfnOriginAccessControl, Distribution, BehaviorOptions, ViewerProtocolPolicy, ErrorResponse
from aws_cdk.aws_cloudfront_origins import S3Origin
from aws_cdk.aws_s3_deployment import BucketDeployment, Source


class HostUiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str, pr_number: str | None = None, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        bucket = s3.Bucket(
            self,
            f"host-ui-bucket-{env_name}{f'-{pr_number}' if pr_number else ''}",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY if env_name != "prod" else RemovalPolicy.RETAIN,
            auto_delete_objects=(env_name != "prod"),
        )

        oac = CfnOriginAccessControl(self, "HostUiOAC",
            origin_access_control_config=CfnOriginAccessControl.OriginAccessControlConfigProperty(
                name=f"host-ui-oac-{env_name}{f'-{pr_number}' if pr_number else ''}",
                origin_access_control_origin_type="s3",
                signing_behavior="always",
                signing_protocol="sigv4",
                description="OAC for Host UI"
            )
        )

        dist = Distribution(
            self,
            f"host-ui-cf-{env_name}{f'-{pr_number}' if pr_number else ''}",
            default_behavior=BehaviorOptions(
                origin=S3Origin(bucket),
                viewer_protocol_policy=ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            default_root_object="index.html",
            error_responses=[
                ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(5),
                ),
                ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(5),
                ),
            ],
        )

        BucketDeployment(
            self,
            f"host-ui-deploy-{env_name}{f'-{pr_number}' if pr_number else ''}",
            sources=[Source.asset("../.output/public")],
            destination_bucket=bucket,
            distribution=dist,
            distribution_paths=["/*"],
            prune=True,
        )

        CfnOutput(self, "HostUiUrl", value=f"https://{dist.distribution_domain_name}")

