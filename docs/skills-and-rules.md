# Skills and Rules

This repository now has one source of truth for skills, rules, and LLM guardrails: `guardrails/`.

Those assets are consumed by the serving layer and the agent layer through the same policy files. That is the important design choice. The repo no longer depends on a second prompt tree that can drift away from the real runtime behavior.

## Source of Truth

### `guardrails/context/`

- `system_context.md`
  global operating constraints for the platform

### `guardrails/skills/`

- `exact_accounting_sql.md`
- `tenant_safe_policy_rag.md`
- `precision_guardrail.md`
- `context_budget_manager.md`

These skill files use Markdown plus YAML front matter so they are human-readable in GitHub and machine-loadable in code.

### `guardrails/rules/`

- `routing.yaml`
  SQL vs RAG vs mixed-guardrail selection
- `retrieval.yaml`
  required metadata filters, doc-type hints, ranking boosts, and citation requirements
- `response.yaml`
  warning text, insufficient-grounding behavior, and exactness rules
- `tenant_isolation.yaml`
  tenant-boundary requirements for query and retrieval paths
- `tooling.yaml`
  allowed tools per skill and execution ordering
- `context_budget.yaml`
  max chunks and max context size rules

### `guardrails/contracts/`

- `answer_contracts.yaml`
  required response fields for each skill

### `guardrails/templates/`

- `response_contract.md`
- `trino_overdue_query.sql`

These are reusable prompt/query assets for the agent workflow.

## Skill Contracts

### `exact_accounting_sql`

- Purpose: answer exact financial and operational questions from governed gold tables
- Sources: `gold_invoice_summary`, `gold_engagement_status`, `gold_control_exceptions`
- Required outputs: SQL, structured records, lineage when available
- Forbidden behavior: never infer exact balances from documents

### `tenant_safe_policy_rag`

- Purpose: retrieve tenant-scoped narrative evidence from policies, workpapers, notes, and issue summaries
- Required outputs: citations, metadata filters, grounded summary
- Forbidden behavior: never answer without tenant filters and never present OCR fragments as exact truth

### `precision_guardrail`

- Purpose: handle mixed questions where exact-value intent and document intent appear together
- Required outputs: warning, SQL-backed exact answer, document citations for context only
- Forbidden behavior: never let RAG own exact balances and never suppress the warning

## Runtime Wiring

The serving stack reads the guardrail files through [registry.py](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/src/caseware_poc/guardrails/registry.py).

- [router.py](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/src/caseware_poc/serving/router.py)
  uses `routing.yaml` to choose `sql`, `rag`, or `mixed_guardrail`
- [service.py](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/src/caseware_poc/rag/service.py)
  uses `retrieval.yaml` to apply metadata filters and ranking hints
- [query_service.py](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/src/caseware_poc/serving/query_service.py)
  uses `response.yaml` to inject guardrail warnings and attaches `guardrail_context`
- [app.py](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/src/caseware_poc/app.py)
  exposes the loaded policy bundle via `GET /guardrails`

## Agent Wiring

The agent layer uses the same repo-native assets instead of a separate prompt tree.

- [prompt_loader.py](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/src/caseware_poc/agents/prompt_loader.py)
  loads `guardrails/skills/`, `guardrails/rules/`, `guardrails/context/`, and `guardrails/templates/`
- [guardrails.py](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/src/caseware_poc/agents/guardrails.py)
  enforces tenant checks, citation minimums, SQL authority for exact mixed answers, and context budgets
- [langgraph_workflow.py](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/src/caseware_poc/agents/langgraph_workflow.py)
  uses those assets in a LangGraph workflow that coordinates Trino, OpenSearch, Bedrock, and Langfuse

## Why This Matters

This design demonstrates four things clearly:

- the repo has explicit, versioned safety policy instead of hidden prompt strings
- the serving layer and the agent layer read from the same policy files
- structured finance questions are guarded away from hallucinated document answers
- context management and tenant isolation are visible in code, docs, and API output
