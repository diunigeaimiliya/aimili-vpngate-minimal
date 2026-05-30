#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME=${SERVICE_NAME:-aimili-vpngate-minimal}
DATA_DIR=${DATA_DIR:-/opt/aimili-minimal-data}
TUN_DEVICE=${TUN_DEVICE:-tun0}
VLESS_FILE=${VLESS_FILE:-/root/aimili-vless-${TUN_DEVICE}.txt}
STATE_FILE="${DATA_DIR}/state.json"
NODES_FILE="${DATA_DIR}/nodes.json"

print_section() {
  echo
  echo "==== $1 ===="
}

print_section "Service Status"
systemctl --no-pager --full status ${SERVICE_NAME} | sed -n '1,20p' || true

print_section "Current State"
if [[ -f "$STATE_FILE" ]]; then
  python3 - <<PY
import json
from pathlib import Path
state=json.loads(Path('$STATE_FILE').read_text(encoding='utf-8'))
for k in ['active_openvpn_node_id','last_check_message','proxy_ok','proxy_ip','proxy_latency_ms']:
    print(f"{k}: {state.get(k)}")
PY
else
  echo "state file not found: $STATE_FILE"
fi

print_section "Active Node Details"
if [[ -f "$STATE_FILE" && -f "$NODES_FILE" ]]; then
  python3 - <<PY
import json
from pathlib import Path
state=json.loads(Path('$STATE_FILE').read_text(encoding='utf-8'))
nodes=json.loads(Path('$NODES_FILE').read_text(encoding='utf-8'))
active=state.get('active_openvpn_node_id')
node=next((n for n in nodes if n.get('id')==active), None)
if not node:
    print('active node metadata not found')
else:
    for k in ['id','country','location','quality','ip_type','latency_ms','score','remote_host','remote_port']:
        print(f"{k}: {node.get(k)}")
PY
else
  echo "node metadata not found"
fi

print_section "Ports"
ss -ltnp | grep -E ':7928|:7938|:2053|:2054|:8787|:8788' || true

print_section "Saved VLESS Link"
if [[ -f "$VLESS_FILE" ]]; then
  cat "$VLESS_FILE"
else
  echo "saved link file not found: $VLESS_FILE"
fi
