# Claude Code Memory

This repository is meant to be read in a technical interview. Optimize for clarity and defensible design choices.

## Core rules

- SQL is the source of truth for balances, counts, overdue totals, and other exact finance questions.
- Retrieval is for policies, notes, workpapers, and narrative context.
- If a prompt mixes exact-value intent with document language, use the precision guardrail path.
- Never cross tenant boundaries.

## Important paths

- `jobs/spark/` for medallion processing
- `sql/iceberg/` and `sql/trino/` for data products
- `src/caseware_poc/rag/chunking.py` for document handling
- `src/caseware_poc/agents/langgraph_workflow.py` for orchestration
- `guardrails/skills/` and `guardrails/rules/` for agent behavior

## Local checks

- `pytest`

## Editing guidance

- Keep language plain.
- Avoid broad claims that the repo does not actually implement.
- If you add tooling references, make sure they match files that really exist here.
