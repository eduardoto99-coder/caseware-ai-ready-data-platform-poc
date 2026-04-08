from __future__ import annotations

from constructs import Construct
from aws_cdk import CfnResource
from aws_cdk import aws_iam as iam
from aws_cdk import aws_opensearchserverless as aoss
from aws_cdk import aws_rds as rds
from aws_cdk import aws_ec2 as ec2
from aws_cdk import SecretValue


class SearchAndAiConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str, *, vpc: ec2.IVpc) -> None:
        super().__init__(scope, construct_id)
        self.vector_collection = aoss.CfnCollection(
            self,
            "VectorCollection",
            name="caseware-vector-search",
            type="VECTORSEARCH",
        )
        aoss.CfnSecurityPolicy(
            self,
            "VectorEncryptionPolicy",
            name="caseware-vector-encryption",
            type="encryption",
            policy='{"Rules":[{"ResourceType":"collection","Resource":["collection/caseware-vector-search"]}],"AWSOwnedKey":true}',
        )
        aoss.CfnAccessPolicy(
            self,
            "VectorAccessPolicy",
            name="caseware-vector-access",
            type="data",
            policy='[{"Rules":[{"ResourceType":"index","Resource":["index/caseware-vector-search/*"],"Permission":["aoss:*"]}],"Principal":["arn:aws:iam::111111111111:role/CasewarePlatformRole"]}]',
        )
        self.postgres = rds.DatabaseCluster(
            self,
            "AuroraPostgresCluster",
            engine=rds.DatabaseClusterEngine.aurora_postgres(version=rds.AuroraPostgresEngineVersion.VER_16_3),
            writer=rds.ClusterInstance.serverless_v2("writer"),
            readers=[rds.ClusterInstance.serverless_v2("reader")],
            vpc=vpc,
            credentials=rds.Credentials.from_password(
                username="caseware_admin",
                password=SecretValue.unsafe_plain_text("change-me-in-secrets-manager"),
            ),
            default_database_name="caseware_platform",
        )
        self.bedrock_gateway_role = iam.Role(
            self,
            "BedrockGatewayRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess")],
        )
        CfnResource(
            self,
            "BedrockKnowledgeBase",
            type="AWS::Bedrock::KnowledgeBase",
            properties={
                "Name": "caseware-tenant-kb",
                "KnowledgeBaseConfiguration": {"Type": "VECTOR"},
                "RoleArn": self.bedrock_gateway_role.role_arn,
                "StorageConfiguration": {
                    "Type": "OPENSEARCH_SERVERLESS",
                    "OpensearchServerlessConfiguration": {
                        "CollectionArn": self.vector_collection.attr_arn,
                        "VectorIndexName": "tenant-documents",
                        "FieldMapping": {
                            "MetadataField": "metadata",
                            "TextField": "content",
                            "VectorField": "embedding",
                        },
                    },
                },
            },
        )
