#!/usr/bin/env python3
"""
Register this host on LAN mDNS as _fieldlight._tcp with bridge TXT keys.

Runs until Ctrl+C. See docs/DISCOVERY_PLAN.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_MESH_ROOT = Path(__file__).resolve().parents[1]
if str(_MESH_ROOT) not in sys.path:
    sys.path.insert(0, str(_MESH_ROOT))

from zeroconf import Zeroconf

from fieldlight_mesh.lan_mdns import build_fieldlight_service


def main() -> int:
    p = argparse.ArgumentParser(description="Advertise Fieldlight SIL listener via mDNS (_fieldlight._tcp).")
    p.add_argument(
        "--instance",
        default="fieldlight-node",
        help="mDNS instance name (safe characters; no spaces recommended)",
    )
    p.add_argument("--port", type=int, default=7750, help="SIL TCP port (sil_mesh receive)")
    p.add_argument(
        "--mesh-uri",
        default="mesh://fieldlight.anni.lemur",
        help="SIL mesh URI (TXT mesh_uri)",
    )
    p.add_argument("--peer", default=None, help="Optional libp2p Peer ID (TXT peer)")
    p.add_argument("--txt-version", default="1", help="TXT schema version (v)")
    args = p.parse_args()

    info = build_fieldlight_service(
        instance=args.instance,
        port=args.port,
        mesh_uri=args.mesh_uri,
        peer_id=args.peer,
        txt_version=args.txt_version,
    )
    zc = Zeroconf()
    try:
        zc.register_service(info)
        print(
            f"Registered {info.name!r} port={args.port} mesh_uri={args.mesh_uri!r}\n"
            "Ctrl+C to unregister and exit.",
            flush=True,
        )
        while True:
            import time

            time.sleep(3600)
    except KeyboardInterrupt:
        print("\nUnregistering…", flush=True)
    finally:
        zc.unregister_service(info)
        zc.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
