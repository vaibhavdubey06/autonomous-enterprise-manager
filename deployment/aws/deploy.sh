#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/opt/autonomous-enterprise-manager}"
RELEASE_ID="${1:-latest}"
RELEASE_DIR="${APP_ROOT}/releases/${RELEASE_ID}"
CURRENT_LINK="${APP_ROOT}/current"

if [[ ! -d "${RELEASE_DIR}" ]]; then
  echo "Release directory not found: ${RELEASE_DIR}" >&2
  exit 1
fi

# Symlink shared .env
if [[ -f "${APP_ROOT}/shared/.env" ]]; then
  ln -sfn "${APP_ROOT}/shared/.env" "${RELEASE_DIR}/.env"
fi

ln -sfn "${RELEASE_DIR}" "${CURRENT_LINK}"

cd "${CURRENT_LINK}"
docker compose -f docker-compose.production.yml up -d --build --remove-orphans

# Wait for Postgres
echo "Waiting for postgres..."
sleep 5

# Run DB Migrations
echo "Running database migrations..."
docker compose -f docker-compose.production.yml exec -T backend uv run alembic upgrade head || echo "No migrations to apply or alembic not found"

echo "Deployment started for ${RELEASE_ID}. Running health checks..."
${APP_ROOT}/shared/health_check.sh || echo "Warning: Health check failed! Please check logs."