#!/usr/bin/env python3
"""
Browse LAN mDNS for Fieldlight service advertisements (Added/Removed ≈ join/leave).

See docs/DISCOVERY_PLAN.md for service type (_fieldlight._tcp) and TXT keys.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

_MESH_ROOT = Path(__file__).resolve().parents[1]
if str(_MESH_ROOT) not in sys.path:
    sys.path.insert(0, str(_MESH_ROOT))

try:
    from zeroconf import ServiceBrowser, ServiceInfo, ServiceListener, Zeroconf
except ImportError:
    print("Missing dependency: pip install zeroconf (see requirements.txt)", file=sys.stderr)
    sys.exit(1)

from fieldlight_mesh.lan_mdns import decode_txt, is_legacy_fieldlight_http_name, resolve_mdns_service


def _txt_summary(info: ServiceInfo | None) -> str:
    d = decode_txt(info)
    if not d:
        return ""
    return " ".join(f"{k}={d[k]}" for k in sorted(d))


def _addrs(info: ServiceInfo | None) -> str:
    if not info:
        return ""
    try:
        addrs = list(info.parsed_addresses())
    except Exception:
        return ""
    return ", ".join(addrs) if addrs else ""


class FieldlightListener(ServiceListener):
    def __init__(self, *, legacy_http: bool, verbose: bool) -> None:
        self.legacy_http = legacy_http
        self.verbose = verbose

    def _want_http(self, name: str) -> bool:
        return self.legacy_http and is_legacy_fieldlight_http_name(name)

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        if type_.startswith("_http._tcp") and not self._want_http(name):
            return
        info = resolve_mdns_service(zc, type_, name)
        txt = _txt_summary(info)
        addr = _addrs(info)
        port = info.port if info else "?"
        line = f"[+] added  type={type_!r} name={name!r} port={port}"
        if addr:
            line += f" addrs=[{addr}]"
        if txt:
            line += f" txt=[{txt}]"
        print(line, flush=True)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        if type_.startswith("_http._tcp") and not self._want_http(name):
            return
        print(f"[-] removed type={type_!r} name={name!r}", flush=True)

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        if not self.verbose:
            return
        if type_.startswith("_http._tcp") and not self._want_http(name):
            return
        info = resolve_mdns_service(zc, type_, name, timeout_ms=1500)
        txt = _txt_summary(info)
        addr = _addrs(info)
        port = info.port if info else "?"
        print(
            f"[~] update type={type_!r} name={name!r} port={port} addrs=[{addr}] txt=[{txt}]",
            flush=True,
        )


def main() -> int:
    p = argparse.ArgumentParser(description="Browse Fieldlight LAN mDNS presence.")
    p.add_argument(
        "--legacy-http",
        action="store_true",
        help="Also browse _http._tcp; only print instances whose name contains 'fieldlight' (case-insensitive).",
    )
    p.add_argument(
        "--duration",
        type=float,
        default=0.0,
        metavar="SEC",
        help="Stop after SEC seconds (0 = run until Ctrl+C).",
    )
    p.add_argument("-v", "--verbose", action="store_true", help="Log TXT update events from mDNS.")
    args = p.parse_args()

    listener = FieldlightListener(legacy_http=args.legacy_http, verbose=args.verbose)
    zc = Zeroconf()
    browsers: list[ServiceBrowser] = []
    try:
        browsers.append(ServiceBrowser(zc, "_fieldlight._tcp.local.", listener))
        if args.legacy_http:
            browsers.append(ServiceBrowser(zc, "_http._tcp.local.", listener))
        print(
            "Listening for mDNS services (Fieldlight). Ctrl+C to stop.\n"
            f"  _fieldlight._tcp.local. — always\n"
            + (
                "  _http._tcp.local. — Fieldlight-named instances only\n"
                if args.legacy_http
                else "  (use --legacy-http to also watch _http._tcp)\n"
            ),
            flush=True,
        )
        if args.duration > 0:
            time.sleep(args.duration)
        else:
            while True:
                time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)
    finally:
        zc.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
