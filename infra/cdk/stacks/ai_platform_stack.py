from __future__ import annotations

from aws_cdk import (
    CfnOutput,
    Stack,
    aws_bedrock as bedrock,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_logs as logs,
    aws_opensearchserverless as aoss,
    aws_s3 as s3,
)
from constructs import Construct


class AiPlatformStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        lakehouse_bucket: s3.IBucket,
        llm_proxy_namespace: str,
        observability_log_group: logs.ILogGroup,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vector_encryption_policy = aoss.CfnSecurityPolicy(
            self,
            "VectorEncryptionPolicy",
            name="caseware-vector-encryption",
            type="encryption",
            policy=f'{{"Rules":[{{"ResourceType":"collection","Resource":["collection/caseware-rag"]}}],"AWSOwnedKey":true}}',
        )
        vector_network_policy = aoss.CfnSecurityPolicy(
            self,
            "VectorNetworkPolicy",
            name="caseware-vector-network",
            type="network",
            policy='[{"Description":"Allow VPC and AWS services access","Rules":[{"ResourceType":"collection","Resource":["collection/caseware-rag"]}],"AllowFromPublic":false}]',
        )
        vector_collection = aoss.CfnCollection(
            self,
            "VectorCollection",
            name="caseware-rag",
            type="VECTORSEARCH",
        )
        vector_collection.add_dependency(vector_encryption_policy)
        vector_collection.add_dependency(vector_network_policy)

        aoss.CfnAccessPolicy(
            self,
            "VectorAccessPolicy",
            name="caseware-vector-access",
            type="data",
            policy=(
                '[{"Description":"Allow application access","Rules":[{"ResourceType":"index","Resource":["index/caseware-rag/*"],'
                '"Permission":["aoss:CreateIndex","aoss:UpdateIndex","aoss:ReadDocument","aoss:WriteDocument"]},'
                '{"ResourceType":"collection","Resource":["collection/caseware-rag"],"Permission":["aoss:DescribeCollectionItems"]}],'
                f'"Principal":["arn:aws:iam::{self.account}:root"]}}]'
            ),
        )

        llm_proxy_repository = ecr.Repository(
            self,
            "LlmProxyRepository",
            repository_name="caseware-llm-proxy",
            image_scan_on_push=True,
        )

        kb_role = iam.Role(
            self,
            "BedrockKnowledgeBaseRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
        )
        lakehouse_bucket.grant_read(kb_role)

        knowledge_base = bedrock.CfnKnowledgeBase(
            self,
            "CasewareKnowledgeBase",
            name="caseware-policy-kb",
            role_arn=kb_role.role_arn,
            knowledge_base_configuration=bedrock.CfnKnowledgeBase.KnowledgeBaseConfigurationProperty(
                type="VECTOR",
                vector_knowledge_base_configuration=bedrock.CfnKnowledgeBase.VectorKnowledgeBaseConfigurationProperty(
                    embedding_model_arn=f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v2:0"
                ),
            ),
            storage_configuration=bedrock.CfnKnowledgeBase.StorageConfigurationProperty(
                type="OPENSEARCH_SERVERLESS",
                opensearch_serverless_configuration=bedrock.CfnKnowledgeBase.OpenSearchServerlessConfigurationProperty(
                    collection_arn=vector_collection.attr_arn,
                    vector_index_name="caseware-policy-index",
                    field_mapping=bedrock.CfnKnowledgeBase.OpenSearchServerlessFieldMappingProperty(
                        metadata_field="metadata",
                        text_field="text",
                        vector_field="embedding",
                    ),
                ),
            ),
        )

        bedrock.CfnDataSource(
            self,
            "KnowledgeBaseSource",
            knowledge_base_id=knowledge_base.attr_knowledge_base_id,
            name="caseware-policy-datasource",
            data_source_configuration=bedrock.CfnDataSource.DataSourceConfigurationProperty(
                type="S3",
                s3_configuration=bedrock.CfnDataSource.S3DataSourceConfigurationProperty(
                    bucket_arn=lakehouse_bucket.bucket_arn,
                    inclusion_prefixes=["bronze/documents/"],
                ),
            ),
        )

        CfnOutput(self, "VectorCollectionArn", value=vector_collection.attr_arn)
        CfnOutput(self, "KnowledgeBaseId", value=knowledge_base.attr_knowledge_base_id)
        CfnOutput(self, "LlmProxyRepositoryName", value=llm_proxy_repository.repository_name)
        CfnOutput(self, "LlmProxyNamespace", value=llm_proxy_namespace)
        CfnOutput(self, "ObservabilityLogGroup", value=observability_log_group.log_group_name)
