#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME=${SERVICE_NAME:-aimili-vpngate-minimal}
DATA_DIR=${DATA_DIR:-/opt/aimili-minimal-data}
REPO_DIR=${REPO_DIR:-/opt/aimili-vpngate-minimal}
XRAY_CONFIG=${XRAY_CONFIG:-/usr/local/etc/xray/config.json}

if [[ $EUID -ne 0 ]]; then
  echo "Please run as root"
  exit 1
fi

systemctl disable --now ${SERVICE_NAME} 2>/dev/null || true
rm -f /etc/systemd/system/${SERVICE_NAME}.service
systemctl daemon-reload

rm -rf "${DATA_DIR}"
rm -rf "${REPO_DIR}"

echo "Removed ${SERVICE_NAME}"
echo "Repository dir removed: ${REPO_DIR}"
echo "Data dir removed: ${DATA_DIR}"
echo "Note: xray service and ${XRAY_CONFIG} were left intact on purpose."
