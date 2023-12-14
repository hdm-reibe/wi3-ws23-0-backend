import aws_cdk as cdk
from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct


def create(construct: Construct) -> dynamodb.Table:
    """This function creates a DynamoDB table for storing shortened URLs.

    :return: DynamoDB table
    """

    table = dynamodb.Table(
        construct,
        id="shortened_urls",
        table_name="shortened_urls",
        partition_key=dynamodb.Attribute(
            name="id",
            type=dynamodb.AttributeType.STRING
        ),
        deletion_protection=False,
        stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,  # important!
        removal_policy=cdk.RemovalPolicy.DESTROY
    )

    # add Index owner-index
    table.add_global_secondary_index(
        index_name="owner-index",
        partition_key=dynamodb.Attribute(
            name="owner",
            type=dynamodb.AttributeType.STRING
        ),
        projection_type=dynamodb.ProjectionType.ALL
    )

    return table
