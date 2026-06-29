#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/opt/autonomous-enterprise-manager}"
CURRENT_LINK="${APP_ROOT}/current"
PREVIOUS_RELEASE="${APP_ROOT}/previous"

if [[ ! -e "${PREVIOUS_RELEASE}" ]]; then
  echo "No previous release available for rollback." >&2
  exit 1
fi

docker compose -f "${CURRENT_LINK}/docker-compose.production.yml" down || true

rm -f "${CURRENT_LINK}"
mv "${PREVIOUS_RELEASE}" "${CURRENT_LINK}"

cd "${CURRENT_LINK}"
docker compose -f docker-compose.production.yml up -d --build --remove-orphans

echo "Rollback completed."