#!/usr/bin/env bash
set -euo pipefail

CONNECT_URL="${CONNECT_URL:-http://localhost:8083}"

curl -sS -X PUT \
  -H "Content-Type: application/json" \
  --data @/connectors/postgres-cdc.json \
  "${CONNECT_URL}/connectors/caseware-postgres-cdc/config"

curl -sS -X PUT \
  -H "Content-Type: application/json" \
  --data @/connectors/mongodb-documents.json \
  "${CONNECT_URL}/connectors/caseware-mongodb-documents/config"

