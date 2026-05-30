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

Default Japan instance:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/diunigeaimiliya/aimili-vpngate-minimal/main/install.sh)
```

Explicit country shortcut:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/diunigeaimiliya/aimili-vpngate-minimal/main/install.sh) jp
bash <(curl -Ls https://raw.githubusercontent.com/diunigeaimiliya/aimili-vpngate-minimal/main/install.sh) kr
```

After installation finishes, it waits for a healthy preferred node and then prints:

- service status
- current selected node
- proxy health
- final ready-to-use VLESS link

If no healthy preferred node is connected in time, the installer exits with an error and tells you which logs to check.

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

Direct one-command install:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/diunigeaimiliya/aimili-vpngate-minimal/main/install.sh) kr
```

Manual runtime example:

```bash
sudo env \
  PREFERRED_COUNTRY=韩国 \
  PREFERRED_IP_TYPE=residential \
  PREFERRED_QUALITY=normal \
  PROXY_PORT=7938 \
  TUN_DEVICE=tun1 \
  ROUTE_TABLE_ID=101 \
  DATA_DIR=/opt/aimili-minimal-data-kr \
  python3 aimili_minimal.py
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

## IP source chain

This project uses three different sources:

1. **Candidate nodes:** VPNGate  
   `https://www.vpngate.net/api/iphone/`

2. **IP type / quality labels:** ip-api.com  
   Used to classify nodes as `residential`, `proxy`, `hosting`, or `mobile`.

3. **Final exit IP:** the connected VPNGate node itself

## Notes

- Requires root
- Tested on Ubuntu / Debian-like systems
- Designed to stay minimal on purpose

## License

MIT
