Review the repo through the mixed-source guardrail path.

Focus on:

- `src/caseware_poc/serving/router.py`
- `src/caseware_poc/agents/guardrails.py`
- `src/caseware_poc/agents/langgraph_workflow.py`
- `guardrails/skills/precision_guardrail.md`
- `guardrails/rules/response.md`

Answer these questions:

1. How does the repo detect a mixed prompt?
2. Why is SQL executed before document context?
3. What warning should the system return and why?
