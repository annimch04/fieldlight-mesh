#!/usr/bin/env python3
"""CLI for Fieldlight SIL over TCP (send / receive)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow `python scripts/sil_mesh.py` without installation
_MESH_ROOT = Path(__file__).resolve().parents[1]
if str(_MESH_ROOT) not in sys.path:
    sys.path.insert(0, str(_MESH_ROOT))


def _default_paths() -> tuple[Path, Path, Path]:
    root = _MESH_ROOT
    return (
        root / "config" / "lemur_route_schema.yml",
        root / "logs" / "routing_log.yml",
        root / "logs" / "message_audit_log.yml",
    )


def cmd_receive(args: argparse.Namespace) -> int:
    from fieldlight_mesh.routing import load_route_schema
    from fieldlight_mesh.server import SILMeshServer, load_trusted_peers

    schema, routing_log, audit_log = _default_paths()
    if args.schema:
        schema = Path(args.schema)
    routes = load_route_schema(schema)

    trusted = load_trusted_peers(Path(args.trusted_peers)) if args.trusted_peers else None

    cfg = {
        "routes": routes,
        "node_id": args.node_id,
        "node_short": args.node_short,
        "trusted_peers": trusted,
        "routing_log_path": Path(args.routing_log) if args.routing_log else routing_log,
        "audit_log_path": Path(args.audit_log) if args.audit_log else audit_log,
        "log_writes": not args.no_log,
    }

    addr = (args.host, args.port)
    server = SILMeshServer(addr, cfg)
    print(
        f"SIL mesh receive on {args.host}:{args.port} as {args.node_id} (schema={schema})",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping.", flush=True)
        server.shutdown()
    return 0


def cmd_send(args: argparse.Namespace) -> int:
    from fieldlight_mesh.client import send_sil_file

    schema_path, routing_log, audit_log = _default_paths()
    _ = schema_path  # send uses receiver's schema; kept for symmetry

    rlog = Path(args.routing_log) if args.routing_log else routing_log
    alog = Path(args.audit_log) if args.audit_log else audit_log

    resp = send_sil_file(
        host=args.host,
        port=args.port,
        payload_path=Path(args.payload),
        node_short=args.node_short,
        routing_log_path=rlog if not args.no_log else None,
        audit_log_path=alog if not args.no_log else None,
        log_writes=not args.no_log,
    )
    import yaml

    print(yaml.safe_dump(resp, default_flow_style=False, sort_keys=False))
    return 0


def main() -> int:
    schema_d, _, _ = _default_paths()
    p = argparse.ArgumentParser(description="Fieldlight SIL TCP mesh (v1)")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("receive", help="Listen for SIL messages and reply")
    r.add_argument("--host", default="127.0.0.1")
    r.add_argument("--port", type=int, default=7750)
    r.add_argument(
        "--node-id",
        default="mesh://fieldlight.anni.lemur",
        help="This node's mesh URI (must match SIL 'to' field)",
    )
    r.add_argument("--node-short", default="LEMUR", help="Short tag for sys: FL-<short>-...")
    r.add_argument("--schema", default=None, help=f"Route schema YAML (default: {schema_d})")
    r.add_argument("--routing-log", default=None, help="routing_log.yml path")
    r.add_argument("--audit-log", default=None, help="message_audit_log.yml path")
    r.add_argument("--trusted-peers", default=None, help="YAML list of allowed mesh:// sender IDs")
    r.add_argument("--no-log", action="store_true", help="Do not append logs")
    r.set_defaults(func=cmd_receive)

    s = sub.add_parser("send", help="Send one SIL YAML file and print response")
    s.add_argument("payload", help="Path to SIL .yml file")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=7750)
    s.add_argument("--node-short", default="LEMUR")
    s.add_argument("--routing-log", default=None)
    s.add_argument("--audit-log", default=None)
    s.add_argument("--no-log", action="store_true")
    s.set_defaults(func=cmd_send)

    args = p.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
