import os
import boto3


AWS_ENDPOINT_URL = os.getenv(
    "AWS_ENDPOINT_URL",
    "http://localhost:4566"
)

AWS_REGION = os.getenv(
    "AWS_DEFAULT_REGION",
    "us-east-1"
)


def get_route53_client():
    return boto3.client(
        "route53",
        endpoint_url=AWS_ENDPOINT_URL,
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv(
            "AWS_ACCESS_KEY_ID",
            "test"
        ),
        aws_secret_access_key=os.getenv(
            "AWS_SECRET_ACCESS_KEY",
            "test"
        )
    )