from __future__ import annotations

from pathlib import Path

import duckdb

from caseware_poc.common.io_utils import read_json
from caseware_poc.common.runtime import PlatformRuntime


class IngestionPipeline:
    def __init__(self, runtime: PlatformRuntime) -> None:
        self.runtime = runtime

    def ingest(self) -> dict[str, int]:
        structured_counts = self._ingest_structured()
        document_count = self._ingest_documents()
        return {
            "structured_records": structured_counts,
            "document_records": document_count,
        }

    def _ingest_structured(self) -> int:
        config = self.runtime.config
        batch_files = sorted((config.sample_data_dir / "events").glob("batch_*.jsonl"))
        record_count = 0
        for batch_file in batch_files:
            batch_id = batch_file.stem
            target_file = config.bronze_dir / "structured" / f"{batch_id}.parquet"
            target_file.parent.mkdir(parents=True, exist_ok=True)
            with duckdb.connect() as con:
                source_sql = _sql_path(batch_file)
                target_sql = _sql_path(target_file)
                con.execute(
                    f"""
                    COPY (
                      SELECT
                        *,
                        '{source_sql}' AS source_file
                      FROM read_json_auto('{source_sql}', records = true)
                    )
                    TO '{target_sql}'
                    (FORMAT PARQUET)
                    """,
                )
                batch_rows = con.execute(
                    f"SELECT count(*) FROM read_json_auto('{source_sql}', records = true)",
                ).fetchone()[0]
            record_count += int(batch_rows)
            self.runtime.logger.emit(
                "structured_bronze_ingested",
                batch_id=batch_id,
                source_file=str(batch_file),
                target_file=str(target_file),
                records=batch_rows,
            )
        return record_count

    def _ingest_documents(self) -> int:
        config = self.runtime.config
        docs_path = config.sample_data_dir / "documents" / "documents.json"
        target_file = config.bronze_dir / "documents" / "documents.parquet"
        target_file.parent.mkdir(parents=True, exist_ok=True)
        documents = read_json(docs_path)
        with duckdb.connect() as con:
            source_sql = _sql_path(docs_path)
            target_sql = _sql_path(target_file)
            con.execute(
                f"""
                COPY (
                  SELECT * FROM read_json_auto('{source_sql}')
                )
                TO '{target_sql}'
                (FORMAT PARQUET)
                """,
            )
        self.runtime.logger.emit(
            "document_bronze_ingested",
            source_file=str(docs_path),
            target_file=str(target_file),
            records=len(documents),
        )
        return len(documents)


def _sql_path(path: Path) -> str:
    return str(path).replace("'", "''")
