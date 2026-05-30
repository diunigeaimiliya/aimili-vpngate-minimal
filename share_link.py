#!/usr/bin/env python3
from __future__ import annotations

import argparse
import urllib.parse


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--server', required=True)
    p.add_argument('--port', required=True)
    p.add_argument('--uuid', required=True)
    p.add_argument('--public-key', required=True)
    p.add_argument('--short-id', required=True)
    p.add_argument('--remark', default='家宽')
    args = p.parse_args()

    query = {
        'remarks': args.remark,
        'tls': '1',
        'peer': 'www.cloudflare.com',
        'udp': '1',
        'xtls': '2',
        'pbk': args.public_key,
        'sid': args.short_id,
    }
    print(f"vless://{args.uuid}@{args.server}:{args.port}?{urllib.parse.urlencode(query)}")


if __name__ == '__main__':
    main()
