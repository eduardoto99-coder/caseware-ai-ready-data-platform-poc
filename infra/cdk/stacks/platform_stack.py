from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

from constructs.lakehouse_construct import LakehouseConstruct
from constructs.observability_construct import ObservabilityConstruct
from constructs.search_ai_construct import SearchAndAiConstruct
from constructs.serving_construct import ServingConstruct
from constructs.streaming_construct import StreamingConstruct


class CasewarePlatformStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        vpc = ec2.Vpc(self, "CasewareVpc", max_azs=2)
        self.lakehouse = LakehouseConstruct(self, "Lakehouse")
        self.streaming = StreamingConstruct(self, "Streaming", vpc=vpc)
        self.search_ai = SearchAndAiConstruct(self, "SearchAndAi", vpc=vpc)
        self.serving = ServingConstruct(self, "Serving", vpc=vpc)
        self.observability = ObservabilityConstruct(self, "Observability")
