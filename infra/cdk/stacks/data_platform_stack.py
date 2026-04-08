from __future__ import annotations

from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_athena as athena,
    aws_ec2 as ec2,
    aws_eks as eks,
    aws_emrserverless as emrserverless,
    aws_glue as glue,
    aws_iam as iam,
    aws_kms as kms,
    aws_msk as msk,
    aws_rds as rds,
    aws_s3 as s3,
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct


class DataPlatformStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        lakehouse_key = kms.Key(
            self,
            "LakehouseKey",
            enable_key_rotation=True,
        )
        self.lakehouse_bucket = s3.Bucket(
            self,
            "LakehouseBucket",
            bucket_name=f"caseware-lakehouse-{self.account}-{self.region}",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=lakehouse_key,
            versioned=True,
            enforce_ssl=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
        )
        script_bucket = s3.Bucket(
            self,
            "SparkScriptBucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=True,
            enforce_ssl=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
        )

        glue.CfnDatabase(
            self,
            "CasewareBronzeDatabase",
            catalog_id=self.account,
            database_input={"name": "caseware_bronze", "description": "Bronze Iceberg tables"},
        )
        glue.CfnDatabase(
            self,
            "CasewareSilverDatabase",
            catalog_id=self.account,
            database_input={"name": "caseware_silver", "description": "Silver Iceberg tables"},
        )
        glue.CfnDatabase(
            self,
            "CasewareGoldDatabase",
            catalog_id=self.account,
            database_input={"name": "caseware_gold", "description": "Gold data products"},
        )

        athena.CfnWorkGroup(
            self,
            "AthenaWorkgroup",
            name="caseware-governed-analytics",
            work_group_configuration=athena.CfnWorkGroup.WorkGroupConfigurationProperty(
                result_configuration=athena.CfnWorkGroup.ResultConfigurationProperty(
                    output_location=f"s3://{self.lakehouse_bucket.bucket_name}/athena-results/"
                ),
                publish_cloud_watch_metrics_enabled=True,
            ),
        )

        vpc = ec2.Vpc(
            self,
            "PlatformVpc",
            max_azs=2,
            nat_gateways=1,
        )

        emr_execution_role = iam.Role(
            self,
            "EmrServerlessExecutionRole",
            assumed_by=iam.ServicePrincipal("emr-serverless.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole"),
            ],
        )
        self.lakehouse_bucket.grant_read_write(emr_execution_role)
        script_bucket.grant_read(emr_execution_role)

        emrserverless.CfnApplication(
            self,
            "CasewareSparkApplication",
            name="caseware-iceberg-spark",
            release_label="emr-7.1.0",
            type="SPARK",
            maximum_capacity=emrserverless.CfnApplication.MaximumAllowedResourcesProperty(
                cpu="32 vCPU",
                memory="128 GB",
                disk="200 GB",
            ),
            network_configuration=emrserverless.CfnApplication.NetworkConfigurationProperty(
                subnet_ids=vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids,
                security_group_ids=[],
            ),
        )

        msk.CfnServerlessCluster(
            self,
            "CasewareMskServerless",
            cluster_name="caseware-cdc-msk",
            vpc_configs=[
                msk.CfnServerlessCluster.VpcConfigProperty(
                    subnet_ids=vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids
                )
            ],
            client_authentication=msk.CfnServerlessCluster.ClientAuthenticationProperty(
                sasl=msk.CfnServerlessCluster.SaslProperty(iam=msk.CfnServerlessCluster.IamProperty(enabled=True))
            ),
        )

        postgres_secret = secretsmanager.Secret(
            self,
            "AuroraPostgresSecret",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username":"caseware_admin"}',
                generate_string_key="password",
            ),
        )
        pg_cluster = rds.DatabaseCluster(
            self,
            "AuroraPostgresCluster",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_16_4
            ),
            writer=rds.ClusterInstance.provisioned("writer"),
            readers=[rds.ClusterInstance.serverless_v2("reader")],
            vpc=vpc,
            credentials=rds.Credentials.from_secret(postgres_secret),
            default_database_name="caseware_ai_serving",
            serverless_v2_min_capacity=0.5,
            serverless_v2_max_capacity=8,
            removal_policy=RemovalPolicy.DESTROY,
        )

        cluster = eks.Cluster(
            self,
            "PlatformEksCluster",
            version=eks.KubernetesVersion.V1_31,
            vpc=vpc,
            default_capacity=2,
            default_capacity_instance=ec2.InstanceType("m6i.large"),
        )

        CfnOutput(self, "LakehouseBucketName", value=self.lakehouse_bucket.bucket_name)
        CfnOutput(self, "SparkScriptBucketName", value=script_bucket.bucket_name)
        CfnOutput(self, "AuroraPostgresEndpoint", value=pg_cluster.cluster_endpoint.hostname)
        CfnOutput(self, "EksClusterName", value=cluster.cluster_name)
