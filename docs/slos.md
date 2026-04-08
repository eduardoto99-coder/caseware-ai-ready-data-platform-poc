# Platform SLOs

Service-level objectives for the AI-ready data platform. These targets would apply to the production environment and are monitored through CloudWatch dashboards and Langfuse traces.

## Data Platform


| Metric                 | Target       | Measurement                                             |
| ---------------------- | ------------ | ------------------------------------------------------- |
| Bronze ingestion lag   | < 5 minutes  | Time between CDC event emission and bronze table write  |
| Silver freshness       | < 15 minutes | Time between bronze write and silver snapshot merge     |
| Gold freshness         | < 30 minutes | Time between silver merge and gold product rebuild      |
| Pipeline success rate  | > 99.5%      | Spark job runs without failure / total runs             |
| Data quality pass rate | > 99.0%      | Records passing quality checks / total records ingested |
| Quarantine rate        | < 1.0%       | Records routed to quarantine / total records processed  |


## AI Platform


| Metric                    | Target    | Measurement                                                |
| ------------------------- | --------- | ---------------------------------------------------------- |
| Query p50 latency         | < 800ms   | End-to-end from request to response                        |
| Query p95 latency         | < 2,000ms | End-to-end from request to response                        |
| Retrieval p95 latency     | < 200ms   | OpenSearch or pgvector query time                          |
| SQL retrieval p95 latency | < 300ms   | Trino query execution time                                 |
| Synthesis p95 latency     | < 1,500ms | Bedrock model inference time                               |
| Guardrail compliance rate | > 99.5%   | Responses passing all guardrail checks / total responses   |
| Citation coverage         | > 95%     | RAG and mixed-guardrail responses with at least 1 citation |
| Routing accuracy          | > 95%     | Correct route assignment measured against eval set         |


## Tenant Isolation


| Metric                     | Target | Measurement                                                                      |
| -------------------------- | ------ | -------------------------------------------------------------------------------- |
| Cross-tenant data leak     | 0      | Retrieval results containing data from another tenant                            |
| Tenant boundary violations | 0      | Requests where authenticated_tenant_id != request_tenant_id that reach retrieval |


## Availability


| Metric                   | Target  | Measurement                                                     |
| ------------------------ | ------- | --------------------------------------------------------------- |
| AI query endpoint uptime | > 99.9% | Successful responses / total requests (excluding client errors) |
| Data pipeline uptime     | > 99.5% | Scheduled pipeline runs that complete / total scheduled runs    |


## Alerting Thresholds

Alerts fire when:

- Bronze lag exceeds 15 minutes (warning) or 30 minutes (critical)
- Gold freshness exceeds 45 minutes
- Guardrail compliance drops below 99%
- Any cross-tenant violation is detected (immediate page)
- Query p95 exceeds 3,000ms for 5 consecutive minutes
- Quarantine rate exceeds 2% in a single batch

