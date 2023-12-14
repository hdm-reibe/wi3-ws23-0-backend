from aws_cdk import aws_iam as iam
from constructs import Construct


def create(construct: Construct, table_arn: str) -> iam.Role:
    """DynamoDB CRUD role for API Gateway

    :param table_arn: DynamoDB table ARN
    :return: IAM role
    """
    # create role for api gateway to access dynamodb
    return iam.Role(
        construct,
        id="api_gateway_dynamodb_list_role",
        assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
        inline_policies={
            "dynamodb": iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        actions=[
                            "dynamodb:Query"
                        ],
                        effect=iam.Effect.ALLOW,
                        resources=[f"{table_arn}/*"]
                    )
                ]
            )
        }
    )
