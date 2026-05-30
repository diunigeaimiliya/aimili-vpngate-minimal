#!/usr/bin/env bash
set -euo pipefail

REPO_DIR=/opt/aimili-vpngate-minimal
SERVICE_NAME=aimili-vpngate-minimal
XRAY_CONFIG=/usr/local/etc/xray/config.json
XRAY_BIN=/usr/local/bin/xray

PREFERRED_COUNTRY=${PREFERRED_COUNTRY:-日本}
PROXY_HOST=${PROXY_HOST:-127.0.0.1}
PROXY_PORT=${PROXY_PORT:-7928}
TUN_DEVICE=${TUN_DEVICE:-tun0}
ROUTE_TABLE_ID=${ROUTE_TABLE_ID:-100}
DATA_DIR=${DATA_DIR:-/opt/aimili-minimal-data}
VLESS_PORT=${VLESS_PORT:-2053}
REMARK=${REMARK:-}

parse_country_alias() {
  case "$(echo "$1" | tr '[:upper:]' '[:lower:]')" in
    jp|japan|日本) echo "日本" ;;
    kr|korea|韩国|南韩) echo "韩国" ;;
    *) echo "$1" ;;
  esac
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    jp|japan|日本|kr|korea|韩国|南韩)
      PREFERRED_COUNTRY="$(parse_country_alias "$1")"
      shift
      ;;
    --country)
      PREFERRED_COUNTRY="$(parse_country_alias "$2")"
      shift 2
      ;;
    --port|--vless-port)
      VLESS_PORT="$2"
      shift 2
      ;;
    --remark)
      REMARK="$2"
      shift 2
      ;;
    --proxy-port)
      PROXY_PORT="$2"
      shift 2
      ;;
    --tun)
      TUN_DEVICE="$2"
      shift 2
      ;;
    --route-table)
      ROUTE_TABLE_ID="$2"
      shift 2
      ;;
    --data-dir)
      DATA_DIR="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ "$PREFERRED_COUNTRY" == "韩国" ]]; then
  [[ "$PROXY_PORT" == "7928" ]] && PROXY_PORT=7938
  [[ "$TUN_DEVICE" == "tun0" ]] && TUN_DEVICE=tun1
  [[ "$ROUTE_TABLE_ID" == "100" ]] && ROUTE_TABLE_ID=101
  [[ "$VLESS_PORT" == "2053" ]] && VLESS_PORT=2054
  [[ "$DATA_DIR" == "/opt/aimili-minimal-data" ]] && DATA_DIR=/opt/aimili-minimal-data-kr
fi

if [[ -z "$REMARK" ]]; then
  REMARK="${PREFERRED_COUNTRY}家宽"
fi

print_section() {
  echo
  echo "==== $1 ===="
}

if [[ $EUID -ne 0 ]]; then
  echo "Please run as root"
  exit 1
fi

apt-get update
apt-get install -y openvpn iproute2 curl ca-certificates python3 git unzip

if [[ ! -d "$REPO_DIR/.git" ]]; then
  rm -rf "$REPO_DIR"
  git clone https://github.com/diunigeaimiliya/aimili-vpngate-minimal.git "$REPO_DIR"
else
  git -C "$REPO_DIR" pull --ff-only || true
fi

mkdir -p "$DATA_DIR"
cat > /etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=Aimili VPNGate Minimal
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=${REPO_DIR}
ExecStart=/usr/bin/python3 ${REPO_DIR}/aimili_minimal.py
Restart=always
RestartSec=5
Environment=PREFERRED_COUNTRY=${PREFERRED_COUNTRY}
Environment=PREFERRED_IP_TYPE=residential
Environment=PREFERRED_QUALITY=normal
Environment=PROXY_HOST=${PROXY_HOST}
Environment=PROXY_PORT=${PROXY_PORT}
Environment=TUN_DEVICE=${TUN_DEVICE}
Environment=ROUTE_TABLE_ID=${ROUTE_TABLE_ID}
Environment=DATA_DIR=${DATA_DIR}

[Install]
WantedBy=multi-user.target
EOF

if [[ ! -x "$XRAY_BIN" ]]; then
  ARCH=$(dpkg --print-architecture)
  case "$ARCH" in
    amd64) XRAY_ZIP='Xray-linux-64.zip' ;;
    arm64) XRAY_ZIP='Xray-linux-arm64-v8a.zip' ;;
    *) echo "Unsupported arch: $ARCH"; exit 1 ;;
  esac
  TMPDIR=$(mktemp -d)
  curl -L "https://github.com/XTLS/Xray-core/releases/latest/download/${XRAY_ZIP}" -o "$TMPDIR/xray.zip"
  unzip -o "$TMPDIR/xray.zip" -d "$TMPDIR/xray"
  install -m 755 "$TMPDIR/xray/xray" /usr/local/bin/xray
  mkdir -p /usr/local/share/xray /usr/local/etc/xray
  [[ -f "$TMPDIR/xray/geosite.dat" ]] && install -m 644 "$TMPDIR/xray/geosite.dat" /usr/local/share/xray/geosite.dat
  [[ -f "$TMPDIR/xray/geoip.dat" ]] && install -m 644 "$TMPDIR/xray/geoip.dat" /usr/local/share/xray/geoip.dat
  rm -rf "$TMPDIR"
fi

mkdir -p /usr/local/etc/xray
if [[ ! -f "$XRAY_CONFIG" ]]; then
  echo '{"log":{"loglevel":"warning"},"inbounds":[],"outbounds":[{"protocol":"freedom","tag":"direct"}],"routing":{"rules":[]}}' > "$XRAY_CONFIG"
fi

UUID=$(python3 - <<'PY'
import uuid
print(uuid.uuid4())
PY
)
KEYS=$($XRAY_BIN x25519)
PRIVATE_KEY=$(echo "$KEYS" | awk '/PrivateKey:/ {print $2}')
PUBLIC_KEY=$(echo "$KEYS" | awk '/PublicKey\):/ {print $3}')
SHORT_ID=$(python3 - <<'PY'
import secrets
print(secrets.token_hex(8))
PY
)

python3 - <<PY
import json
from pathlib import Path
p=Path('$XRAY_CONFIG')
conf=json.loads(p.read_text())
conf.setdefault('inbounds', [])
conf.setdefault('outbounds', [{'protocol':'freedom','tag':'direct'}])
conf.setdefault('routing', {}).setdefault('rules', [])
conf['inbounds']=[ib for ib in conf['inbounds'] if ib.get('tag')!='aimili-vless']
conf['outbounds']=[ob for ob in conf['outbounds'] if ob.get('tag')!='aimili-socks-out']
conf['routing']['rules']=[r for r in conf['routing']['rules'] if 'aimili-vless' not in r.get('inboundTag',[])]
conf['inbounds'].append({
  'tag':'aimili-vless',
  'listen':'0.0.0.0',
  'port':$VLESS_PORT,
  'protocol':'vless',
  'settings':{'clients':[{'id':'$UUID','flow':'xtls-rprx-vision','email':'aimili-minimal@local'}],'decryption':'none'},
  'streamSettings':{
    'network':'tcp',
    'security':'reality',
    'realitySettings':{
      'show':False,
      'dest':'www.cloudflare.com:443',
      'xver':0,
      'serverNames':['www.cloudflare.com'],
      'privateKey':'$PRIVATE_KEY',
      'shortIds':['$SHORT_ID']
    }
  },
  'sniffing':{'enabled':True,'destOverride':['http','tls','quic']}
})
conf['outbounds'].append({'protocol':'socks','tag':'aimili-socks-out','settings':{'servers':[{'address':'127.0.0.1','port':$PROXY_PORT}]}})
conf['routing']['rules'].append({'type':'field','inboundTag':['aimili-vless'],'outboundTag':'aimili-socks-out'})
p.write_text(json.dumps(conf, ensure_ascii=False, indent=2))
PY

cat > /etc/systemd/system/xray.service <<EOF
[Unit]
Description=Xray Service
After=network.target nss-lookup.target

[Service]
Type=simple
ExecStart=${XRAY_BIN} run -config ${XRAY_CONFIG}
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now ${SERVICE_NAME}
systemctl enable --now xray
systemctl restart ${SERVICE_NAME}
systemctl restart xray

STATE_FILE="${DATA_DIR}/state.json"
WAIT_OK=0
for _ in $(seq 1 36); do
  sleep 5
  if [[ -f "$STATE_FILE" ]]; then
    if python3 - <<PY
import json, sys
from pathlib import Path
p=Path('$STATE_FILE')
state=json.loads(p.read_text(encoding='utf-8'))
active=state.get('active_openvpn_node_id')
proxy_ok=state.get('proxy_ok')
print(json.dumps({'active_openvpn_node_id': active, 'proxy_ok': proxy_ok, 'last_check_message': state.get('last_check_message')}, ensure_ascii=False))
sys.exit(0 if active and proxy_ok else 1)
PY
    then
      WAIT_OK=1
      break
    fi
  fi
done

print_section "Service Status"
systemctl --no-pager --full status ${SERVICE_NAME} | sed -n '1,20p' || true
systemctl --no-pager --full status xray | sed -n '1,20p' || true

print_section "Port Check"
ss -ltnp | grep -E ":${PROXY_PORT}|:${VLESS_PORT}" || true

if [[ -f "$STATE_FILE" ]]; then
  print_section "Current State"
  python3 - <<PY
import json
from pathlib import Path
p=Path('$STATE_FILE')
state=json.loads(p.read_text(encoding='utf-8'))
for k in ['active_openvpn_node_id','last_check_message','proxy_ok','proxy_ip','proxy_latency_ms']:
    print(f"{k}: {state.get(k)}")
PY
fi

if [[ "$WAIT_OK" != "1" ]]; then
  print_section "Install Result"
  echo "Installation finished, but no healthy preferred node is connected yet."
  echo "Check logs with: journalctl -u ${SERVICE_NAME} -n 100 --no-pager"
  exit 1
fi

SERVER_IP=$(curl -4 -s https://api.ipify.org || hostname -I | awk '{print $1}')
VLESS_LINK=$(python3 ${REPO_DIR}/share_link.py \
  --server "$SERVER_IP" \
  --port "$VLESS_PORT" \
  --uuid "$UUID" \
  --public-key "$PUBLIC_KEY" \
  --short-id "$SHORT_ID" \
  --remark "$REMARK")

ACTIVE_NODE=$(python3 - <<PY
import json
from pathlib import Path
p=Path('$STATE_FILE')
state=json.loads(p.read_text(encoding='utf-8'))
print(state.get('active_openvpn_node_id') or '')
PY
)

VLESS_FILE="/root/aimili-vless-${TUN_DEVICE}.txt"
printf '%s\n' "$VLESS_LINK" > "$VLESS_FILE"
chmod 600 "$VLESS_FILE"

print_section "VLESS Link"
echo "$VLESS_LINK"

print_section "Summary"
printf '%-18s %s\n' 'Country' "${PREFERRED_COUNTRY}"
printf '%-18s %s\n' 'Exit IP' "${SERVER_IP}"
printf '%-18s %s\n' 'Active Node' "${ACTIVE_NODE}"
printf '%-18s %s\n' 'Proxy' "${PROXY_HOST}:${PROXY_PORT}"
printf '%-18s %s\n' 'Tun Device' "${TUN_DEVICE}"
printf '%-18s %s\n' 'Route Table' "${ROUTE_TABLE_ID}"
printf '%-18s %s\n' 'VLESS Port' "${VLESS_PORT}"
printf '%-18s %s\n' 'Remark' "${REMARK}"
printf '%-18s %s\n' 'Data Dir' "${DATA_DIR}"
printf '%-18s %s\n' 'Saved Link File' "${VLESS_FILE}"
printf '%-18s %s\n' 'Status' 'healthy preferred node connected'
