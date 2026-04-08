from __future__ import annotations

from constructs import Construct
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_logs as logs
from aws_cdk import aws_msk as msk


class StreamingConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str, *, vpc: ec2.IVpc) -> None:
        super().__init__(scope, construct_id)
        self.kafka_logs = logs.LogGroup(self, "KafkaBrokerLogs")
        self.cluster = msk.CfnServerlessCluster(
            self,
            "CasewareMskServerlessCluster",
            cluster_name="caseware-cdc-stream",
            vpc_configs=[
                msk.CfnServerlessCluster.VpcConfigProperty(
                    subnet_ids=vpc.private_subnets[:2],
                    security_groups=[],
                )
            ],
            client_authentication=msk.CfnServerlessCluster.ClientAuthenticationProperty(
                sasl=msk.CfnServerlessCluster.SaslProperty(iam=msk.CfnServerlessCluster.IamProperty(enabled=True))
            ),
        )
