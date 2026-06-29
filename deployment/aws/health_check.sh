#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.production.yml}"

curl -fsS "${BASE_URL}/health" >/dev/null
curl -fsS "${BASE_URL}/health/backend" >/dev/null || curl -fsS "${BASE_URL}/api/v1/health" >/dev/null

if [[ -f "${COMPOSE_FILE}" ]]; then
	docker compose -f "${COMPOSE_FILE}" ps
elif [[ -f /opt/autonomous-enterprise-manager/current/docker-compose.production.yml ]]; then
	docker compose -f /opt/autonomous-enterprise-manager/current/docker-compose.production.yml ps
fi

echo "Health checks passed."