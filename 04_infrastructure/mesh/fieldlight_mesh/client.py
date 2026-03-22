"""TCP SIL sender (one request → one response per connection)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import socket

from . import sil
from .frame import read_frame, write_frame
from .logs import append_audit_log, append_routing_log, make_sys_id


def send_sil_file(
    *,
    host: str,
    port: int,
    payload_path: Path,
    node_short: str,
    routing_log_path: Path | None,
    audit_log_path: Path | None,
    log_writes: bool,
) -> dict[str, Any]:
    text = payload_path.read_text(encoding="utf-8")
    msg = sil.load_sil_yaml(text)
    sil.validate_inbound_sil(msg)
    body = sil.sil_to_yaml_bytes(msg)

    with socket.create_connection((host, port), timeout=30) as sock:
        wfile = sock.makefile("wb")
        rfile = sock.makefile("rb")
        write_frame(wfile, body)
        raw = read_frame(rfile)
        wfile.close()
        rfile.close()

    resp = sil.load_sil_yaml(raw.decode("utf-8"))

    if log_writes and routing_log_path:
        mid = sil.ensure_msg_id(msg)
        sys_id = make_sys_id(node_short)
        append_routing_log(
            routing_log_path,
            sys_id=sys_id,
            message_type=str(msg.get("message_type")),
            origin=str(msg.get("from")),
            destination=str(msg.get("to")),
            trust_level="outbound",
            status="sent",
            msg_id=mid,
        )
        if audit_log_path:
            append_audit_log(
                audit_log_path,
                msg_id=mid,
                message_type=str(msg.get("message_type")),
                direction="outbound",
                origin=str(msg.get("from")),
                destination=str(msg.get("to")),
                result="sent",
            )
        # Log received response summary
        append_routing_log(
            routing_log_path,
            sys_id=sys_id,
            message_type="response",
            origin=str(resp.get("from", "")),
            destination=str(resp.get("to", "")),
            trust_level="inbound",
            status=f"response_{resp.get('status', 'unknown')}",
            msg_id=str(resp.get("msg_id", "")),
            extra={"in_reply_to": resp.get("in_reply_to"), "intent": resp.get("intent")},
        )

    return resp
