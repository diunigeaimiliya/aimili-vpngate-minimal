#!/usr/bin/env python3
from __future__ import annotations

import base64
import csv
import json
import os
import queue
import re
import select
import shlex
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any

VPNGATE_API = "https://www.vpngate.net/api/iphone/"
IPINFO_API = (
    "http://ip-api.com/batch?lang=zh-CN&"
    "fields=status,query,country,regionName,city,isp,org,as,asname,proxy,hosting,mobile"
)

PREFERRED_COUNTRY = os.environ.get("PREFERRED_COUNTRY", "日本")
PREFERRED_IP_TYPE = os.environ.get("PREFERRED_IP_TYPE", "residential")
PREFERRED_QUALITY = os.environ.get("PREFERRED_QUALITY", "normal")
PROXY_HOST = os.environ.get("PROXY_HOST", "127.0.0.1")
PROXY_PORT = int(os.environ.get("PROXY_PORT", "7928"))
TUN_DEVICE = os.environ.get("TUN_DEVICE", "tun0")
ROUTE_TABLE_ID = os.environ.get("ROUTE_TABLE_ID", "100")
OPENVPN_CMD = os.environ.get("OPENVPN_CMD", "openvpn")
OPENVPN_AUTH_USER = os.environ.get("OPENVPN_AUTH_USER", "vpn")
OPENVPN_AUTH_PASS = os.environ.get("OPENVPN_AUTH_PASS", "vpn")
CHECK_INTERVAL_SECONDS = int(os.environ.get("CHECK_INTERVAL_SECONDS", "30"))
SCAN_BATCH_SIZE = int(os.environ.get("SCAN_BATCH_SIZE", "10"))
OPENVPN_TEST_TIMEOUT_SECONDS = int(os.environ.get("OPENVPN_TEST_TIMEOUT_SECONDS", "15"))
DATA_DIR = Path(os.environ.get("DATA_DIR", str(Path(__file__).with_name("data"))))
STATE_FILE = DATA_DIR / "state.json"
NODES_FILE = DATA_DIR / "nodes.json"
AUTH_FILE = DATA_DIR / "vpngate_auth.txt"
CONFIG_DIR = DATA_DIR / "configs"
IP_CACHE_FILE = DATA_DIR / "ip_cache.json"

COUNTRY_TRANSLATIONS = {
    "Japan": "日本",
    "Korea Republic of": "韩国",
    "Korea": "韩国",
    "Republic of Korea": "韩国",
    "United States": "美国",
    "Hong Kong": "香港",
    "Taiwan": "台湾",
    "Singapore": "新加坡",
}

lock = threading.RLock()
ip_cache_lock = threading.RLock()
active_openvpn_process: subprocess.Popen[str] | None = None
active_node_id = ""


def log(msg: str) -> None:
    print(time.strftime("[%Y-%m-%d %H:%M:%S]"), msg, flush=True)


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not AUTH_FILE.exists():
        AUTH_FILE.write_text(f"{OPENVPN_AUTH_USER}\n{OPENVPN_AUTH_PASS}\n", encoding="utf-8")
        AUTH_FILE.chmod(0o600)


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def state_update(**updates: Any) -> None:
    with lock:
        state = read_json(STATE_FILE, {})
        state.update(updates)
        write_json(STATE_FILE, state)


def safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return value.strip("._") or "node"


def parse_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def parse_vpngate_rows(text: str) -> list[dict[str, str]]:
    lines = [line for line in text.splitlines() if line and not line.startswith("*")]
    if lines and lines[0].startswith("#"):
        lines[0] = lines[0][1:]
    return list(csv.DictReader(lines))


def decode_config(encoded: str) -> str:
    return base64.b64decode(encoded.encode("ascii"), validate=False).decode("utf-8", errors="replace")


def parse_remote(config_text: str, fallback_ip: str = "") -> tuple[str, int, str]:
    remote_host = fallback_ip
    remote_port = 0
    proto = "unknown"
    for raw_line in config_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", ";")):
            continue
        parts = line.split()
        if parts[0].lower() == "proto" and len(parts) >= 2:
            proto = parts[1].lower()
        elif parts[0].lower() == "remote" and len(parts) >= 3:
            remote_host = parts[1]
            remote_port = int(parts[2]) if parts[2].isdigit() else 0
    return remote_host, remote_port, proto


def fetch_candidates() -> list[dict[str, Any]]:
    req = urllib.request.Request(
        VPNGATE_API,
        headers={"User-Agent": "aimili-vpngate-minimal/1.0", "Accept": "text/plain,*/*"},
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    rows = parse_vpngate_rows(text)
    seen_ips = set()
    candidates: list[dict[str, Any]] = []
    for row in rows:
        ip = row.get("IP", "")
        encoded = row.get("OpenVPN_ConfigData_Base64", "")
        if not ip or not encoded or ip in seen_ips:
            continue
        seen_ips.add(ip)
        config_text = decode_config(encoded)
        remote_host, remote_port, proto = parse_remote(config_text, ip)
        country_long = row.get("CountryLong", "")
        country = COUNTRY_TRANSLATIONS.get(country_long, country_long)
        node_id = safe_name(f"{row.get('CountryShort','XX')}_{ip}_{remote_port}_{proto}")
        candidates.append({
            "id": node_id,
            "country": country,
            "ip": ip,
            "score": parse_int(row.get("Score")),
            "ping": parse_int(row.get("Ping")),
            "remote_host": remote_host,
            "remote_port": remote_port,
            "proto": proto,
            "config_text": config_text,
            "config_file": str(CONFIG_DIR / f"{node_id}.ovpn"),
            "probe_status": "not_checked",
            "latency_ms": 0,
            "quality": "",
            "ip_type": "",
            "location": "",
            "active": False,
        })
    return candidates


def load_ip_cache() -> dict[str, dict[str, Any]]:
    with ip_cache_lock:
        return read_json(IP_CACHE_FILE, {})


def save_ip_cache(cache: dict[str, dict[str, Any]]) -> None:
    with ip_cache_lock:
        write_json(IP_CACHE_FILE, cache)


def enrich_ip_info(nodes: list[dict[str, Any]]) -> None:
    cache = load_ip_cache()
    now = time.time()
    need: list[str] = []
    for node in nodes:
        ip = node.get("ip") or node.get("remote_host")
        if not ip:
            continue
        cached = cache.get(ip)
        if cached and now - cached.get("cached_at", 0) < 7 * 24 * 3600:
            node.update({k: cached.get(k, "") for k in ["location", "ip_type", "quality"]})
        else:
            need.append(ip)
    if not need:
        return
    payload = json.dumps(need).encode("utf-8")
    req = urllib.request.Request(
        IPINFO_API,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "aimili-vpngate-minimal/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception as exc:
        log(f"ip-api query failed: {exc}")
        return
    for item in data:
        if item.get("status") != "success":
            continue
        ip = item.get("query")
        if not ip:
            continue
        ip_type = "residential"
        quality = "normal"
        if item.get("mobile"):
            ip_type = "mobile"
            quality = "mobile"
        elif item.get("proxy"):
            ip_type = "proxy"
            quality = "proxy"
        elif item.get("hosting"):
            ip_type = "hosting"
            quality = "datacenter"
        location = " ".join(x for x in [item.get("country"), item.get("regionName"), item.get("city")] if x)
        cache[ip] = {"ip_type": ip_type, "quality": quality, "location": location, "cached_at": now}
    save_ip_cache(cache)
    for node in nodes:
        ip = node.get("ip") or node.get("remote_host")
        if ip in cache:
            node.update({k: cache[ip].get(k, "") for k in ["location", "ip_type", "quality"]})


def ping_latency_ms(host: str, port: int, fallback_ping: int = 0) -> int:
    started = time.time()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(5)
        s.connect((host, port))
        return max(1, int((time.time() - started) * 1000))
    except OSError:
        return fallback_ping if fallback_ping > 0 else 0
    finally:
        try:
            s.close()
        except Exception:
            pass


def openvpn_command(config_file: str, dev: str) -> list[str]:
    cmd = shlex.split(OPENVPN_CMD, posix=False) or ["openvpn"]
    cmd.extend([
        "--config", config_file,
        "--dev", dev,
        "--dev-type", "tun",
        "--pull-filter", "ignore", "route-ipv6",
        "--pull-filter", "ignore", "ifconfig-ipv6",
        "--route-delay", "2",
        "--connect-retry-max", "1",
        "--connect-timeout", str(OPENVPN_TEST_TIMEOUT_SECONDS),
        "--auth-user-pass", str(AUTH_FILE),
        "--auth-nocache",
        "--data-ciphers", "AES-128-CBC:AES-256-GCM:AES-128-GCM:CHACHA20-POLY1305",
        "--verb", "3",
        "--route-nopull",
    ])
    return cmd


def stop_process(process: subprocess.Popen[str] | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        process.kill()


def kill_existing_openvpn_processes() -> None:
    if not sys.platform.startswith("linux"):
        return
    subprocess.run(["pkill", "-f", f"openvpn.*{TUN_DEVICE}"], capture_output=True, timeout=2)
    subprocess.run(["pkill", "-f", f"openvpn.*{DATA_DIR}"], capture_output=True, timeout=2)


def run_openvpn_until_ready(config_file: str, dev: str, keep_alive: bool) -> tuple[bool, str, subprocess.Popen[str] | None]:
    try:
        process = subprocess.Popen(
            openvpn_command(config_file, dev),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(DATA_DIR),
        )
    except Exception as exc:
        return False, str(exc), None

    lines: queue.Queue[str | None] = queue.Queue()
    startup_done = [False]

    def reader() -> None:
        assert process.stdout is not None
        for line in process.stdout:
            if not startup_done[0]:
                lines.put(line.rstrip())
            elif keep_alive:
                log(f"OpenVPN: {line.rstrip()}")
        if not startup_done[0]:
            lines.put(None)

    threading.Thread(target=reader, daemon=True).start()
    started = time.time()
    tail: list[str] = []
    ok = False
    message = "OpenVPN did not complete initialization."
    while time.time() - started < OPENVPN_TEST_TIMEOUT_SECONDS:
        try:
            line = lines.get(timeout=0.5)
        except queue.Empty:
            if process.poll() is not None:
                break
            continue
        if line is None:
            break
        tail.append(line)
        tail = tail[-8:]
        lower = line.lower()
        if keep_alive:
            log(f"OpenVPN: {line}")
        if "initialization sequence completed" in lower:
            ok = True
            message = "connected"
            break
        if "auth_failed" in lower or "fatal error" in lower:
            message = line[-220:]
            break
    startup_done[0] = True
    if not keep_alive or not ok:
        stop_process(process)
        process = None
    return ok, message, process


def cleanup_policy_routing() -> None:
    subprocess.run(["ip", "rule", "del", "table", ROUTE_TABLE_ID], capture_output=True, timeout=2)
    subprocess.run(["ip", "route", "flush", "table", ROUTE_TABLE_ID], capture_output=True, timeout=2)


def setup_policy_routing(interface: str) -> None:
    cleanup_policy_routing()
    subprocess.run(["ip", "route", "add", "default", "dev", interface, "table", ROUTE_TABLE_ID], check=True, timeout=2)
    subprocess.run(["ip", "rule", "add", "oif", interface, "table", ROUTE_TABLE_ID], check=True, timeout=2)


def stop_active_openvpn() -> None:
    global active_openvpn_process, active_node_id
    cleanup_policy_routing()
    stop_process(active_openvpn_process)
    active_openvpn_process = None
    active_node_id = ""
    kill_existing_openvpn_processes()


def connect_node(node: dict[str, Any]) -> str:
    global active_openvpn_process, active_node_id
    stop_active_openvpn()
    config_path = Path(node["config_file"])
    config_path.write_text(node.get("config_text") or "", encoding="utf-8")
    ok, message, process = run_openvpn_until_ready(str(config_path), TUN_DEVICE, keep_alive=True)
    if not ok or process is None:
        raise RuntimeError(message)
    active_openvpn_process = process
    active_node_id = node["id"]
    setup_policy_routing(TUN_DEVICE)
    nodes = read_json(NODES_FILE, [])
    for item in nodes:
        item["active"] = item.get("id") == node["id"]
    write_json(NODES_FILE, nodes)
    state_update(active_openvpn_node_id=node["id"], last_check_message=f"Connected {node['id']}")
    return node["id"]


def is_preferred(node: dict[str, Any]) -> bool:
    return (
        node.get("country") == PREFERRED_COUNTRY
        and node.get("quality") == PREFERRED_QUALITY
        and node.get("ip_type") == PREFERRED_IP_TYPE
    )


def sorted_preferred(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    preferred = [n for n in nodes if n.get("probe_status") == "available" and is_preferred(n)]
    preferred.sort(key=lambda n: (parse_int(n.get("latency_ms")) or 999999, -parse_int(n.get("score"))))
    return preferred


def test_node(node: dict[str, Any], idx: int) -> dict[str, Any]:
    config_path = Path(node["config_file"])
    config_path.write_text(node.get("config_text") or "", encoding="utf-8")
    latency = ping_latency_ms(str(node.get("remote_host") or node.get("ip")), parse_int(node.get("remote_port")), parse_int(node.get("ping")))
    ok, message, _ = run_openvpn_until_ready(str(config_path), f"tun{idx}", keep_alive=False)
    result = dict(node)
    result["latency_ms"] = latency
    result["probe_status"] = "available" if ok else "unavailable"
    result["probe_message"] = message
    return result


def check_proxy_health() -> bool:
    if active_openvpn_process is None or active_openvpn_process.poll() is not None:
        return False
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.5)
        s.connect((PROXY_HOST, PROXY_PORT))
        s.close()
        return Path(f"/sys/class/net/{TUN_DEVICE}").exists()
    except Exception:
        return False


def create_connection(address: tuple[str, int], timeout: float = 20.0) -> socket.socket:
    host, port = address
    err = None
    for res in socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM):
        af, socktype, proto, _, sa = res
        sock = None
        try:
            sock = socket.socket(af, socktype, proto)
            sock.settimeout(timeout)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, TUN_DEVICE.encode("utf-8"))
            sock.connect(sa)
            return sock
        except OSError as exc:
            err = exc
            if sock is not None:
                sock.close()
    raise err or OSError("getaddrinfo failed")


def recv_exact(sock: socket.socket, size: int) -> bytes:
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("unexpected disconnect")
        data += chunk
    return data


def relay(left: socket.socket, right: socket.socket) -> None:
    sockets = [left, right]
    while True:
        readable, _, errored = select.select(sockets, [], sockets, 120)
        if errored:
            return
        for source in readable:
            target = right if source is left else left
            data = source.recv(65536)
            if not data:
                return
            target.sendall(data)


def socks5_client(client: socket.socket) -> None:
    upstream = None
    try:
        methods_count = recv_exact(client, 1)[0]
        recv_exact(client, methods_count)
        client.sendall(b"\x05\x00")
        version, command, _, address_type = recv_exact(client, 4)
        if version != 5 or command != 1:
            client.sendall(b"\x05\x07\x00\x01\x00\x00\x00\x00\x00\x00")
            return
        if address_type == 1:
            host = socket.inet_ntoa(recv_exact(client, 4))
        elif address_type == 3:
            host = recv_exact(client, recv_exact(client, 1)[0]).decode("idna")
        elif address_type == 4:
            host = socket.inet_ntop(socket.AF_INET6, recv_exact(client, 16))
        else:
            client.sendall(b"\x05\x08\x00\x01\x00\x00\x00\x00\x00\x00")
            return
        port = int.from_bytes(recv_exact(client, 2), "big")
        upstream = create_connection((host, port), timeout=20)
        client.sendall(b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00")
        relay(client, upstream)
    finally:
        client.close()
        if upstream:
            upstream.close()


def read_http_header(client: socket.socket, first_byte: bytes) -> bytes:
    data = first_byte
    while b"\r\n\r\n" not in data and len(data) < 65536:
        chunk = client.recv(4096)
        if not chunk:
            break
        data += chunk
    return data


def http_client(client: socket.socket, first_byte: bytes) -> None:
    upstream = None
    try:
        header = read_http_header(client, first_byte)
        head, rest = header.split(b"\r\n\r\n", 1)
        lines = head.decode("iso-8859-1", errors="replace").split("\r\n")
        method, target, version = lines[0].split(" ", 2)
        if method.upper() == "CONNECT":
            host, _, port_text = target.partition(":")
            port = parse_int(port_text) or 443
            upstream = create_connection((host, port), timeout=20)
            client.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            if rest:
                upstream.sendall(rest)
            relay(client, upstream)
            return
        from urllib.parse import urlsplit, urlunsplit
        parsed = urlsplit(target)
        if not parsed.hostname:
            client.sendall(b"HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n")
            return
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        path = urlunsplit(("", "", parsed.path or "/", parsed.query, ""))
        headers = [line for line in lines[1:] if not line.lower().startswith(("proxy-connection:", "connection:"))]
        request = f"{method} {path} {version}\r\n" + "\r\n".join(headers) + "\r\nConnection: close\r\n\r\n"
        upstream = create_connection((parsed.hostname, port), timeout=20)
        upstream.sendall(request.encode("iso-8859-1") + rest)
        relay(client, upstream)
    except Exception:
        try:
            client.sendall(b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n\r\n")
        except Exception:
            pass
    finally:
        client.close()
        if upstream:
            upstream.close()


def proxy_client(client: socket.socket) -> None:
    try:
        client.settimeout(30)
        first = recv_exact(client, 1)
        if first == b"\x05":
            socks5_client(client)
        else:
            http_client(client, first)
    except Exception:
        try:
            client.close()
        except Exception:
            pass


def start_proxy_server() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((PROXY_HOST, PROXY_PORT))
    server.listen(256)
    log(f"proxy listening on {PROXY_HOST}:{PROXY_PORT} via {TUN_DEVICE}")
    while True:
        client, _ = server.accept()
        threading.Thread(target=proxy_client, args=(client,), daemon=True).start()


def maintain() -> None:
    ensure_dirs()
    while True:
        try:
            nodes = read_json(NODES_FILE, [])
            active = next((n for n in nodes if n.get("active")), None)
            if active and is_preferred(active) and check_proxy_health():
                state_update(active_openvpn_node_id=active.get("id"), last_check_message=f"keep current preferred node: {active.get('id')}")
                time.sleep(CHECK_INTERVAL_SECONDS)
                continue

            candidates = fetch_candidates()
            write_json(NODES_FILE, candidates)
            tested = read_json(NODES_FILE, [])
            ordered = sorted(
                [n for n in tested if not n.get("active")],
                key=lambda n: (0 if n.get("country") == PREFERRED_COUNTRY else 1, -parse_int(n.get("score")), parse_int(n.get("ping"))),
            )
            idx_base = 10
            for start in range(0, len(ordered), SCAN_BATCH_SIZE):
                batch = ordered[start:start + SCAN_BATCH_SIZE]
                log(f"testing batch {start // SCAN_BATCH_SIZE + 1}: {[n['id'] for n in batch]}")
                results = []
                for offset, node in enumerate(batch, start=idx_base):
                    results.append(test_node(node, offset))
                enrich_ip_info(results)
                current = read_json(NODES_FILE, [])
                mapping = {n['id']: n for n in results}
                for item in current:
                    if item['id'] in mapping:
                        item.update(mapping[item['id']])
                write_json(NODES_FILE, current)
                preferred = sorted_preferred(current)
                if preferred:
                    chosen = preferred[0]
                    if not active or active.get("id") != chosen.get("id") or not check_proxy_health():
                        log(f"connecting preferred node: {chosen['id']}")
                        connect_node(chosen)
                    break
            else:
                log("no preferred residential node found in this round")
        except Exception as exc:
            log(f"maintain loop error: {exc}")
        time.sleep(CHECK_INTERVAL_SECONDS)


def print_config() -> None:
    print(json.dumps({
        "PREFERRED_COUNTRY": PREFERRED_COUNTRY,
        "PREFERRED_IP_TYPE": PREFERRED_IP_TYPE,
        "PREFERRED_QUALITY": PREFERRED_QUALITY,
        "PROXY_HOST": PROXY_HOST,
        "PROXY_PORT": PROXY_PORT,
        "TUN_DEVICE": TUN_DEVICE,
        "ROUTE_TABLE_ID": ROUTE_TABLE_ID,
        "DATA_DIR": str(DATA_DIR),
    }, ensure_ascii=False, indent=2))


def main() -> None:
    if "--print-config" in sys.argv:
        print_config()
        return
    ensure_dirs()
    threading.Thread(target=start_proxy_server, daemon=True).start()
    maintain()


if __name__ == "__main__":
    main()
