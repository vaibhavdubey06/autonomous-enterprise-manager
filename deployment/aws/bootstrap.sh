#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/opt/autonomous-enterprise-manager}"
CURRENT_DIR="${CURRENT_DIR:-${APP_ROOT}/current}"
SHARED_DIR="${SHARED_DIR:-${APP_ROOT}/shared}"

mkdir -p "${APP_ROOT}/releases" "${CURRENT_DIR}" "${SHARED_DIR}"

cat >/etc/systemd/system/aem-stack.service <<EOF
[Unit]
Description=Autonomous Enterprise Manager stack
After=docker.service network-online.target
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${CURRENT_DIR}
ExecStart=/usr/bin/docker compose -f ${CURRENT_DIR}/docker-compose.production.yml up -d --build
ExecStop=/usr/bin/docker compose -f ${CURRENT_DIR}/docker-compose.production.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable aem-stack.service

echo "Bootstrap completed."