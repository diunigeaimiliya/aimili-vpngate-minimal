# aimili-vpngate-minimal

一个极简版的 AimiliVPN 思路实现：

- 无前端
- 默认自动拉取 VPNGate 节点
- 默认优先筛选 `普通(normal)` + `住宅(residential)`
- 默认按目标国家优先（默认 `日本`）
- 找到符合条件的最优节点后自动连接
- 已连接且健康正常时，不主动换节点
- 本地提供 HTTP/SOCKS5 代理，默认 `127.0.0.1:7928`

> 这个项目的候选节点来源是 **VPNGate 公共节点池**，IP 类型标签来源是 **ip-api.com**。

## 运行要求

- Ubuntu / Debian 系 Linux
- Python 3.10+
- `openvpn`
- `iproute2`
- 建议 root 运行（因为需要创建 `tun`、配置策略路由、SO_BINDTODEVICE）

安装依赖：

```bash
sudo apt update
sudo apt install -y openvpn iproute2 curl ca-certificates python3
```

## 快速运行

```bash
sudo mkdir -p /opt/aimili-minimal-data
sudo python3 aimili_minimal.py
```

默认配置：

- 目标国家：`日本`
- IP 类型：`residential`
- 网络质量：`normal`
- 本地代理：`127.0.0.1:7928`
- TUN 设备：`tun0`
- 路由表：`100`
- 数据目录：`./data`

## 常用环境变量

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

## 示例：韩国实例

```bash
sudo env \
  PREFERRED_COUNTRY=韩国 \
  PROXY_PORT=7938 \
  TUN_DEVICE=tun1 \
  ROUTE_TABLE_ID=101 \
  DATA_DIR=/opt/aimili-minimal-data-kr \
  python3 aimili_minimal.py
```

## systemd 示例

```ini
[Unit]
Description=Aimili VPNGate Minimal
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/aimili-vpngate-minimal
ExecStart=/usr/bin/python3 /opt/aimili-vpngate-minimal/aimili_minimal.py
Restart=always
RestartSec=5
Environment=PREFERRED_COUNTRY=日本
Environment=PROXY_HOST=127.0.0.1
Environment=PROXY_PORT=7928
Environment=TUN_DEVICE=tun0
Environment=ROUTE_TABLE_ID=100
Environment=DATA_DIR=/opt/aimili-minimal-data

[Install]
WantedBy=multi-user.target
```

## 特性取舍

这个极简版故意不做：

- Web UI
- 登录系统
- 手动节点管理界面
- 多余的安装脚本
- 复杂的节点池维护

保留的只有：

- 拉取节点
- 打标签
- 分批测试
- 自动选最优住宅节点
- 自动连接
- 代理出站
- 健康检查

## 自检

```bash
python3 -m py_compile aimili_minimal.py
python3 aimili_minimal.py --print-config
```
