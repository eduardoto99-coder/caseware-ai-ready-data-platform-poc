#!/usr/bin/env python3
from aws_cdk import App, Environment

from stacks.platform_stack import CasewarePlatformStack


app = App()
CasewarePlatformStack(
    app,
    "CasewarePlatformStack",
    env=Environment(account="111111111111", region="us-east-1"),
)
app.synth()
