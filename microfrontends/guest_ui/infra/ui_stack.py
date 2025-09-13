from aws_cdk import Stack, CfnOutput, RemovalPolicy, Duration
from constructs import Construct
from aws_cdk import aws_s3 as s3
from aws_cdk.aws_cloudfront import CfnOriginAccessControl, Distribution, BehaviorOptions, ViewerProtocolPolicy, ErrorResponse
from aws_cdk.aws_cloudfront_origins import S3Origin
from aws_cdk.aws_s3_deployment import BucketDeployment, Source
from pathlib import Path


class GuestUiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_name: str, pr_number: str | None = None, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        bucket = s3.Bucket(
            self,
            f"guest-ui-bucket-{env_name}{f'-{pr_number}' if pr_number else ''}",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY if env_name != "prod" else RemovalPolicy.RETAIN,
            auto_delete_objects=(env_name != "prod"),
        )

        oac = CfnOriginAccessControl(self, "GuestUiOAC",
            origin_access_control_config=CfnOriginAccessControl.OriginAccessControlConfigProperty(
                name=f"guest-ui-oac-{env_name}{f'-{pr_number}' if pr_number else ''}",
                origin_access_control_origin_type="s3",
                signing_behavior="always",
                signing_protocol="sigv4",
                description="OAC for Guest UI"
            )
        )

        dist = Distribution(
            self,
            f"guest-ui-cf-{env_name}{f'-{pr_number}' if pr_number else ''}",
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

        # Deploy local built assets (Nuxt generate) to S3 and invalidate CF
        build_dir = (Path(__file__).resolve().parents[1] / ".output" / "public").as_posix()
        BucketDeployment(
            self,
            f"guest-ui-deploy-{env_name}{f'-{pr_number}' if pr_number else ''}",
            sources=[Source.asset(build_dir)],
            destination_bucket=bucket,
            distribution=dist,
            distribution_paths=["/*"],
            prune=True,
        )

        CfnOutput(self, "GuestUiUrl", value=f"https://{dist.distribution_domain_name}")

