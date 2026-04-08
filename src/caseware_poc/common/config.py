from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    """Filesystem-backed configuration for the reference implementation."""

    root_dir: Path
    data_dir: Path
    bronze_dir: Path
    silver_dir: Path
    gold_dir: Path
    vector_dir: Path
    quality_dir: Path
    log_dir: Path
    sample_data_dir: Path
    guardrails_dir: Path
    db_path: Path
    batch_size: int = Field(default=6)
    max_retrieval_results: int = Field(default=4)
    embedding_dimensions: int = Field(default=512)

    @classmethod
    def from_root(cls, root_dir: Path) -> "AppConfig":
        data_dir = root_dir / "data"
        return cls(
            root_dir=root_dir,
            data_dir=data_dir,
            bronze_dir=data_dir / "bronze",
            silver_dir=data_dir / "silver",
            gold_dir=data_dir / "gold",
            vector_dir=data_dir / "vector_index",
            quality_dir=data_dir / "quality",
            log_dir=data_dir / "logs",
            sample_data_dir=root_dir / "sample_data",
            guardrails_dir=root_dir / "guardrails",
            db_path=data_dir / "platform.duckdb",
        )
