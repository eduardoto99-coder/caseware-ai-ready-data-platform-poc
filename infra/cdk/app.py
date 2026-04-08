#!/usr/bin/env python3
from aws_cdk import App, Environment

from stacks.ai_platform_stack import AiPlatformStack
from stacks.data_platform_stack import DataPlatformStack
from stacks.observability_stack import ObservabilityStack


app = App()
environment = Environment(account="111111111111", region="us-east-1")

data_platform = DataPlatformStack(
    app,
    "CasewareDataPlatformStack",
    env=environment,
)
observability = ObservabilityStack(
    app,
    "CasewareObservabilityStack",
    env=environment,
)
AiPlatformStack(
    app,
    "CasewareAiPlatformStack",
    lakehouse_bucket=data_platform.lakehouse_bucket,
    llm_proxy_namespace="ai-platform",
    observability_log_group=observability.llm_log_group,
    env=environment,
)
app.synth()
