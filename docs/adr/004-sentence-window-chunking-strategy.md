# ADR-004: Sentence-window chunking over recursive/semantic splitting

## Status

Accepted

## Context

The RAG pipeline must split accounting and audit documents into chunks suitable for embedding and retrieval. Three strategies were evaluated:

1. **Recursive character splitting** (e.g., LangChain's RecursiveCharacterTextSplitter): splits on paragraph, then sentence, then character boundaries at a fixed size.
2. **Semantic chunking**: uses embedding similarity between adjacent sentences to find natural topic boundaries.
3. **Sentence-window chunking**: groups sentences into overlapping windows of a target size, preserving sentence integrity.

The documents include both narrative policy text and OCR-extracted tables from workpapers.

## Decision

We use sentence-window chunking with a 320-character window and sentence carryover for narrative text. Table-like fragments are kept intact and never split.

## Rationale

### Why sentence windows

- **Retrieval context**: A 320-character window typically contains 2-4 sentences, which is enough context for the embedding model to capture the topic without diluting it with unrelated content.
- **Overlap via carryover**: The last sentence of each window is carried forward to the next chunk. This ensures that cross-sentence references (e.g., "This threshold applies to the above") are not lost at chunk boundaries.
- **Sentence integrity**: Unlike fixed-size splitting, sentence-window chunking never cuts a sentence in half. This avoids malformed embeddings and improves retrieval precision.

### Why 320 characters

- Empirical testing on Caseware-style policy documents showed that 320 characters captures 2-3 complete accounting policy statements. Smaller windows (200 chars) often split a single policy statement; larger windows (500+ chars) dilute the embedding with adjacent topics.
- The 320-char threshold also aligns with the context budget (8,000 chars / ~25 chunks), keeping the maximum prompt size manageable for Bedrock.

### Why tables are kept intact

- OCR-extracted tables have column alignment encoded in whitespace. Splitting a table row across chunks destroys the column-to-value association.
- Table detection uses a simple heuristic (`_is_table_like`): 2+ lines with multi-space separators. This is intentionally conservative; false negatives (a table treated as narrative) are safer than false positives (narrative text treated as a table and left unsplit).

### Why not semantic chunking

- Semantic chunking requires an embedding call per sentence during ingestion, which adds latency and cost proportional to document length.
- For the controlled vocabulary of accounting documents, sentence-window chunking achieves comparable retrieval quality without the ingestion overhead.
- Semantic chunking is harder to test deterministically: the chunk boundaries depend on the embedding model, making the eval set fragile across model versions.

## Trade-offs

- The 320-char window is a static threshold. Very long policy statements (e.g., multi-clause definitions) may be split mid-thought. The carryover mitigates this but does not eliminate it.
- The table detection heuristic misses tables that use tab characters instead of multi-space alignment. This is acceptable because `contains_table_like_text` is set upstream (by Textract or the document source), and the heuristic is a secondary check.

## When to revisit

- If retrieval eval (`evals/eval_chunking.py`) shows mean chunk size drifting significantly from the 200-400 char range, re-tune the window threshold.
- If the platform adds support for PDF documents with complex layouts (multi-column, nested tables), consider layout-aware chunking using Textract's block geometry.
