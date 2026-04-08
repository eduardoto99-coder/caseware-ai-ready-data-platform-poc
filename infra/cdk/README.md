# CDK Reference Stack

This directory contains production-shaped AWS CDK scaffolding for the role-aligned platform stack.

The intent is to show how the local POC would translate into:

- S3 lakehouse buckets
- Glue Catalog and Iceberg metadata plane
- EMR Serverless Spark applications
- MSK/Kafka for CDC ingestion
- Aurora PostgreSQL with pgvector
- OpenSearch Serverless for vector retrieval
- EKS for Trino, Spark Operator, Langfuse, and supporting services
- Bedrock-aligned IAM roles and AI data-plane resources
- CloudWatch and New Relic observability resources

These files are reference code and are not part of the runnable local demo path.
