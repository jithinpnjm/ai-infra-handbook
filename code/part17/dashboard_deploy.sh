#!/bin/bash
# Deploy a Grafana dashboard via the Grafana API
DASHBOARD_JSON=$(cat dashboards/on-call.json | jq -c '.dashboard')
curl -X POST -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -d "{\"dashboard\": $DASHBOARD_JSON, \"overwrite\": true}" \
  $GRAFANA_URL/api/dashboards/db
