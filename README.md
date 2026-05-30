# aimili-vpngate-minimal

A minimal VPNGate-based egress selector for Linux VPS.

## What it does

- Fetches public OpenVPN nodes from **VPNGate**
- Labels node IPs with **ip-api.com**
- Prefers nodes matching:
  - target country
  - `normal` quality
  - `residential` IP type
- Tests nodes in small batches
- Connects the best preferred node automatically
- Exposes a local HTTP / SOCKS5 proxy
- Keeps the current preferred node if health is still good

## Why this project exists

This repository is intentionally small.

It does **not** include:
- Web UI
- Login/auth system
- Frontend node table
- Heavy installer scripts
- Extra management panels

It keeps only the basic runtime needed to:
- fetch nodes
- classify nodes
- test nodes
- auto-connect a preferred residential node
- keep the proxy stable

## IP source chain

This project uses three different sources:

1. **Candidate nodes:** VPNGate  
   `https://www.vpngate.net/api/iphone/`

2. **IP type / quality labels:** ip-api.com  
   Used to classify nodes as `residential`, `proxy`, `hosting`, or `mobile`.

3. **Final exit IP:** the connected VPNGate node itself

## Requirements

- Ubuntu / Debian
- Python 3.10+
- `openvpn`
- `iproute2`
- root privileges

Install dependencies:

```bash
sudo apt update
sudo apt install -y openvpn iproute2 curl ca-certificates python3
```

## Quick start

```bash
git clone https://github.com/diunigeaimiliya/aimili-vpngate-minimal.git
cd aimili-vpngate-minimal
sudo python3 aimili_minimal.py
```

## Default behavior

By default it prefers:

- country: `日本`
- quality: `normal`
- ip type: `residential`
- local proxy: `127.0.0.1:7928`
- tun device: `tun0`
- route table: `100`

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
```

## Multi-instance usage

You can run multiple independent instances in parallel by changing:

- `PREFERRED_COUNTRY`
- `PROXY_PORT`
- `TUN_DEVICE`
- `ROUTE_TABLE_ID`
- `DATA_DIR`

### Example: Korea instance

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

This makes the Korea instance independent from the Japan instance.

## systemd

A sample service file is included:

- `aimili-vpngate-minimal.service`

Install example:

```bash
sudo cp aimili-vpngate-minimal.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now aimili-vpngate-minimal
```

## Self-check

```bash
python3 -m py_compile aimili_minimal.py
python3 aimili_minimal.py --print-config
```

## License

MIT

---

# 中文说明

这是一个极简版的 Linux VPS 出站代理工具。

## 功能

- 自动从 **VPNGate** 拉取公开节点
- 自动用 **ip-api.com** 给节点打标签
- 默认优先筛选：
  - 目标国家
  - `normal`（普通）
  - `residential`（住宅）
- 小批量测试节点
- 自动连接最优目标节点
- 提供本地 HTTP / SOCKS5 代理
- 当前优选节点健康正常时，不主动换节点

## 适合场景

- 想要一个最小可运行版本
- 不需要前端和复杂控制面板
- 想把 VPNGate 住宅出口逻辑集成到自己的项目里

## 多实例

支持多实例并行运行。

例如：
- 日本实例：`tun0 + 7928 + table 100`
- 韩国实例：`tun1 + 7938 + table 101`

只要这些参数分开，它们就能互不影响并行运行。
