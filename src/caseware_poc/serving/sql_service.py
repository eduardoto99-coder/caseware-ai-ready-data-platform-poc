from __future__ import annotations

from dataclasses import dataclass

import duckdb

from caseware_poc.common.models import QueryResponse, RouteDecision
from caseware_poc.common.runtime import PlatformRuntime


@dataclass(slots=True)
class SqlPlan:
    sql: str
    description: str


class StructuredQueryService:
    def __init__(self, runtime: PlatformRuntime) -> None:
        self.runtime = runtime

    def answer(self, *, tenant_id: str, question: str, route: RouteDecision) -> QueryResponse:
        plan = self._plan(question)
        with duckdb.connect(str(self.runtime.config.db_path), read_only=True) as con:
            cursor = con.execute(plan.sql, [tenant_id])
            columns = [item[0] for item in cursor.description]
            rows = cursor.fetchall()
        records = [dict(zip(columns, row)) for row in rows]
        answer = self._render_answer(plan.description, records)
        self.runtime.logger.emit(
            "sql_answer_completed",
            tenant_id=tenant_id,
            question=question,
            route=route.route,
            sql=plan.sql,
            record_count=len(records),
        )
        return QueryResponse(
            tenant_id=tenant_id,
            question=question,
            route=route,
            answer=answer,
            sql=plan.sql,
            records=records,
        )

    def _plan(self, question: str) -> SqlPlan:
        normalized = question.lower()
        if "overdue" in normalized and ("invoice" in normalized or "amount" in normalized or "total" in normalized):
            return SqlPlan(
                description="Total overdue invoice amount in the latest reference month.",
                sql="""
                SELECT
                  tenant_id,
                  sum(invoice_amount) AS total_overdue_amount,
                  count(*) AS overdue_invoice_count
                FROM gold_invoice_summary
                WHERE tenant_id = ?
                  AND is_overdue
                  AND in_latest_month
                GROUP BY tenant_id
                """,
            )
        if "control" in normalized and "exception" in normalized:
            return SqlPlan(
                description="Open control exceptions for the tenant.",
                sql="""
                SELECT
                  tenant_id,
                  control_id,
                  control_name,
                  engagement_name,
                  severity,
                  status,
                  exception_count,
                  lineage_ref
                FROM gold_control_exceptions
                WHERE tenant_id = ?
                  AND exception_count > 0
                ORDER BY exception_count DESC, severity DESC
                """,
            )
        if "engagement" in normalized and "status" in normalized:
            return SqlPlan(
                description="Engagement status summary for the tenant.",
                sql="""
                SELECT
                  tenant_id,
                  engagement_id,
                  engagement_name,
                  status,
                  owner,
                  issue_count,
                  control_exception_count,
                  lineage_ref
                FROM gold_engagement_status
                WHERE tenant_id = ?
                ORDER BY engagement_name
                """,
            )
        return SqlPlan(
            description="Invoice summary detail for the tenant.",
            sql="""
            SELECT
              tenant_id,
              invoice_id,
              invoice_number,
              customer_name,
              invoice_amount,
              status,
              is_overdue,
              aging_bucket,
              lineage_ref
            FROM gold_invoice_summary
            WHERE tenant_id = ?
            ORDER BY invoice_number
            """,
        )

    @staticmethod
    def _render_answer(description: str, records: list[dict]) -> str:
        if not records:
            return f"{description} No rows matched the tenant-scoped query."
        first = records[0]
        if "total_overdue_amount" in first:
            amount = round(float(first["total_overdue_amount"]), 2)
            count = int(first["overdue_invoice_count"])
            return f"Found {count} overdue invoices totaling {amount:.2f} for the tenant in the latest reference month."
        if "control_id" in first:
            return f"Found {len(records)} control exceptions in the curated gold table."
        if "engagement_id" in first:
            return f"Found {len(records)} engagement status rows in the gold serving layer."
        return f"Returned {len(records)} structured rows from the gold serving layer."
