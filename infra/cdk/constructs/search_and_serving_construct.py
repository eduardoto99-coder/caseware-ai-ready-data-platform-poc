from __future__ import annotations

from constructs import Construct

from aws_cdk import (
    RemovalPolicy,
    aws_ec2 as ec2,
    aws_eks as eks,
    aws_iam as iam,
    aws_logs as logs,
    aws_opensearchserverless as opensearchserverless,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
)

from infra.cdk.config.platform_config import ReferencePlatformConfig


class SearchAndServingConstruct(Construct):
    """Aurora PostgreSQL/pgvector, OpenSearch, EKS, CloudWatch, and secrets."""

    def __init__(self, scope: Construct, construct_id: str, *, config: ReferencePlatformConfig) -> None:
        super().__init__(scope, construct_id)

        self.vpc = ec2.Vpc(self, "PlatformVpc", max_azs=2, nat_gateways=1)

        self.pgvector_parameter_group = rds.ParameterGroup(
            self,
            "AuroraPgVectorParameterGroup",
            engine=rds.DatabaseClusterEngine.aurora_postgres(version=rds.AuroraPostgresEngineVersion.VER_16_3),
            parameters={
                "shared_preload_libraries": "vector,pg_stat_statements",
                "rds.force_ssl": "1",
            },
        )

        self.aurora_cluster = rds.DatabaseCluster(
            self,
            "AuroraPgVectorCluster",
            engine=rds.DatabaseClusterEngine.aurora_postgres(version=rds.AuroraPostgresEngineVersion.VER_16_3),
            writer=rds.ClusterInstance.serverless_v2("writer"),
            readers=[rds.ClusterInstance.serverless_v2("reader")],
            default_database_name=config.aurora_database_name,
            vpc=self.vpc,
            parameter_group=self.pgvector_parameter_group,
            removal_policy=RemovalPolicy.SNAPSHOT,
        )

        self.network_policy = opensearchserverless.CfnSecurityPolicy(
            self,
            "OpenSearchNetworkPolicy",
            name=f"{config.project}-{config.environment}-network",
            type="network",
            policy=f"""
            [
              {{
                "Rules": [
                  {{
                    "ResourceType": "collection",
                    "Resource": ["collection/{config.opensearch_collection_name}"]
                  }}
                ],
                "AllowFromPublic": false
              }}
            ]
            """,
        )
        self.encryption_policy = opensearchserverless.CfnSecurityPolicy(
            self,
            "OpenSearchEncryptionPolicy",
            name=f"{config.project}-{config.environment}-encryption",
            type="encryption",
            policy=f"""
            {{
              "Rules": [
                {{
                  "ResourceType": "collection",
                  "Resource": ["collection/{config.opensearch_collection_name}"]
                }}
              ],
              "AWSOwnedKey": true
            }}
            """,
        )
        self.search_collection = opensearchserverless.CfnCollection(
            self,
            "OpenSearchCollection",
            name=config.opensearch_collection_name,
            type="VECTORSEARCH",
            description="Tenant-aware vector and lexical search collection for audit documents.",
        )
        self.search_collection.add_dependency(self.network_policy)
        self.search_collection.add_dependency(self.encryption_policy)

        self.eks_cluster = eks.Cluster(
            self,
            "PlatformEksCluster",
            cluster_name=f"{config.project}-{config.environment}-eks",
            version=eks.KubernetesVersion.V1_31,
            vpc=self.vpc,
            default_capacity=0,
        )
        self.eks_cluster.add_nodegroup_capacity(
            "PlatformNodeGroup",
            desired_size=2,
            min_size=2,
            max_size=4,
            instance_types=[ec2.InstanceType("m7i.xlarge")],
        )

        self.cloudwatch_log_group = logs.LogGroup(
            self,
            "AiPlatformLogGroup",
            log_group_name=f"/caseware/{config.environment}/ai-platform",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY,
        )
        self.newrelic_license_secret = secretsmanager.Secret(
            self,
            "NewRelicLicenseSecret",
            secret_name=config.newrelic_secret_name,
            description="New Relic license key used by EKS workloads and background jobs.",
        )
        self.langfuse_secret = secretsmanager.Secret(
            self,
            "LangfuseSecret",
            secret_name=config.langfuse_secret_name,
            description="Langfuse public/private API keys for LLM tracing and evaluation.",
        )

        self.bedrock_runtime_role = iam.Role(
            self,
            "BedrockRuntimeRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
        )
        self.bedrock_runtime_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess")
        )
