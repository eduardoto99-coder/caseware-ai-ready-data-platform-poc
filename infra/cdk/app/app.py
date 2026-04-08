from __future__ import annotations

from aws_cdk import App

from infra.cdk.config.platform_config import ReferencePlatformConfig
from infra.cdk.stacks.reference_platform_stack import ReferencePlatformStack


app = App()
config = ReferencePlatformConfig()
ReferencePlatformStack(app, "CasewareAiReadyPlatformReferenceStack", config=config)
app.synth()
