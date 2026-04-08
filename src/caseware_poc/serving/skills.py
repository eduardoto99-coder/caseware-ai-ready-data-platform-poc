from __future__ import annotations


SKILLS = {
    "exact_accounting_sql": {
        "description": "Answer exact, governed questions from curated gold tables using deterministic DuckDB SQL.",
        "use_for": ["totals", "counts", "overdue exposure", "engagement status", "control exception metrics"],
        "output_contract": "Structured rows, lineage references, no document-derived exact balances.",
    },
    "tenant_safe_policy_rag": {
        "description": "Retrieve tenant-scoped narrative evidence from policy, workpaper, note, and issue documents.",
        "use_for": ["policies", "workpapers", "notes", "issue summaries", "explanations"],
        "output_contract": "Grounded narrative summary with source citations and pre-retrieval metadata filters.",
    },
    "precision_guardrail": {
        "description": "Prevent OCR or narrative chunks from being treated as sources of exact financial truth.",
        "use_for": ["mixed narrative/exact questions", "document tables with numeric values", "tenant-safe guardrail flows"],
        "output_contract": "SQL-owned exact answer plus document context only when appropriate.",
    },
}

ROUTING_RULES = {
    "sql": "Use when the prompt asks for exact values, filters, aggregations, invoice state, engagement state, or control metrics.",
    "rag": "Use when the prompt asks what a policy, note, workpaper, or issue summary says.",
    "mixed_guardrail": "Use when exact-value intent and document intent appear together; structured data remains authoritative.",
}
