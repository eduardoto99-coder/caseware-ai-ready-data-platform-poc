# LLM Guardrails

The repository uses `guardrails/` as the single policy system for hallucination prevention, tenant isolation, tool discipline, and context management.

That policy system is consumed by both the serving layer and the LangGraph/Bedrock agent layer.

## Policy Files

### System context

[system_context.md](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/guardrails/context/system_context.md) defines the top-level operating rules:

- SQL is the source of truth for exact financial values
- RAG is for narrative evidence and policy context
- tenant isolation must be enforced before retrieval or query execution
- citations are required for grounded narrative answers
- OCR and table fragments are not authoritative exact sources

### Skill files

[exact_accounting_sql.md](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/guardrails/skills/exact_accounting_sql.md)  
[tenant_safe_policy_rag.md](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/guardrails/skills/tenant_safe_policy_rag.md)  
[precision_guardrail.md](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/guardrails/skills/precision_guardrail.md)  
[context_budget_manager.md](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/guardrails/skills/context_budget_manager.md)

These files define:

- what each route is for
- what evidence is allowed
- what outputs are required
- what the model or agent is prohibited from doing

### Rule files

[routing.yaml](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/guardrails/rules/routing.yaml)  
[retrieval.yaml](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/guardrails/rules/retrieval.yaml)  
[response.yaml](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/guardrails/rules/response.yaml)  
[tenant_isolation.yaml](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/guardrails/rules/tenant_isolation.yaml)  
[tooling.yaml](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/guardrails/rules/tooling.yaml)  
[context_budget.yaml](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/guardrails/rules/context_budget.yaml)

These files capture hard constraints around:

- route selection
- mandatory retrieval filters
- warning injection
- tenant boundary rules
- allowed tools per skill
- maximum context size

### Answer contracts

[answer_contracts.yaml](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/guardrails/contracts/answer_contracts.yaml) describes the required response shape for each skill.

### Templates

[response_contract.md](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/guardrails/templates/response_contract.md)  
[trino_overdue_query.sql](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/guardrails/templates/trino_overdue_query.sql)

These are reusable repo-native assets for the agent path.

## Serving Runtime Use

[registry.py](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/src/caseware_poc/guardrails/registry.py) loads the guardrail bundle and exposes:

- `skills`
- `routing`
- `retrieval`
- `response`
- `tenant_isolation`
- `tooling`
- `context_budget`
- `answer_contracts`

[router.py](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/src/caseware_poc/serving/router.py) reads `routing.yaml`.

[service.py](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/src/caseware_poc/rag/service.py) reads `retrieval.yaml`.

[query_service.py](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/src/caseware_poc/serving/query_service.py) reads `response.yaml` and returns `guardrail_context` with the response.

[app.py](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/src/caseware_poc/app.py) exposes the full bundle at `GET /guardrails`.

## Agent Use

[prompt_loader.py](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/src/caseware_poc/agents/prompt_loader.py) now reads directly from `guardrails/` instead of a separate prompt directory.

[langgraph_workflow.py](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/src/caseware_poc/agents/langgraph_workflow.py) uses:

- guardrail route rules
- repo-native skill files
- system context
- response template
- Trino SQL template

[guardrails.py](/Users/eduardoblandon/Desktop/caseware-ai-ready-platform-poc/src/caseware_poc/agents/guardrails.py) applies:

- tenant-boundary checks
- citation minimums
- SQL authority for exact mixed answers
- context-budget truncation

## Why It Is Strong

This design is strong in an interview because the guardrails are visible in three ways:

- as versioned files the team can inspect
- as runtime logic the API can expose
- as agent-side enforcement for a Bedrock/LangGraph production path
