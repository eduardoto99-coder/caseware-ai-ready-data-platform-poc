from __future__ import annotations

from dataclasses import dataclass

import boto3


@dataclass(slots=True)
class GlueCatalogConfig:
    region_name: str
    database_name: str


class GlueIcebergCatalogManager:
    """Reference Glue Catalog helper for Iceberg-backed medallion tables."""

    def __init__(self, config: GlueCatalogConfig) -> None:
        self.config = config
        self.client = boto3.client("glue", region_name=config.region_name)

    def ensure_database(self) -> None:
        self.client.create_database(
            DatabaseInput={
                "Name": self.config.database_name,
                "Description": "Caseware AI-ready accounting lakehouse",
            }
        )

    def register_iceberg_table(
        self,
        *,
        table_name: str,
        s3_location: str,
        columns: list[dict[str, str]],
    ) -> None:
        self.client.create_table(
            DatabaseName=self.config.database_name,
            TableInput={
                "Name": table_name,
                "TableType": "EXTERNAL_TABLE",
                "StorageDescriptor": {
                    "Columns": columns,
                    "Location": s3_location,
                    "InputFormat": "org.apache.iceberg.mr.hive.HiveIcebergInputFormat",
                    "OutputFormat": "org.apache.iceberg.mr.hive.HiveIcebergOutputFormat",
                    "SerdeInfo": {
                        "SerializationLibrary": "org.apache.iceberg.mr.hive.HiveIcebergSerDe"
                    },
                },
                "Parameters": {
                    "table_type": "ICEBERG",
                    "metadata_location": f"{s3_location.rstrip('/')}/metadata/v1.metadata.json",
                },
            },
        )
