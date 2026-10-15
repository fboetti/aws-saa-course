"""Minimal S3 client built with boto3.

Creates the bucket named BUCKET_NAME in the configured region.

Usage:
    python3 sdk/python/s3.py
"""

import os

import boto3
from botocore.exceptions import ClientError

BUCKET_NAME = "my-test-bucket-fboetti"
REGION = os.environ.get("AWS_DEFAULT_REGION", "eu-north-1")


def get_s3_client(region: str = REGION):
    """Return an S3 client using the ambient AWS credentials."""
    return boto3.client("s3", region_name=region)


def create_bucket(s3, bucket_name: str = BUCKET_NAME, region: str = REGION) -> str:
    """Create `bucket_name` and return its ARN."""
    kwargs = {"Bucket": bucket_name}
    # us-east-1 is the default region and rejects the LocationConstraint.
    if region != "us-east-1":
        kwargs["CreateBucketConfiguration"] = {"LocationConstraint": region}

    try:
        s3.create_bucket(**kwargs)
    except ClientError as err:
        code = err.response.get("Error", {}).get("Code", "")
        if code in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            # BucketAlreadyExists: owned by someone else, BucketAlreadyOwnedByYou: ours.
            if code == "BucketAlreadyOwnedByYou":
                print(f"Bucket already exists: {bucket_name} ({region})")
                return f"arn:aws:s3:::{bucket_name}"
            raise
        raise

    print(f"Created bucket: {bucket_name} ({region})")
    return f"arn:aws:s3:::{bucket_name}"


def main() -> None:
    s3 = get_s3_client()
    create_bucket(s3)


if __name__ == "__main__":
    main()
