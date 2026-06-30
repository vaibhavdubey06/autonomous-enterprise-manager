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

echo "Deployment started for ${RELEASE_ID}."