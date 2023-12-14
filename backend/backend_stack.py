from aws_cdk import Stack
from constructs import Construct

from resources import services


class BackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # add backend service
        services.BackendService(self, "BackendService")
