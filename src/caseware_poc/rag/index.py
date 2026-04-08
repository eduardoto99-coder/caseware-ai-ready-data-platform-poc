from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import re
from typing import Any

import duckdb
import numpy as np

from caseware_poc.common.io_utils import write_json
from caseware_poc.common.models import RetrievedChunk
from caseware_poc.common.runtime import PlatformRuntime
from caseware_poc.rag.chunking import DocumentChunk, chunk_document
from caseware_poc.rag.embedding import HashEmbeddingProvider


class SharedVectorIndex:
    def __init__(self, runtime: PlatformRuntime, embedding_provider: HashEmbeddingProvider) -> None:
        self.runtime = runtime
        self.embedding_provider = embedding_provider
        self.metadata_path = runtime.config.vector_dir / "chunk_metadata.json"
        self.vector_path = runtime.config.vector_dir / "chunk_vectors.npy"

    def build(self) -> dict[str, int]:
        self.runtime.config.vector_dir.mkdir(parents=True, exist_ok=True)
        documents = self._load_documents()
        chunks = [chunk for document in documents for chunk in chunk_document(document)]
        matrix = self.embedding_provider.embed_many(chunk.text for chunk in chunks)
        np.save(self.vector_path, matrix)
        write_json(self.metadata_path, [asdict(chunk) for chunk in chunks])
        self.runtime.logger.emit(
            "vector_index_built",
            chunks=len(chunks),
            documents=len(documents),
            vector_path=str(self.vector_path),
            metadata_path=str(self.metadata_path),
        )
        return {"documents": len(documents), "chunks": len(chunks)}

    def search(
        self,
        *,
        question: str,
        tenant_id: str,
        top_k: int,
        metadata_filters: dict[str, Any] | None = None,
        ranking_policy: dict[str, Any] | None = None,
    ) -> list[RetrievedChunk]:
        metadata_filters = metadata_filters or {}
        chunk_metadata = self._load_metadata()
        matrix = self._load_vectors()
        eligible_indexes = [
            index
            for index, chunk in enumerate(chunk_metadata)
            if chunk["tenant_id"] == tenant_id
            and all(chunk.get(key) == value for key, value in metadata_filters.items())
        ]
        if not eligible_indexes:
            return []
        question_vector = self.embedding_provider.embed_text(question)
        filtered_matrix = matrix[eligible_indexes]
        scores = filtered_matrix @ question_vector
        scores = scores + self._heuristic_boosts(
            question=question,
            chunks=[chunk_metadata[index] for index in eligible_indexes],
            ranking_policy=ranking_policy or {},
        )
        ranking = np.argsort(scores)[::-1][:top_k]
        results: list[RetrievedChunk] = []
        for rank in ranking:
            chunk_index = eligible_indexes[int(rank)]
            chunk = chunk_metadata[chunk_index]
            results.append(
                RetrievedChunk(
                    chunk_id=chunk["chunk_id"],
                    tenant_id=chunk["tenant_id"],
                    document_id=chunk["document_id"],
                    doc_type=chunk["doc_type"],
                    title=chunk["title"],
                    source_uri=chunk["source_uri"],
                    chunk_index=chunk["chunk_index"],
                    score=float(scores[int(rank)]),
                    text=chunk["text"],
                )
            )
        self.runtime.logger.emit(
            "vector_search_completed",
            tenant_id=tenant_id,
            question=question,
            metadata_filters=metadata_filters,
            chunk_ids=[result.chunk_id for result in results],
        )
        return results

    def _load_documents(self) -> list[Any]:
        docs_file = _sql_path(self.runtime.config.bronze_dir / "documents" / "*.parquet")
        with duckdb.connect() as con:
            rows = con.execute(
                f"""
                SELECT
                  tenant_id,
                  document_id,
                  title,
                  doc_type,
                  classification,
                  retention_state,
                  created_at,
                  updated_at,
                  text,
                  source_uri,
                  contains_table_like_text
                FROM read_parquet('{docs_file}')
                ORDER BY tenant_id, document_id
                """,
            ).fetchall()
        from caseware_poc.common.models import DocumentRecord

        return [
            DocumentRecord(
                tenant_id=row[0],
                document_id=row[1],
                title=row[2],
                doc_type=row[3],
                classification=row[4],
                retention_state=row[5],
                created_at=row[6],
                updated_at=row[7],
                text=row[8],
                source_uri=row[9],
                contains_table_like_text=row[10],
            )
            for row in rows
        ]

    def _load_metadata(self) -> list[dict[str, Any]]:
        from caseware_poc.common.io_utils import read_json

        return read_json(self.metadata_path)

    def _load_vectors(self) -> np.ndarray:
        return np.load(self.vector_path)

    def _heuristic_boosts(
        self,
        *,
        question: str,
        chunks: list[dict[str, Any]],
        ranking_policy: dict[str, Any],
    ) -> np.ndarray:
        lowered = question.lower()
        query_terms = set(re.findall(r"[a-z0-9_]+", lowered))
        boost_values = []
        for chunk in chunks:
            chunk_terms = set(re.findall(r"[a-z0-9_]+", chunk["text"].lower()))
            overlap_ratio = len(query_terms & chunk_terms) / max(len(query_terms), 1)
            doc_type_boost = 0.0
            if "policy" in lowered and chunk["doc_type"] == "policy":
                doc_type_boost += float(ranking_policy.get("policy_doc_boost", 0.18))
            if any(term in lowered for term in ["workpaper", "ocr", "table"]) and chunk["doc_type"] == "workpaper":
                doc_type_boost += float(ranking_policy.get("workpaper_doc_boost", 0.18))
            if "note" in lowered and chunk["doc_type"] == "engagement_note":
                doc_type_boost += float(ranking_policy.get("note_doc_boost", 0.12))
            if "issue" in lowered and chunk["doc_type"] == "issue_summary":
                doc_type_boost += float(ranking_policy.get("issue_doc_boost", 0.12))
            lexical_overlap_boost = float(ranking_policy.get("lexical_overlap_boost", 0.25))
            boost_values.append((overlap_ratio * lexical_overlap_boost) + doc_type_boost)
        return np.array(boost_values, dtype=np.float32)


def _sql_path(path: Path) -> str:
    return str(path).replace("'", "''")
