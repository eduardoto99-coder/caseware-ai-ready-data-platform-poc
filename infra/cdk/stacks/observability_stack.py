from __future__ import annotations

from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_cloudwatch as cloudwatch,
    aws_logs as logs,
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct


class ObservabilityStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.llm_log_group = logs.LogGroup(
            self,
            "LlmProxyLogGroup",
            log_group_name="/caseware/ai/llm-proxy",
            retention=logs.RetentionDays.ONE_MONTH,
        )
        pipeline_log_group = logs.LogGroup(
            self,
            "PipelineLogGroup",
            log_group_name="/caseware/data/pipelines",
            retention=logs.RetentionDays.ONE_MONTH,
        )

        cloudwatch.Dashboard(
            self,
            "CasewareAiDataPlatformDashboard",
            dashboard_name="caseware-ai-data-platform",
            widgets=[
                [
                    cloudwatch.GraphWidget(
                        title="Pipeline Freshness and Failures",
                        left=[
                            cloudwatch.Metric(namespace="Caseware/DataPlatform", metric_name="FreshnessLagMinutes"),
                            cloudwatch.Metric(namespace="Caseware/DataPlatform", metric_name="PipelineFailures"),
                        ],
                    )
                ],
                [
                    cloudwatch.GraphWidget(
                        title="LLM Guardrail and Retrieval Metrics",
                        left=[
                            cloudwatch.Metric(namespace="Caseware/AI", metric_name="GuardrailInvocations"),
                            cloudwatch.Metric(namespace="Caseware/AI", metric_name="RetrievalLatencyMs"),
                            cloudwatch.Metric(namespace="Caseware/AI", metric_name="CitationMisses"),
                        ],
                    )
                ],
            ],
        )

        cloudwatch.Alarm(
            self,
            "FreshnessAlarm",
            metric=cloudwatch.Metric(namespace="Caseware/DataPlatform", metric_name="FreshnessLagMinutes"),
            threshold=30,
            evaluation_periods=1,
            datapoints_to_alarm=1,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        secretsmanager.Secret(
            self,
            "NewRelicLicenseKey",
            secret_name="caseware/newrelic/license-key",
        )
        secretsmanager.Secret(
            self,
            "LangfuseKeys",
            secret_name="caseware/langfuse/keys",
        )

        CfnOutput(self, "LlmLogGroupName", value=self.llm_log_group.log_group_name)
        CfnOutput(self, "PipelineLogGroupName", value=pipeline_log_group.log_group_name)
