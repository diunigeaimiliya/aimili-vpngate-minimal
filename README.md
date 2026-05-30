# aimili-vpngate-minimal

A minimal VPNGate residential egress project for Linux VPS.

## Goal

Run **one command**, and get:

- VPNGate node auto-selection
- preferred `normal` + `residential` egress
- local proxy already configured
- Xray Reality inbound already configured
- a ready-to-use **VLESS link** printed at the end

## Features

- Fetch nodes from VPNGate
- Label IPs using ip-api.com
- Prefer target country + residential + normal
- Test in small batches
- Auto-connect the best preferred node
- Keep the current preferred node while health is good
- Provide local HTTP / SOCKS5 proxy for Xray outbound
- Auto-generate a VLESS Reality inbound and print the final share link

## One-command install

```bash
bash <(curl -Ls https://raw.githubusercontent.com/diunigeaimiliya/aimili-vpngate-minimal/main/install.sh)
```

After installation finishes, it prints a ready-to-use VLESS link.

## Default behavior

Defaults:

- country: `日本`
- quality: `normal`
- ip type: `residential`
- local proxy: `127.0.0.1:7928`
- tun device: `tun0`
- route table: `100`
- VLESS Reality port: `2053`

## Example: Korea instance

```bash
PREFERRED_COUNTRY=韩国 PROXY_PORT=7938 TUN_DEVICE=tun1 ROUTE_TABLE_ID=101 VLESS_PORT=2054 bash <(curl -Ls https://raw.githubusercontent.com/diunigeaimiliya/aimili-vpngate-minimal/main/install.sh)
```

## Environment variables

```bash
PREFERRED_COUNTRY=日本
PREFERRED_IP_TYPE=residential
PREFERRED_QUALITY=normal
PROXY_HOST=127.0.0.1
PROXY_PORT=7928
TUN_DEVICE=tun0
ROUTE_TABLE_ID=100
DATA_DIR=/opt/aimili-minimal-data
OPENVPN_CMD=openvpn
CHECK_INTERVAL_SECONDS=30
SCAN_BATCH_SIZE=10
OPENVPN_TEST_TIMEOUT_SECONDS=15
VLESS_PORT=2053
```

## Output

The installer prints a final link like:

```text
vless://UUID@SERVER:2053?remarks=日本家宽&tls=1&peer=www.cloudflare.com&udp=1&xtls=2&pbk=PUBLIC_KEY&sid=SHORT_ID
```

## Notes

- Candidate node source: `https://www.vpngate.net/api/iphone/`
- IP type / quality labels: `ip-api.com`
- Requires root
- Tested on Ubuntu / Debian-like systems

## License

MIT
