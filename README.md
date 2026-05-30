# aimili-vpngate-minimal

<p align="center">
  <a href="#english"><img alt="English" src="https://img.shields.io/badge/README-English-2d6cdf"></a>
  <a href="#中文说明"><img alt="中文" src="https://img.shields.io/badge/README-中文-d14d72"></a>
</p>

---

## English
<a id="english"></a>

A minimal VPNGate residential egress project for Linux VPS.

### Table of contents

- [Goal](#goal)
- [Quick start](#quick-start)
- [Country shortcuts](#country-shortcuts)
- [Advanced install example](#advanced-install-example)
- [What the installer prints](#what-the-installer-prints)
- [What a successful result looks like](#what-a-successful-result-looks-like)
- [Beginner steps](#beginner-steps)
- [Default behavior](#default-behavior)
- [Korea defaults](#korea-defaults)
- [Supported installer flags](#supported-installer-flags)
- [Health check](#health-check)
- [Troubleshooting](#troubleshooting)
- [Uninstall](#uninstall)
- [IP source chain](#ip-source-chain)

### Goal
<a id="goal"></a>

Run **one command**, and get:

- VPNGate node auto-selection
- preferred `normal` + `residential` egress
- local proxy already configured
- Xray Reality inbound already configured
- a ready-to-use **VLESS link** printed at the end
- the final link also saved locally on disk

### Quick start
<a id="quick-start"></a>

Default Japan instance:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/diunigeaimiliya/aimili-vpngate-minimal/main/install.sh)
```

### Country shortcuts
<a id="country-shortcuts"></a>

```bash
bash <(curl -Ls https://raw.githubusercontent.com/diunigeaimiliya/aimili-vpngate-minimal/main/install.sh) jp
bash <(curl -Ls https://raw.githubusercontent.com/diunigeaimiliya/aimili-vpngate-minimal/main/install.sh) kr
```

### Advanced install example
<a id="advanced-install-example"></a>

```bash
bash <(curl -Ls https://raw.githubusercontent.com/diunigeaimiliya/aimili-vpngate-minimal/main/install.sh) \
  --country kr \
  --port 2054 \
  --remark KR-Residential \
  --proxy-port 7938 \
  --tun tun1 \
  --route-table 101 \
  --data-dir /opt/aimili-minimal-data-kr
```

### What the installer prints
<a id="what-the-installer-prints"></a>

After installation finishes, it waits for a healthy preferred node and then prints:

- service status
- current selected node
- proxy health
- exit IP
- proxy exit IP
- node country / location / quality / ip type
- final ready-to-use VLESS link
- local file path where the link was saved

If no healthy preferred node is connected in time, the installer exits with an error and tells you which logs to check.

### What a successful result looks like
<a id="what-a-successful-result-looks-like"></a>

```text
==== VLESS Link ====
vless://UUID@YOUR_SERVER_IP:2053?remarks=日本家宽&tls=1&peer=www.cloudflare.com&udp=1&xtls=2&pbk=PUBLIC_KEY&sid=SHORT_ID

==== Summary ====
Country            日本
Exit IP            1.2.3.4
Proxy Exit IP      203.0.113.10
Active Node        JP_xxx_xxx_tcp
Node Country       日本
Node Location      日本 东京都 ...
Node Quality       normal
Node IP Type       residential
Saved Link File    /root/aimili-vless-tun0.txt
Status             healthy preferred node connected
```

### Beginner steps
<a id="beginner-steps"></a>

1. Open your VPS terminal.
2. Make sure you are root, or run `sudo -i` first.
3. Copy one install command above and run it.
4. Wait until the script finishes.
5. Copy the printed VLESS link.
6. Import it into your client.
7. If you close the terminal, read the saved link file from `/root/aimili-vless-tun0.txt` or `/root/aimili-vless-tun1.txt`.

### Default behavior
<a id="default-behavior"></a>

Defaults:

- country: `日本`
- quality: `normal`
- ip type: `residential`
- local proxy: `127.0.0.1:7928`
- tun device: `tun0`
- route table: `100`
- VLESS Reality port: `2053`
- saved link file: `/root/aimili-vless-tun0.txt`

### Korea defaults
<a id="korea-defaults"></a>

Using `kr` automatically switches defaults to:

- proxy port: `7938`
- tun device: `tun1`
- route table: `101`
- vless port: `2054`
- data dir: `/opt/aimili-minimal-data-kr`
- saved link file: `/root/aimili-vless-tun1.txt`

### Supported installer flags
<a id="supported-installer-flags"></a>

```bash
--country
--port / --vless-port
--remark
--proxy-port
--tun
--route-table
--data-dir
--wait-seconds
```

### Health check
<a id="health-check"></a>

Use the included check script:

```bash
curl -Ls https://raw.githubusercontent.com/diunigeaimiliya/aimili-vpngate-minimal/main/check.sh | sudo bash
```

It prints:
- service status
- current state
- active node details
- important ports
- saved VLESS link

### Troubleshooting
<a id="troubleshooting"></a>

#### 1. The script finished but no VLESS link was printed

Check the service log:

```bash
journalctl -u aimili-vpngate-minimal -n 100 --no-pager
```

Common reasons:
- VPNGate did not return a good residential node in time
- the target country had no healthy preferred node at that moment
- `openvpn` failed to connect

#### 2. How do I find the generated VLESS link again?

```bash
cat /root/aimili-vless-tun0.txt
```

For Korea mode:

```bash
cat /root/aimili-vless-tun1.txt
```

#### 3. How do I reinstall?

Just run the install command again. It will overwrite the existing service config and refresh the Xray inbound used by this project.

#### 4. How do I uninstall?

```bash
curl -Ls https://raw.githubusercontent.com/diunigeaimiliya/aimili-vpngate-minimal/main/uninstall.sh | sudo bash
```

### Uninstall
<a id="uninstall"></a>

```bash
curl -Ls https://raw.githubusercontent.com/diunigeaimiliya/aimili-vpngate-minimal/main/uninstall.sh | sudo bash
```

### IP source chain
<a id="ip-source-chain"></a>

This project uses three sources:

1. **Candidate nodes:** VPNGate  
   `https://www.vpngate.net/api/iphone/`
2. **IP labels:** ip-api.com  
   Used for `residential / proxy / hosting / mobile`
3. **Final exit IP:** the connected VPNGate node itself

---

## 中文说明
<a id="中文说明"></a>

这是一个给 Linux VPS 用的极简 VPNGate 住宅出口项目。

### 目录

- [目标](#目标)
- [快速开始](#快速开始)
- [国家快捷参数](#国家快捷参数)
- [高级安装示例](#高级安装示例)
- [安装完成后会输出什么](#安装完成后会输出什么)
- [成功安装后的样子](#成功安装后的样子)
- [小白跟着做](#小白跟着做)
- [默认行为](#默认行为)
- [韩国实例默认值](#韩国实例默认值)
- [支持的安装参数](#支持的安装参数)
- [健康检查](#健康检查)
- [常见问题 / 排错](#常见问题--排错)
- [卸载](#卸载)
- [IP 来源链路](#ip-来源链路)

### 目标
<a id="目标"></a>

你只需要执行 **一条命令**，它就会自动帮你完成：

- 自动从 VPNGate 拉节点
- 自动优先筛选 `普通 normal + 住宅 residential`
- 自动连接目标国家的优选节点
- 自动配置本地代理
- 自动配置 Xray Reality 入站
- 最后直接输出一个可用的 **VLESS 链接**
- 同时把这个链接保存到本地文件里

### 快速开始
<a id="快速开始"></a>

默认安装日本实例：

```bash
bash <(curl -Ls https://raw.githubusercontent.com/diunigeaimiliya/aimili-vpngate-minimal/main/install.sh)
```

### 国家快捷参数
<a id="国家快捷参数"></a>

```bash
bash <(curl -Ls https://raw.githubusercontent.com/diunigeaimiliya/aimili-vpngate-minimal/main/install.sh) jp
bash <(curl -Ls https://raw.githubusercontent.com/diunigeaimiliya/aimili-vpngate-minimal/main/install.sh) kr
```

### 高级安装示例
<a id="高级安装示例"></a>

```bash
bash <(curl -Ls https://raw.githubusercontent.com/diunigeaimiliya/aimili-vpngate-minimal/main/install.sh) \
  --country kr \
  --port 2054 \
  --remark 韩国家宽 \
  --proxy-port 7938 \
  --tun tun1 \
  --route-table 101 \
  --data-dir /opt/aimili-minimal-data-kr
```

### 安装完成后会输出什么
<a id="安装完成后会输出什么"></a>

脚本会等待“健康的优选节点真正连上”以后，再输出：

- 服务状态
- 当前选中的节点
- 代理健康状态
- 当前出口 IP
- 代理实际出口 IP
- 节点国家 / 位置 / 质量 / IP 类型
- 最终可直接使用的 VLESS 链接
- 本地保存链接的文件路径

如果在等待时间内没有连上健康节点，脚本会直接报错，并告诉你去看哪条日志。

### 成功安装后的样子
<a id="成功安装后的样子"></a>

```text
==== VLESS Link ====
vless://UUID@你的服务器IP:2053?remarks=日本家宽&tls=1&peer=www.cloudflare.com&udp=1&xtls=2&pbk=PUBLIC_KEY&sid=SHORT_ID

==== Summary ====
Country            日本
Exit IP            1.2.3.4
Proxy Exit IP      203.0.113.10
Active Node        JP_xxx_xxx_tcp
Node Country       日本
Node Location      日本 东京都 ...
Node Quality       normal
Node IP Type       residential
Saved Link File    /root/aimili-vless-tun0.txt
Status             healthy preferred node connected
```

### 小白跟着做
<a id="小白跟着做"></a>

1. 打开你的 VPS 终端。  
2. 先切到 root，或者执行 `sudo -i`。  
3. 复制上面的一条安装命令并执行。  
4. 等脚本自动跑完。  
5. 复制它最后输出的 VLESS 链接。  
6. 导入到你的客户端里。  
7. 如果终端关掉了，也可以去本地文件里重新看链接。  

### 默认行为
<a id="默认行为"></a>

默认是：

- 国家：`日本`
- 质量：`normal`
- IP 类型：`residential`
- 本地代理：`127.0.0.1:7928`
- tun 设备：`tun0`
- 路由表：`100`
- VLESS 端口：`2053`
- 链接保存文件：`/root/aimili-vless-tun0.txt`

### 韩国实例默认值
<a id="韩国实例默认值"></a>

如果你用 `kr` 安装，它会自动切换成：

- 代理端口：`7938`
- tun 设备：`tun1`
- 路由表：`101`
- VLESS 端口：`2054`
- 数据目录：`/opt/aimili-minimal-data-kr`
- 链接保存文件：`/root/aimili-vless-tun1.txt`

### 支持的安装参数
<a id="支持的安装参数"></a>

```bash
--country
--port / --vless-port
--remark
--proxy-port
--tun
--route-table
--data-dir
--wait-seconds
```

### 健康检查
<a id="健康检查"></a>

使用仓库内提供的检查脚本：

```bash
curl -Ls https://raw.githubusercontent.com/diunigeaimiliya/aimili-vpngate-minimal/main/check.sh | sudo bash
```

它会输出：
- 服务状态
- 当前状态
- 活动节点详情
- 关键端口
- 保存好的 VLESS 链接

### 常见问题 / 排错
<a id="常见问题--排错"></a>

#### 1）脚本跑完了，但没有输出 VLESS 链接

先看日志：

```bash
journalctl -u aimili-vpngate-minimal -n 100 --no-pager
```

常见原因：
- 当前时刻没筛到健康的目标国家住宅节点
- `openvpn` 连接失败
- VPNGate 返回的节点质量太差

#### 2）怎么重新找到已经生成的链接？

默认日本实例：

```bash
cat /root/aimili-vless-tun0.txt
```

韩国实例：

```bash
cat /root/aimili-vless-tun1.txt
```

#### 3）怎么重新安装？

直接再执行一遍安装命令就行。它会覆盖当前项目使用的 service 配置和 Xray 入站配置。

#### 4）怎么卸载？

```bash
curl -Ls https://raw.githubusercontent.com/diunigeaimiliya/aimili-vpngate-minimal/main/uninstall.sh | sudo bash
```

### 卸载
<a id="卸载"></a>

```bash
curl -Ls https://raw.githubusercontent.com/diunigeaimiliya/aimili-vpngate-minimal/main/uninstall.sh | sudo bash
```

### IP 来源链路
<a id="ip-来源链路"></a>

这个项目的 IP 来源分三层：

1. **候选节点来源：VPNGate**  
   `https://www.vpngate.net/api/iphone/`
2. **IP 标签来源：ip-api.com**  
   用来判断 `住宅 / 代理 / 机房 / 移动`  
3. **最终出口 IP**  
   是你连接成功后的那个 VPNGate 节点本身

### 说明

- 需要 root 权限
- 适合 Ubuntu / Debian 类系统
- 这是一个故意保持极简的版本

## License

MIT
