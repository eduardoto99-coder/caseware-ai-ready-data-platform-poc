# Guardrails

This directory is the repo-native policy layer for both the runnable local POC and the production-shaped agent reference path.

It holds:

- `context/`: global operating constraints for the system
- `skills/`: route-specific behavior contracts
- `rules/`: routing, retrieval, tenant-isolation, tooling, context-budget, and response policies
- `contracts/`: answer-shape requirements for each skill
- `templates/`: reusable prompt/query templates for the production-shaped agent path
