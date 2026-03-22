"""Append-only YAML logs aligned with fieldlight_mesh_log_function / templates."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def _utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ensure_file(path: Path, starter: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(starter, f, default_flow_style=False, sort_keys=False)
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def _write_file(path: Path, data: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


def append_routing_log(
    path: Path,
    *,
    sys_id: str,
    message_type: str,
    origin: str,
    destination: str,
    trust_level: str,
    status: str,
    ttl: int | None = None,
    auth: str | None = None,
    msg_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    starter = {
        "header": [
            "msg_id",
            "message_type",
            "origin",
            "destination",
            "trust_level",
            "status",
            "timestamp",
        ],
        "entries": [],
    }
    data = _ensure_file(path, starter)
    entries = data.setdefault("entries", [])
    entry: dict[str, Any] = {
        "sys": sys_id,
        "type": "mesh-send",
        "message_type": message_type,
        "origin": origin,
        "destination": destination,
        "trust_level": trust_level,
        "status": status,
        "timestamp": _utc_ts(),
    }
    if msg_id is not None:
        entry["msg_id"] = msg_id
    if ttl is not None:
        entry["ttl"] = ttl
    if auth is not None:
        entry["auth"] = auth
    if extra:
        entry.update(extra)
    entries.append(entry)
    _write_file(path, data)


def append_audit_log(
    path: Path,
    *,
    msg_id: str,
    message_type: str,
    direction: str,
    origin: str,
    destination: str,
    result: str,
) -> None:
    starter = {
        "header": [
            "msg_id",
            "message_type",
            "direction",
            "origin",
            "destination",
            "result",
            "timestamp",
        ],
        "entries": [],
    }
    data = _ensure_file(path, starter)
    entries = data.setdefault("entries", [])
    entries.append(
        {
            "msg_id": msg_id,
            "message_type": message_type,
            "direction": direction,
            "origin": origin,
            "destination": destination,
            "result": result,
            "timestamp": _utc_ts(),
        }
    )
    _write_file(path, data)


def make_sys_id(node_short: str) -> str:
    """Human-readable correlation id (style: FL-LEMUR-YYYYMMDD-HHMMSS)."""
    return f"FL-{node_short}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
