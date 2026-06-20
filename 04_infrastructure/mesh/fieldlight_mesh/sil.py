"""Parse and validate minimal SIL (Signal Intent Language) documents."""

from __future__ import annotations

from typing import Any, Mapping

import yaml

REQUIRED_TOP_LEVEL = ("message_type", "from", "to")


def load_sil_yaml(text: str) -> dict[str, Any]:
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("SIL root must be a mapping")
    return data


def validate_inbound_sil(msg: Mapping[str, Any]) -> None:
    missing = [k for k in REQUIRED_TOP_LEVEL if k not in msg or msg[k] in (None, "")]
    if missing:
        raise ValueError(f"missing required SIL fields: {missing}")
    for key in REQUIRED_TOP_LEVEL:
        if not isinstance(msg[key], str) or not str(msg[key]).strip():
            raise ValueError(f"SIL field {key!r} must be a non-empty string")
        if len(str(msg[key])) > 512:
            raise ValueError(f"SIL field {key!r} is too long")


def ensure_msg_id(msg: dict[str, Any]) -> str:
    mid = msg.get("msg_id")
    if mid:
        return str(mid)
    # Auto id when schema says msg_id: auto
    import hashlib
    import time

    blob = yaml.safe_dump(dict(sorted(msg.items())), sort_keys=True).encode()
    mid = "auto-" + hashlib.sha256(blob + str(time.time_ns()).encode()).hexdigest()[:16]
    msg["msg_id"] = mid
    return mid


def sil_to_yaml_bytes(msg: dict[str, Any]) -> bytes:
    return yaml.safe_dump(
        msg,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    ).encode("utf-8")
