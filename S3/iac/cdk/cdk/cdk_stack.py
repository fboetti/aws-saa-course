from aws_cdk import (
    # Duration,
    CfnOutput,
    RemovalPolicy,
    Stack,
    aws_s3 as s3,
    # aws_sqs as sqs,
)
from constructs import Construct

class CdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # S3 bucket construct
        bucket = s3.Bucket(
            self, "MyBucket",
            versioned=True,
            bucket_name="my-bucket-with-iac-cdk-fboetti", 
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,

            # Next two args are Course/dev only: delete the bucket on `cdk destroy` even if it holds objects.
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Stack output: the bucket name is printed after `cdk deploy` (and visible in CloudFormation).
        CfnOutput(
            self, "BucketName",
            value=bucket.bucket_name,
            description="Name of the S3 bucket created by the stack",
            export_name="MyBucketName",
        )

        # example resource
        # queue = sqs.Queue(
        #     self, "CdkQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )
