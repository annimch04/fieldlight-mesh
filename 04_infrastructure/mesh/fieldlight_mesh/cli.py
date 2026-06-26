"""Installed operator CLI for local-first Fieldlight nodes."""

from __future__ import annotations

import argparse
import socket
import sys
from pathlib import Path
from typing import Any

import yaml

from .client import send_sil_message
from .identity import identity_exists, initialize_identity, load_identity
from .inbox import list_messages
from .peer_registry import load_registry, resolve_sil_address
from .routing import load_route_schema
from .server import SILMeshServer, load_trusted_peers
from .state import default_home, default_node_id, ensure_default_routes, initialize, load_config, load_yaml, paths, write_yaml
from .town_square import create_post, create_reply, export_bundle, import_bundle, list_objects, verify_store


def _home(args: argparse.Namespace) -> Path:
    return Path(args.home).expanduser()


def cmd_init(args: argparse.Namespace) -> int:
    home = _home(args)
    initialize(home, node_id=args.node_id, node_name=args.name, port=args.port, force=args.force)
    print(f"Initialized {args.node_id} at {home}")
    print("Security: plaintext trusted-LAN alpha; do not send sensitive content.")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    home = _home(args)
    failures = 0
    try:
        cfg = load_config(home)
        print(f"[ok] node: {cfg['node_id']}")
    except Exception as exc:
        print(f"[fail] configuration: {exc}")
        return 1
    p = paths(home)
    try:
        changed = ensure_default_routes(home)
        if changed:
            print("[ok] routes upgraded with packaged defaults")
    except Exception as exc:
        failures += 1
        print(f"[fail] route upgrade: {exc}")
    for label in ("routes", "trusted", "registry"):
        try:
            load_yaml(p[label], {})
            print(f"[ok] {label}: {p[label]}")
        except Exception as exc:
            failures += 1
            print(f"[fail] {label}: {exc}")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
        print("[ok] local TCP sockets")
    except OSError as exc:
        failures += 1
        print(f"[fail] local TCP sockets: {exc}")
    try:
        import zeroconf  # noqa: F401
        print("[ok] mDNS discovery extra")
    except ImportError:
        print("[warn] mDNS unavailable; install fieldlight-mesh[discovery]")
    print("[warn] transport is plaintext; use only a trusted LAN or encrypted overlay")
    return 1 if failures else 0


def _server_config(home: Path, cfg: dict[str, Any]) -> dict[str, Any]:
    p = paths(home)
    ensure_default_routes(home)
    return {
        "routes": load_route_schema(p["routes"]),
        "node_id": cfg["node_id"],
        "node_short": str(cfg.get("node_name", "node")).upper(),
        "trusted_peers": load_trusted_peers(p["trusted"]),
        "routing_log_path": p["routing_log"],
        "audit_log_path": p["audit_log"],
        "inbox_path": p["inbox"],
        "town_square_path": p["town_square"],
        "log_writes": True,
        "socket_timeout": 10.0,
    }


def cmd_node(args: argparse.Namespace) -> int:
    home = _home(args)
    cfg = load_config(home)
    host = args.host or str(cfg.get("host", "0.0.0.0"))
    port = args.port or int(cfg.get("port", 7750))
    server = SILMeshServer((host, port), _server_config(home, cfg))
    zc = info = None
    if args.advertise:
        try:
            from zeroconf import Zeroconf
            from .lan_mdns import build_fieldlight_service
        except ImportError:
            server.server_close()
            print("error: --advertise requires fieldlight-mesh[discovery]", file=sys.stderr)
            return 2
        info = build_fieldlight_service(
            instance=f"fieldlight-{cfg.get('node_name', 'node')}", port=port, mesh_uri=str(cfg["node_id"])
        )
        zc = Zeroconf()
        zc.register_service(info)
        print(f"Advertising {cfg['node_id']} via _fieldlight._tcp")
    print(f"Fieldlight node {cfg['node_id']} listening on {host}:{port}")
    print("WARNING: plaintext TCP alpha; trusted LAN or encrypted overlay only.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        server.server_close()
        if zc and info:
            zc.unregister_service(info)
            zc.close()
    return 0


def _registry_entries(home: Path) -> list[dict[str, Any]]:
    return load_registry(paths(home)["registry"])["entries"]


def cmd_peers(args: argparse.Namespace) -> int:
    home = _home(args)
    load_config(home)
    p = paths(home)
    if args.peer_action == "list":
        trusted = load_trusted_peers(p["trusted"]) or set()
        entries = _registry_entries(home)
        if not entries and not trusted:
            print("No peers enrolled.")
        for entry in entries:
            uri = str(entry.get("mesh_uri", ""))
            mark = "trusted" if uri in trusted else "untrusted"
            print(f"{uri}  {entry.get('host')}:{entry.get('port')}  {mark}")
        for uri in sorted(trusted - {str(e.get('mesh_uri')) for e in entries}):
            print(f"{uri}  no address  trusted")
        return 0
    if args.peer_action == "discover":
        try:
            from .lan_mdns import collect_lan_advertisements
            from .peer_registry import merge_registry
        except ImportError:
            print("error: discovery requires fieldlight-mesh[discovery]", file=sys.stderr)
            return 2
        reg = load_registry(p["registry"])
        rows = collect_lan_advertisements(duration=args.duration)
        merged = merge_registry(reg, rows)
        write_yaml(p["registry"], merged)
        print(f"Discovered {len(rows)} advertisement(s); none were automatically trusted.")
        return 0
    if args.peer_action == "add":
        reg = load_registry(p["registry"])
        reg["entries"] = [e for e in reg["entries"] if e.get("mesh_uri") != args.uri]
        reg["entries"].append(
            {"mesh_uri": args.uri, "host": args.host, "port": args.port, "source": "manual"}
        )
        write_yaml(p["registry"], reg)
        print(f"Added address for {args.uri}")
        return 0
    trusted_data = load_yaml(p["trusted"], {"peers": []})
    peers = {str(x) for x in trusted_data.get("peers", [])}
    if args.peer_action == "trust":
        peers.add(args.uri)
        verb = "Trusted"
    else:
        peers.discard(args.uri)
        verb = "Untrusted"
    write_yaml(p["trusted"], {"peers": sorted(peers)})
    print(f"{verb} {args.uri}")
    return 0


def cmd_send_message(args: argparse.Namespace) -> int:
    home = _home(args)
    cfg = load_config(home)
    if args.host:
        host, port = args.host, args.port or 7750
    else:
        resolved = resolve_sil_address(_registry_entries(home), args.to)
        if not resolved:
            print(f"error: no address for {args.to}; use peers add or --host", file=sys.stderr)
            return 2
        host, port = resolved
    msg = {
        "message_type": "message",
        "from": cfg["node_id"],
        "to": args.to,
        "intent": "human_message",
        "body": args.text,
    }
    p = paths(home)
    resp = send_sil_message(
        host=host, port=port, msg=msg,
        node_short=str(cfg.get("node_name", "node")).upper(),
        routing_log_path=p["routing_log"], audit_log_path=p["audit_log"], log_writes=True,
    )
    print(yaml.safe_dump(resp, default_flow_style=False, sort_keys=False), end="")
    return 0 if int(resp.get("status", 500)) < 400 else 1


def cmd_inbox(args: argparse.Namespace) -> int:
    home = _home(args)
    load_config(home)
    messages = list_messages(paths(home)["inbox"], limit=args.limit)
    if not messages:
        print("Inbox empty.")
        return 0
    for row in messages:
        msg = row["message"]
        print(f"{row['received_at']}  {row['from']}  {row['msg_id']}")
        print(f"  {msg.get('body', '')}")
    return 0


def cmd_identity(args: argparse.Namespace) -> int:
    home = _home(args)
    cfg = load_config(home)
    if args.identity_action == "init":
        record = initialize_identity(
            home,
            node_id=str(cfg["node_id"]),
            label=args.label or str(cfg.get("node_name", "node")),
            force=args.force,
        )
        print(yaml.safe_dump(record, default_flow_style=False, sort_keys=False), end="")
        return 0
    record = load_identity(home)
    if args.identity_action == "show":
        print(yaml.safe_dump(record, default_flow_style=False, sort_keys=False), end="")
        return 0
    if args.identity_action == "export":
        Path(args.path).expanduser().write_text(
            yaml.safe_dump(record, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
        print(f"Exported public identity to {args.path}")
        return 0
    raise ValueError(f"unknown identity action: {args.identity_action}")


def _print_town_objects(rows: list[dict[str, Any]]) -> None:
    if not rows:
        print("Town Square empty.")
        return
    for obj in rows:
        content = obj.get("content", {})
        refs = obj.get("refs", {})
        body = content.get("body", "") if isinstance(content, dict) else ""
        suffix = f" reply_to={refs.get('reply_to')}" if isinstance(refs, dict) and refs.get("reply_to") else ""
        print(f"{obj.get('created_at')}  {obj.get('author')}  {obj.get('object_id')}{suffix}")
        print(f"  {body}")


def cmd_town(args: argparse.Namespace) -> int:
    home = _home(args)
    cfg = load_config(home)
    ensure_default_routes(home)
    p = paths(home)
    if args.town_action in {"post", "reply"} and not identity_exists(home):
        initialize_identity(home, node_id=str(cfg["node_id"]), label=str(cfg.get("node_name", "node")))
    if args.town_action == "post":
        obj = create_post(p["town_square"], home, args.text)
        print(f"posted {obj['object_id']}")
        return 0
    if args.town_action == "reply":
        obj = create_reply(p["town_square"], home, args.text, parent=args.parent)
        print(f"replied {obj['object_id']}")
        return 0
    if args.town_action == "list":
        _print_town_objects(list_objects(p["town_square"], limit=args.limit))
        return 0
    if args.town_action == "verify":
        print(yaml.safe_dump(verify_store(p["town_square"]), default_flow_style=False, sort_keys=False), end="")
        return 0
    if args.town_action == "export":
        bundle = export_bundle(p["town_square"], limit=args.limit)
        Path(args.path).expanduser().write_text(
            yaml.safe_dump(bundle, default_flow_style=False, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        print(f"Exported {len(bundle['objects'])} object(s) to {args.path}")
        return 0
    if args.town_action == "import":
        bundle = yaml.safe_load(Path(args.path).expanduser().read_text(encoding="utf-8"))
        summary = import_bundle(p["town_square"], bundle)
        print(yaml.safe_dump(summary, default_flow_style=False, sort_keys=False), end="")
        return 0
    if args.town_action == "sync":
        resolved = resolve_sil_address(_registry_entries(home), args.to)
        if not resolved:
            print(f"error: no address for {args.to}; use peers add or --host", file=sys.stderr)
            return 2
        bundle = export_bundle(p["town_square"], limit=args.limit)
        resp = send_sil_message(
            host=resolved[0], port=resolved[1],
            msg={"message_type": "town_square_bundle", "from": cfg["node_id"], "to": args.to,
                 "intent": "town_square_sync", "bundle": bundle},
            node_short=str(cfg.get("node_name", "node")).upper(),
            routing_log_path=p["routing_log"], audit_log_path=p["audit_log"], log_writes=True,
        )
        print(yaml.safe_dump(resp, default_flow_style=False, sort_keys=False), end="")
        return 0 if int(resp.get("status", 500)) < 400 else 1
    raise ValueError(f"unknown town action: {args.town_action}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="fieldlight-mesh", description="Fieldlight local-first mesh alpha")
    p.add_argument("--home", default=str(default_home()), help="Node state directory")
    sub = p.add_subparsers(dest="command", required=True)
    i = sub.add_parser("init", help="Initialize a node")
    i.add_argument("--name", required=True)
    i.add_argument("--node-id", default=default_node_id())
    i.add_argument("--port", type=int, default=7750)
    i.add_argument("--force", action="store_true")
    i.set_defaults(func=cmd_init)
    d = sub.add_parser("doctor", help="Check local readiness")
    d.set_defaults(func=cmd_doctor)
    n = sub.add_parser("node", help="Run receiver and optional LAN advertisement")
    n.add_argument("--host")
    n.add_argument("--port", type=int)
    n.add_argument("--advertise", action="store_true")
    n.set_defaults(func=cmd_node)
    peers = sub.add_parser("peers", help="Manage peer addresses and trust")
    ps = peers.add_subparsers(dest="peer_action", required=True)
    ps.add_parser("list")
    pd = ps.add_parser("discover")
    pd.add_argument("--duration", type=float, default=8.0)
    pa = ps.add_parser("add")
    pa.add_argument("uri")
    pa.add_argument("--host", required=True)
    pa.add_argument("--port", type=int, default=7750)
    for action in ("trust", "untrust"):
        q = ps.add_parser(action)
        q.add_argument("uri")
    peers.set_defaults(func=cmd_peers)
    s = sub.add_parser("send-message", help="Send a text message")
    s.add_argument("to")
    s.add_argument("text")
    s.add_argument("--host")
    s.add_argument("--port", type=int)
    s.set_defaults(func=cmd_send_message)
    inbox = sub.add_parser("inbox", help="Read received messages")
    inbox.add_argument("--limit", type=int, default=50)
    inbox.set_defaults(func=cmd_inbox)
    identity = sub.add_parser("identity", help="Manage Ed25519 node identity")
    ids = identity.add_subparsers(dest="identity_action", required=True)
    ii = ids.add_parser("init", help="Create local signing identity")
    ii.add_argument("--label")
    ii.add_argument("--force", action="store_true")
    ids.add_parser("show", help="Show public identity")
    ie = ids.add_parser("export", help="Export public identity YAML")
    ie.add_argument("path")
    identity.set_defaults(func=cmd_identity)
    town = sub.add_parser("town", help="Signed public Town Square feed")
    ts = town.add_subparsers(dest="town_action", required=True)
    tp = ts.add_parser("post", help="Create a signed public post")
    tp.add_argument("text")
    tr = ts.add_parser("reply", help="Create a signed public reply")
    tr.add_argument("parent")
    tr.add_argument("text")
    tl = ts.add_parser("list", help="List local Town Square objects")
    tl.add_argument("--limit", type=int, default=50)
    tv = ts.add_parser("verify", help="Verify local Town Square signatures")
    te = ts.add_parser("export", help="Export signed Town Square bundle")
    te.add_argument("path")
    te.add_argument("--limit", type=int, default=500)
    ti = ts.add_parser("import", help="Import signed Town Square bundle")
    ti.add_argument("path")
    ty = ts.add_parser("sync", help="Send signed Town Square bundle to a trusted peer")
    ty.add_argument("to")
    ty.add_argument("--limit", type=int, default=500)
    town.set_defaults(func=cmd_town)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (FileExistsError, FileNotFoundError, ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
