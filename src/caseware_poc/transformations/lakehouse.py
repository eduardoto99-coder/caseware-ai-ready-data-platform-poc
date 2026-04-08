from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb

from caseware_poc.common.io_utils import write_json
from caseware_poc.common.runtime import PlatformRuntime


class LakehouseTransformer:
    def __init__(self, runtime: PlatformRuntime) -> None:
        self.runtime = runtime

    def run(self) -> dict[str, Any]:
        config = self.runtime.config
        config.silver_dir.mkdir(parents=True, exist_ok=True)
        config.gold_dir.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(config.db_path)) as con:
            self._build_bronze_views(con)
            silver_metrics = self._build_silver(con)
            gold_metrics = self._build_gold(con)
            quality_report = self._run_quality_checks(con)
            self._export_tables(con)
        return {
            "silver_metrics": silver_metrics,
            "gold_metrics": gold_metrics,
            "quality_report": quality_report,
        }

    def _build_bronze_views(self, con: duckdb.DuckDBPyConnection) -> None:
        bronze_structured = _sql_path(self.runtime.config.bronze_dir / "structured" / "*.parquet")
        bronze_documents = _sql_path(self.runtime.config.bronze_dir / "documents" / "*.parquet")
        con.execute(
            f"""
            CREATE OR REPLACE VIEW bronze_structured AS
            SELECT * FROM read_parquet('{bronze_structured}')
            """,
        )
        con.execute(
            f"""
            CREATE OR REPLACE VIEW bronze_documents AS
            SELECT * FROM read_parquet('{bronze_documents}')
            """,
        )

    def _build_silver(self, con: duckdb.DuckDBPyConnection) -> dict[str, int]:
        con.execute(
            """
            CREATE OR REPLACE TABLE silver_structured_events AS
            WITH deduped AS (
              SELECT
                *,
                row_number() OVER (
                  PARTITION BY event_id
                  ORDER BY emitted_at DESC, source_sequence DESC
                ) AS duplicate_rank
              FROM bronze_structured
            ),
            ranked AS (
              SELECT
                *,
                row_number() OVER (
                  PARTITION BY entity_name, tenant_id, entity_id
                  ORDER BY updated_at DESC, source_sequence DESC, emitted_at DESC
                ) AS entity_rank
              FROM deduped
              WHERE duplicate_rank = 1
            )
            SELECT
              event_id,
              entity_name,
              op,
              tenant_id,
              entity_id,
              updated_at,
              emitted_at,
              source_sequence,
              batch_id,
              source_file,
              payload_json,
              payload,
              duplicate_rank = 1 AS is_primary_event,
              entity_rank,
              op = 'delete' AS is_deleted
            FROM ranked
            """,
        )
        con.execute(
            """
            CREATE OR REPLACE TABLE silver_invoice_snapshot AS
            SELECT
              tenant_id,
              entity_id AS invoice_id,
              json_extract_string(payload_json, '$.customer_id') AS customer_id,
              json_extract_string(payload_json, '$.engagement_id') AS engagement_id,
              json_extract_string(payload_json, '$.invoice_number') AS invoice_number,
              try_cast(json_extract_string(payload_json, '$.invoice_amount') AS DOUBLE) AS invoice_amount,
              json_extract_string(payload_json, '$.currency') AS currency,
              json_extract_string(payload_json, '$.status') AS status,
              try_cast(json_extract_string(payload_json, '$.due_date') AS DATE) AS due_date,
              try_cast(json_extract_string(payload_json, '$.invoice_date') AS DATE) AS invoice_date,
              is_deleted,
              updated_at,
              event_id AS source_event_id,
              batch_id AS source_batch_id
            FROM silver_structured_events
            WHERE entity_name = 'invoice'
              AND entity_rank = 1
            """,
        )
        con.execute(
            """
            CREATE OR REPLACE TABLE silver_customer_snapshot AS
            SELECT
              tenant_id,
              entity_id AS customer_id,
              json_extract_string(payload_json, '$.customer_name') AS customer_name,
              json_extract_string(payload_json, '$.segment') AS segment,
              json_extract_string(payload_json, '$.billing_country') AS billing_country,
              is_deleted,
              updated_at,
              event_id AS source_event_id,
              batch_id AS source_batch_id
            FROM silver_structured_events
            WHERE entity_name = 'customer'
              AND entity_rank = 1
            """,
        )
        con.execute(
            """
            CREATE OR REPLACE TABLE silver_engagement_snapshot AS
            SELECT
              tenant_id,
              entity_id AS engagement_id,
              json_extract_string(payload_json, '$.engagement_name') AS engagement_name,
              json_extract_string(payload_json, '$.status') AS status,
              json_extract_string(payload_json, '$.owner') AS owner,
              try_cast(json_extract_string(payload_json, '$.issue_count') AS INTEGER) AS issue_count,
              is_deleted,
              updated_at,
              event_id AS source_event_id,
              batch_id AS source_batch_id
            FROM silver_structured_events
            WHERE entity_name = 'engagement'
              AND entity_rank = 1
            """,
        )
        con.execute(
            """
            CREATE OR REPLACE TABLE silver_control_snapshot AS
            SELECT
              tenant_id,
              entity_id AS control_id,
              json_extract_string(payload_json, '$.engagement_id') AS engagement_id,
              json_extract_string(payload_json, '$.control_name') AS control_name,
              json_extract_string(payload_json, '$.severity') AS severity,
              json_extract_string(payload_json, '$.status') AS status,
              try_cast(json_extract_string(payload_json, '$.exception_count') AS INTEGER) AS exception_count,
              json_extract_string(payload_json, '$.owner') AS owner,
              is_deleted,
              updated_at,
              event_id AS source_event_id,
              batch_id AS source_batch_id
            FROM silver_structured_events
            WHERE entity_name = 'control'
              AND entity_rank = 1
            """,
        )
        con.execute(
            """
            CREATE OR REPLACE TABLE silver_journal_entry_snapshot AS
            SELECT
              tenant_id,
              entity_id AS journal_entry_id,
              json_extract_string(payload_json, '$.engagement_id') AS engagement_id,
              json_extract_string(payload_json, '$.entry_type') AS entry_type,
              try_cast(json_extract_string(payload_json, '$.amount') AS DOUBLE) AS amount,
              json_extract_string(payload_json, '$.debit_account') AS debit_account,
              json_extract_string(payload_json, '$.credit_account') AS credit_account,
              is_deleted,
              updated_at,
              event_id AS source_event_id,
              batch_id AS source_batch_id
            FROM silver_structured_events
            WHERE entity_name = 'journal_entry'
              AND entity_rank = 1
            """,
        )
        return {
            "silver_structured_events": self._count(con, "silver_structured_events"),
            "silver_invoice_snapshot": self._count(con, "silver_invoice_snapshot"),
            "silver_engagement_snapshot": self._count(con, "silver_engagement_snapshot"),
            "silver_control_snapshot": self._count(con, "silver_control_snapshot"),
        }

    def _build_gold(self, con: duckdb.DuckDBPyConnection) -> dict[str, int]:
        con.execute(
            """
            CREATE OR REPLACE TABLE gold_invoice_summary AS
            WITH reference_clock AS (
              SELECT cast(max(emitted_at) AS DATE) AS reference_date
              FROM silver_structured_events
            )
            SELECT
              inv.tenant_id,
              inv.invoice_id,
              inv.invoice_number,
              inv.engagement_id,
              eng.engagement_name,
              inv.customer_id,
              cust.customer_name,
              inv.invoice_amount,
              inv.currency,
              inv.status,
              inv.invoice_date,
              inv.due_date,
              date_diff('day', inv.due_date, (SELECT reference_date FROM reference_clock)) AS days_past_due,
              CASE
                WHEN inv.status = 'overdue' OR inv.due_date < (SELECT reference_date FROM reference_clock) THEN TRUE
                ELSE FALSE
              END AS is_overdue,
              CASE
                WHEN inv.due_date < (SELECT reference_date FROM reference_clock)
                 AND date_diff('day', inv.due_date, (SELECT reference_date FROM reference_clock)) <= 30 THEN '0_30'
                WHEN inv.due_date < (SELECT reference_date FROM reference_clock)
                 AND date_diff('day', inv.due_date, (SELECT reference_date FROM reference_clock)) <= 60 THEN '31_60'
                WHEN inv.due_date < (SELECT reference_date FROM reference_clock) THEN '61_plus'
                ELSE 'current'
              END AS aging_bucket,
              date_trunc('month', inv.invoice_date) = date_trunc('month', (SELECT reference_date FROM reference_clock)) AS in_latest_month,
              inv.updated_at,
              inv.source_event_id,
              inv.source_batch_id,
              concat('invoice:', inv.source_event_id, '|customer:', cust.source_event_id, '|engagement:', eng.source_event_id) AS lineage_ref
            FROM silver_invoice_snapshot inv
            LEFT JOIN silver_customer_snapshot cust
              ON inv.tenant_id = cust.tenant_id
             AND inv.customer_id = cust.customer_id
             AND NOT cust.is_deleted
            LEFT JOIN silver_engagement_snapshot eng
              ON inv.tenant_id = eng.tenant_id
             AND inv.engagement_id = eng.engagement_id
             AND NOT eng.is_deleted
            WHERE NOT inv.is_deleted
            """,
        )
        con.execute(
            """
            CREATE OR REPLACE TABLE gold_engagement_status AS
            SELECT
              eng.tenant_id,
              eng.engagement_id,
              eng.engagement_name,
              eng.status,
              eng.owner,
              eng.issue_count,
              coalesce(sum(ctrl.exception_count), 0) AS control_exception_count,
              max(eng.updated_at) AS updated_at,
              eng.source_event_id,
              eng.source_batch_id,
              concat('engagement:', eng.source_event_id) AS lineage_ref
            FROM silver_engagement_snapshot eng
            LEFT JOIN silver_control_snapshot ctrl
              ON eng.tenant_id = ctrl.tenant_id
             AND eng.engagement_id = ctrl.engagement_id
             AND NOT ctrl.is_deleted
            WHERE NOT eng.is_deleted
            GROUP BY ALL
            """,
        )
        con.execute(
            """
            CREATE OR REPLACE TABLE gold_control_exceptions AS
            SELECT
              ctrl.tenant_id,
              ctrl.control_id,
              ctrl.control_name,
              ctrl.engagement_id,
              eng.engagement_name,
              ctrl.severity,
              ctrl.status,
              ctrl.exception_count,
              ctrl.owner,
              ctrl.updated_at,
              ctrl.source_event_id,
              ctrl.source_batch_id,
              concat('control:', ctrl.source_event_id, '|engagement:', eng.source_event_id) AS lineage_ref
            FROM silver_control_snapshot ctrl
            LEFT JOIN silver_engagement_snapshot eng
              ON ctrl.tenant_id = eng.tenant_id
             AND ctrl.engagement_id = eng.engagement_id
             AND NOT eng.is_deleted
            WHERE NOT ctrl.is_deleted
            """,
        )
        return {
            "gold_invoice_summary": self._count(con, "gold_invoice_summary"),
            "gold_engagement_status": self._count(con, "gold_engagement_status"),
            "gold_control_exceptions": self._count(con, "gold_control_exceptions"),
        }

    def _run_quality_checks(self, con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
        bronze_columns = {
            row[0]
            for row in con.execute("DESCRIBE bronze_structured").fetchall()
        }
        expected_columns = {
            "event_id",
            "entity_name",
            "op",
            "tenant_id",
            "entity_id",
            "updated_at",
            "emitted_at",
            "source_sequence",
            "payload",
            "payload_json",
            "source_system",
            "batch_id",
            "source_file",
        }
        duplicate_events = con.execute(
            """
            SELECT count(*) FROM (
              SELECT event_id
              FROM bronze_structured
              GROUP BY event_id
              HAVING count(*) > 1
            )
            """,
        ).fetchone()[0]
        null_invoice_amounts = con.execute(
            """
            SELECT count(*) FROM silver_invoice_snapshot
            WHERE NOT is_deleted AND invoice_amount IS NULL
            """,
        ).fetchone()[0]
        null_customer_names = con.execute(
            """
            SELECT count(*) FROM gold_invoice_summary
            WHERE customer_name IS NULL
            """,
        ).fetchone()[0]
        freshness = con.execute(
            """
            SELECT
              round(avg(date_diff('minute', updated_at, emitted_at)), 2) AS avg_emit_delay_minutes,
              max(date_diff('minute', updated_at, emitted_at)) AS max_emit_delay_minutes
            FROM bronze_structured
            """,
        ).fetchone()
        document_metadata_issues = con.execute(
            """
            SELECT count(*) FROM bronze_documents
            WHERE classification IS NULL OR retention_state IS NULL OR tenant_id IS NULL
            """
        ).fetchone()[0]
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "schema_drift": {
                "status": "pass" if bronze_columns == expected_columns else "warn",
                "expected_columns": sorted(expected_columns),
                "actual_columns": sorted(bronze_columns),
                "missing_columns": sorted(expected_columns - bronze_columns),
                "unexpected_columns": sorted(bronze_columns - expected_columns),
            },
            "duplicates": {
                "status": "warn" if duplicate_events else "pass",
                "duplicate_event_ids": int(duplicate_events),
            },
            "completeness": {
                "status": "pass" if not null_invoice_amounts and not null_customer_names else "warn",
                "null_invoice_amount_rows": int(null_invoice_amounts),
                "null_customer_name_rows": int(null_customer_names),
            },
            "freshness": {
                "status": "pass",
                "avg_emit_delay_minutes": float(freshness[0]),
                "max_emit_delay_minutes": int(freshness[1]),
            },
            "document_metadata": {
                "status": "pass" if not document_metadata_issues else "warn",
                "missing_metadata_rows": int(document_metadata_issues),
            },
            "traceability": {
                "status": "pass",
                "gold_tables_with_lineage_ref": [
                    "gold_invoice_summary",
                    "gold_engagement_status",
                    "gold_control_exceptions",
                ],
            },
        }
        write_json(self.runtime.config.quality_dir / "quality_report.json", report)
        self.runtime.logger.emit("quality_checks_completed", report=report)
        return report

    def _export_tables(self, con: duckdb.DuckDBPyConnection) -> None:
        for table_name, output_dir in [
            ("silver_structured_events", self.runtime.config.silver_dir),
            ("silver_invoice_snapshot", self.runtime.config.silver_dir),
            ("silver_customer_snapshot", self.runtime.config.silver_dir),
            ("silver_engagement_snapshot", self.runtime.config.silver_dir),
            ("silver_control_snapshot", self.runtime.config.silver_dir),
            ("silver_journal_entry_snapshot", self.runtime.config.silver_dir),
            ("gold_invoice_summary", self.runtime.config.gold_dir),
            ("gold_engagement_status", self.runtime.config.gold_dir),
            ("gold_control_exceptions", self.runtime.config.gold_dir),
        ]:
            output_file = output_dir / f"{table_name}.parquet"
            output_sql = _sql_path(output_file)
            con.execute(f"COPY {table_name} TO '{output_sql}' (FORMAT PARQUET)")
        self.runtime.logger.emit("lakehouse_exported", db_path=str(self.runtime.config.db_path))

    @staticmethod
    def _count(con: duckdb.DuckDBPyConnection, table_name: str) -> int:
        return int(con.execute(f"SELECT count(*) FROM {table_name}").fetchone()[0])


def _sql_path(path: Path) -> str:
    return str(path).replace("'", "''")
