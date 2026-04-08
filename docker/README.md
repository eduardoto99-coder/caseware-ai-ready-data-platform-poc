# Docker Demo Stack

This directory contains an optional demo environment for interview walkthroughs.

The goal is not to run the full platform locally with production fidelity. The goal is to show concrete source systems, CDC plumbing, and search infrastructure using technologies that look closer to a real platform stack:

- PostgreSQL as the structured OLTP source
- MongoDB as the document-heavy source system
- Kafka as the CDC/event backbone
- Debezium / Kafka Connect for source capture
- OpenSearch as the retrieval/search engine

Why this exists:

- it gives you real-looking configuration for OLTP -> CDC -> ingestion discussions
- it avoids weaker interview signals like generic file-only sources when the feedback was about hands-on depth
- it keeps DocumentDB out of the architecture because it is not needed for this challenge

Important:

- this stack is interview-facing and demo-oriented
- it does not need to be production-ready or fully automated
- CDK remains the primary infrastructure-as-code story for AWS resources

Recommended walkthrough:

1. show `docker/compose.yaml`
2. show `docker/postgres/init/001_caseware_oltp.sql`
3. show `docker/mongo/init/001_seed_documents.js`
4. show `docker/connectors/postgres-cdc.json`
5. show `docker/connectors/mongodb-documents.json`
6. connect those sources to `jobs/spark/` and `src/caseware_poc/integrations/`

