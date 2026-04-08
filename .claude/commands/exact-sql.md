Review the repo through the exact SQL path.

Focus on:

- `jobs/spark/bronze_to_silver.py`
- `jobs/spark/silver_to_gold.py`
- `sql/trino/gold_serving_views.sql`
- `src/caseware_poc/integrations/trino_client.py`

Answer these questions:

1. How does the POC ensure exact answers come from governed tables?
2. Where is duplicate or out-of-order CDC handled?
3. What would you say in an interview about SQL being the source of truth?
