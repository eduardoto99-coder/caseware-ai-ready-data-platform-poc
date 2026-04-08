from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from caseware_poc.common.config import AppConfig
from caseware_poc.common.runtime import PlatformRuntime
from caseware_poc.ingestion.pipeline import IngestionPipeline
from caseware_poc.ingestion.sample_data import write_sample_data
from caseware_poc.rag.embedding import HashEmbeddingProvider
from caseware_poc.rag.index import SharedVectorIndex
from caseware_poc.rag.service import RagAnswerService
from caseware_poc.serving.query_service import QueryOrchestrator
from caseware_poc.serving.sql_service import StructuredQueryService
from caseware_poc.transformations.lakehouse import LakehouseTransformer


class PlatformApp:
    def __init__(self, root_dir: Path) -> None:
        self.config = AppConfig.from_root(root_dir)
        self.runtime = PlatformRuntime.create(self.config)
        self.embedding_provider = HashEmbeddingProvider(self.config.embedding_dimensions)
        self.vector_index = SharedVectorIndex(self.runtime, self.embedding_provider)
        self.query_service = QueryOrchestrator(
            self.runtime,
            StructuredQueryService(self.runtime),
            RagAnswerService(self.runtime, self.vector_index),
        )

    def reset(self) -> None:
        for path in [self.config.data_dir, self.config.sample_data_dir]:
            if path.exists():
                shutil.rmtree(path)
        for path in [
            self.config.bronze_dir,
            self.config.silver_dir,
            self.config.gold_dir,
            self.config.vector_dir,
            self.config.quality_dir,
            self.config.log_dir,
            self.config.sample_data_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def bootstrap(self) -> dict[str, Any]:
        write_sample_data(self.config.sample_data_dir)
        ingestion_metrics = IngestionPipeline(self.runtime).ingest()
        transform_metrics = LakehouseTransformer(self.runtime).run()
        vector_metrics = self.vector_index.build()
        return {
            "ingestion": ingestion_metrics,
            "transformations": transform_metrics,
            "vector_index": vector_metrics,
        }

    def answer(self, tenant_id: str, question: str):
        return self.query_service.answer(tenant_id=tenant_id, question=question)
