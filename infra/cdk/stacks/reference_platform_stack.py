from __future__ import annotations

from aws_cdk import CfnOutput, Environment, Stack
from constructs import Construct

from infra.cdk.config.platform_config import ReferencePlatformConfig
from infra.cdk.constructs.lakehouse_construct import LakehouseConstruct
from infra.cdk.constructs.search_and_serving_construct import SearchAndServingConstruct
from infra.cdk.constructs.streaming_construct import StreamingConstruct


class ReferencePlatformStack(Stack):
    """Single stack that surfaces the technologies emphasized by the role."""

    def __init__(self, scope: Construct, construct_id: str, *, config: ReferencePlatformConfig) -> None:
        super().__init__(
            scope,
            construct_id,
            env=Environment(account=config.account_id, region=config.region),
            description="Production-shaped AI-ready accounting data platform reference stack.",
        )

        self.lakehouse = LakehouseConstruct(self, "Lakehouse", config=config)
        self.streaming = StreamingConstruct(self, "Streaming", config=config)
        self.search_and_serving = SearchAndServingConstruct(self, "SearchAndServing", config=config)

        CfnOutput(self, "BronzeBucketName", value=self.lakehouse.bronze_bucket.bucket_name)
        CfnOutput(self, "GoldBucketName", value=self.lakehouse.gold_bucket.bucket_name)
        CfnOutput(self, "GlueDatabaseName", value=config.glue_database_name)
        CfnOutput(self, "KafkaClusterArn", value=self.streaming.kafka_cluster.attr_arn)
        CfnOutput(self, "AuroraClusterArn", value=self.search_and_serving.aurora_cluster.cluster_arn)
        CfnOutput(self, "OpenSearchCollectionArn", value=self.search_and_serving.search_collection.attr_arn)
        CfnOutput(self, "EksClusterName", value=self.search_and_serving.eks_cluster.cluster_name)
