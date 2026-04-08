from __future__ import annotations

from constructs import Construct
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_eks as eks


class ServingConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str, *, vpc: ec2.IVpc) -> None:
        super().__init__(scope, construct_id)
        self.cluster = eks.Cluster(
            self,
            "CasewareEksCluster",
            version=eks.KubernetesVersion.V1_31,
            vpc=vpc,
            default_capacity=2,
            cluster_name="caseware-platform-eks",
        )
        self.cluster.add_helm_chart(
            "TrinoChart",
            repository="https://trinodb.github.io/charts",
            chart="trino",
            namespace="analytics",
            values={
                "server": {"workers": 3},
                "catalogs": {
                    "iceberg": """
connector.name=iceberg
iceberg.catalog.type=glue
hive.metastore.glue.region=us-east-1
"""
                },
            },
        )
        self.cluster.add_helm_chart(
            "SparkOperator",
            repository="https://kubeflow.github.io/spark-operator",
            chart="spark-operator",
            namespace="spark",
        )
