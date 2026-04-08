# Agent Guide

This repo is an interview POC for a multi-tenant accounting and audit data platform.

## Working context

- Exact financial facts come from SQL over governed gold tables.
- Narrative answers come from tenant-scoped retrieval.
- Mixed questions must use the guardrail path: SQL for the exact answer, documents for context only.
- Tenant isolation is mandatory before query execution or retrieval.

## Files to read first

1. `README.md`
2. `jobs/spark/cdc_to_bronze.py`
3. `jobs/spark/bronze_to_silver.py`
4. `jobs/spark/silver_to_gold.py`
5. `src/caseware_poc/rag/chunking.py`
6. `src/caseware_poc/serving/router.py`
7. `src/caseware_poc/agents/langgraph_workflow.py`

## Guardrail files

- Skills live under `guardrails/skills/*.md`
- Rules live under `guardrails/rules/*.md`
- Answer contracts live in `guardrails/contracts/answer_contracts.yaml`

## Review bar

- Prefer concrete fixes over architecture theater.
- Do not introduce demo-only shortcuts that are not relevant to the challenge.
- Keep comments short and decision-focused.
- If you change route behavior, tenant handling, or retrieval policy, update the guardrail files too.
