from __future__ import annotations

from constructs import Construct
from aws_cdk import RemovalPolicy
from aws_cdk import aws_glue as glue
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lakeformation as lakeformation
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_emrserverless as emrserverless


class LakehouseConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)
        self.raw_bucket = s3.Bucket(
            self,
            "RawBucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=True,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        self.warehouse_bucket = s3.Bucket(
            self,
            "WarehouseBucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=True,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        self.glue_database = glue.CfnDatabase(
            self,
            "LakehouseDatabase",
            catalog_id=self.node.try_get_context("account_id") or "111111111111",
            database_input=glue.CfnDatabase.DatabaseInputProperty(name="caseware"),
        )
        self.lf_admin_role = iam.Role(
            self,
            "LakeFormationAdminRole",
            assumed_by=iam.ServicePrincipal("lakeformation.amazonaws.com"),
        )
        lakeformation.CfnResource(
            self,
            "WarehouseResourceRegistration",
            resource_arn=self.warehouse_bucket.bucket_arn,
            role_arn=self.lf_admin_role.role_arn,
        )
        self.emr_application = emrserverless.CfnApplication(
            self,
            "SparkServerlessApp",
            release_label="emr-7.3.0",
            type="SPARK",
            name="caseware-iceberg-spark",
        )
