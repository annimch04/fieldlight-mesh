#!/usr/bin/env python3
"""CLI for Fieldlight SIL over TCP: send, receive, LAN/libp2p discover → peer registry."""

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


def cmd_discover(args: argparse.Namespace) -> int:
    from fieldlight_mesh.lan_mdns import collect_lan_advertisements
    from fieldlight_mesh.peer_registry import (
        dump_registry,
        load_libp2p_jsonl,
        load_registry,
        merge_registry,
    )

    libp2p_entries = None
    if args.libp2p_jsonl:
        use_stdin = args.libp2p_jsonl.strip() == "-"
        if not use_stdin:
            p = Path(args.libp2p_jsonl)
            if not p.is_file():
                print(f"error: --libp2p-jsonl not a file: {p}", file=sys.stderr)
                return 1
        libp2p_entries = load_libp2p_jsonl(
            None if use_stdin else Path(args.libp2p_jsonl),
            stdin=use_stdin,
        )

    if args.skip_lan and not args.libp2p_jsonl:
        print(
            "error: --skip-lan requires --libp2p-jsonl (or drop --skip-lan for LAN scan)",
            file=sys.stderr,
        )
        return 1

    lan_rows = None if args.skip_lan else collect_lan_advertisements(
        duration=args.duration, legacy_http=args.legacy_http
    )

    default_out = _MESH_ROOT / "config" / "discovered_peers.yml"
    out_path = Path(args.output) if args.output else default_out

    if args.merge and out_path.exists():
        payload_base = load_registry(out_path)
    else:
        payload_base = {"version": 1, "entries": []}

    payload = merge_registry(payload_base, lan_rows, libp2p_entries=libp2p_entries)

    if args.stdout:
        print(dump_registry(payload), end="")
        return 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(dump_registry(payload), encoding="utf-8")
    scan_note = "LAN skipped" if args.skip_lan else f"LAN {args.duration}s"
    p2p_note = f", libp2p {args.libp2p_jsonl!r}" if args.libp2p_jsonl else ""
    print(
        f"Wrote {len(payload['entries'])} entr(y/ies) to {out_path} ({scan_note}{p2p_note}).",
        flush=True,
    )
    return 0


def cmd_send(args: argparse.Namespace) -> int:
    from fieldlight_mesh.client import send_sil_file
    from fieldlight_mesh.peer_registry import load_registry, resolve_sil_address
    from fieldlight_mesh.sil import load_sil_yaml

    schema_path, routing_log, audit_log = _default_paths()
    _ = schema_path  # send uses receiver's schema; kept for symmetry

    rlog = Path(args.routing_log) if args.routing_log else routing_log
    alog = Path(args.audit_log) if args.audit_log else audit_log

    host, port = args.host, args.port
    if args.use_registry:
        reg_path = Path(args.registry) if args.registry else _MESH_ROOT / "config" / "discovered_peers.yml"
        payload_path = Path(args.payload)
        msg = load_sil_yaml(payload_path.read_text(encoding="utf-8"))
        target = args.resolve_to or msg.get("to")
        if not target:
            print(
                "error: --use-registry requires a SIL `to` field or --resolve-to mesh://…",
                file=sys.stderr,
            )
            return 1
        reg = load_registry(reg_path)
        resolved = resolve_sil_address(reg["entries"], str(target))
        if not resolved:
            print(
                f"error: no SIL host/port in registry for {target!r} ({reg_path})",
                file=sys.stderr,
            )
            return 1
        host, port = resolved
        print(f"Registry dial {target} -> {host}:{port}", flush=True)

    resp = send_sil_file(
        host=host,
        port=port,
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
    s.add_argument(
        "--use-registry",
        action="store_true",
        help="Resolve --host/--port from registry using payload `to` or --resolve-to",
    )
    s.add_argument(
        "--resolve-to",
        default=None,
        metavar="MESH_URI",
        help="Destination mesh URI for registry lookup (overrides payload `to` when set)",
    )
    s.add_argument(
        "--registry",
        default=None,
        help="Peer registry YAML (default: config/discovered_peers.yml)",
    )
    s.add_argument("--node-short", default="LEMUR")
    s.add_argument("--routing-log", default=None)
    s.add_argument("--audit-log", default=None)
    s.add_argument("--no-log", action="store_true")
    s.set_defaults(func=cmd_send)

    d = sub.add_parser(
        "discover",
        help="Scan LAN mDNS and/or merge libp2p JSONL into peer registry YAML",
    )
    d.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="Seconds to browse (longer catches slow responders)",
    )
    d.add_argument(
        "--legacy-http",
        action="store_true",
        help="Include legacy _http._tcp instances with 'fieldlight' in the name",
    )
    d.add_argument(
        "--output",
        "-o",
        default=None,
        help="Registry YAML path (default: config/discovered_peers.yml under mesh root)",
    )
    d.add_argument(
        "--merge",
        action="store_true",
        help="Merge with existing --output file instead of replacing non-scan fields",
    )
    d.add_argument(
        "--stdout",
        action="store_true",
        help="Print registry YAML to stdout only; do not write a file",
    )
    d.add_argument(
        "--skip-lan",
        action="store_true",
        help="Do not run mDNS scan (requires --libp2p-jsonl)",
    )
    d.add_argument(
        "--libp2p-jsonl",
        default=None,
        metavar="PATH",
        help="Merge JSON lines from libp2p_peer_probe (use '-' for stdin)",
    )
    d.set_defaults(func=cmd_discover)

    args = p.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
