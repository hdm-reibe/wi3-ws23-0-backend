import aws_cdk as cdk

from backend.backend_stack import BackendStack

app = cdk.App()

BackendStack(app, "backend-stack")

app.synth()
