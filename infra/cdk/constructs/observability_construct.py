from __future__ import annotations

from constructs import Construct
from aws_cdk import Duration
from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk import aws_logs as logs
from aws_cdk import aws_ssm as ssm


class ObservabilityConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)
        self.app_log_group = logs.LogGroup(self, "PlatformLogGroup")
        self.guardrail_alarm = cloudwatch.Alarm(
            self,
            "GuardrailBypassAlarm",
            metric=cloudwatch.Metric(
                namespace="CasewarePlatform",
                metric_name="GuardrailBypassAttempts",
                period=Duration.minutes(5),
                statistic="sum",
            ),
            threshold=1,
            evaluation_periods=1,
        )
        ssm.StringParameter(
            self,
            "NewRelicLicenseKeySecretReference",
            parameter_name="/caseware/platform/newrelic/license-key-secret-name",
            string_value="newrelic-license-key",
        )
