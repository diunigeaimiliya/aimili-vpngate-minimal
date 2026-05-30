# aimili-vpngate-minimal

极简版 Linux VPS 出站代理工具：

- 自动从 **VPNGate** 拉取公开节点
- 自动用 **ip-api.com** 给节点打标签
- 默认优先筛选 **普通（normal）+ 住宅（residential）**
- 默认按目标国家优先（默认：`日本`）
- 自动连接最优节点
- 当前已连优选节点且健康正常时：**不主动换节点**
- 本地提供 HTTP / SOCKS5 代理
- **无前端、无管理面板、无安装脚本依赖**

这个项目的目标不是“功能全”，而是：

> **用尽量少的代码，把 VPNGate 自动筛选住宅出口这件事稳定跑起来。**

## IP 来源说明

这个项目的 IP 来源分三层：

1. **候选节点来源：VPNGate**  
   使用 `https://www.vpngate.net/api/iphone/` 拉取公开 OpenVPN 节点。

2. **IP 类型与质量标签来源：ip-api.com**  
   用于判断节点是否为：
   - `residential`
   - `proxy`
   - `hosting`
   - `mobile`

3. **最终实际出口**  
   是连接成功后的 VPNGate 节点本身。

## 保留的核心功能

- 拉取 VPNGate 节点
- 按批次测试节点
- 自动筛选目标国家的普通住宅 IP
- 自动连接最优节点
- 健康检查
- 本地 HTTP / SOCKS5 代理
- 已连优选节点时保持稳定，不主动切换

## 刻意删掉的东西

- Web UI
- 登录系统
- 节点列表前端
- 复杂安装脚本
- 多余命令菜单
- 黑名单 / 人工面板逻辑

## 运行要求

- Ubuntu / Debian
- Python 3.10+
- `openvpn`
- `iproute2`
- root 权限（需要 tun / 策略路由 / SO_BINDTODEVICE）

安装依赖：

```bash
sudo apt update
sudo apt install -y openvpn iproute2 curl ca-certificates python3
```

## 快速运行

```bash
git clone https://github.com/diunigeaimiliya/aimili-vpngate-minimal.git
cd aimili-vpngate-minimal
sudo python3 aimili_minimal.py
```

## 默认行为

默认配置：

- 目标国家：`日本`
- 网络质量：`normal`
- IP 类型：`residential`
- 本地代理：`127.0.0.1:7928`
- TUN：`tun0`
- 路由表：`100`

## 环境变量

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

## 韩国实例示例

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

## systemd

仓库内已附带示例服务文件：

- `aimili-vpngate-minimal.service`

安装示例：

```bash
sudo cp aimili-vpngate-minimal.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now aimili-vpngate-minimal
```

## 自检

```bash
python3 -m py_compile aimili_minimal.py
python3 aimili_minimal.py --print-config
```

## License

MIT
