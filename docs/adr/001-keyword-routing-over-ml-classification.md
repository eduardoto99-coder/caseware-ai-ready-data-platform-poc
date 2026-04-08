# ADR-001: Keyword routing over ML classification

## Status

Accepted

## Context

The agent workflow must route incoming questions to the correct retrieval path: SQL for exact financial answers, RAG for narrative context, or a guarded mixed path when both are needed.

Two approaches were considered:

1. **Keyword-based routing** using curated term lists maintained in guardrail rule files.
2. **ML classification** using a fine-tuned intent classifier or an LLM-as-judge step.

## Decision

We chose keyword-based routing for the initial platform.

## Rationale

- **Controlled vocabulary**: Audit and accounting domains use a finite, well-defined set of financial terms (invoice, overdue, balance, control, exception) and document terms (policy, workpaper, note). The overlap between categories is small and predictable.
- **Determinism**: Keyword routing produces the same result for the same input every time. This is important for auditability in a regulated domain where reviewers need to understand why a question took a particular path.
- **Latency**: A keyword check adds microseconds. An LLM classification step adds 200-500ms and an API call, which doubles the total query latency for every request.
- **Testability**: The golden question eval set (`evals/golden_questions.yaml`) can exhaustively verify routing accuracy. An ML classifier would require a separate training/evaluation pipeline and introduces drift risk.
- **Debuggability**: When a question misroutes, the fix is a term list update in `guardrails/rules/routing.md`, reviewable in a pull request. An ML misclassification requires retraining and redeployment.

## Trade-offs

- Keyword routing cannot handle paraphrased or ambiguous questions as well as a learned classifier. Questions like "how much do we owe" would miss unless "owe" is added to `sql_terms`.
- The mixed guardrail path depends on co-occurrence of SQL and precision-doc terms, which can produce false positives for questions that mention documents in passing.

## When to revisit

Upgrade to an ML classifier when:
- The eval set shows routing accuracy dropping below 90% on new question patterns.
- The term lists grow past 50 entries per category, indicating the vocabulary is no longer bounded.
- The platform supports user-authored queries where paraphrasing is common.
