"""Core SIL request/response handling (routing schema + status codes)."""

from __future__ import annotations

from typing import Any

from . import routing as R
from . import sil
from .logs import append_audit_log, append_routing_log, log_nonfatal_warning, make_sys_id


def _response(
    *,
    node_id: str,
    to_peer: str,
    in_reply_to: str,
    status: int,
    intent: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    # Semantic routing: `to` is the peer mesh id (equals inbound `from`).
    # Bytes return on the same TCP connection (see docs/INGRESS_CONTRACT.md).
    m: dict[str, Any] = {
        "message_type": "response",
        "from": node_id,
        "to": to_peer,
        "in_reply_to": in_reply_to,
        "status": status,
        "intent": intent,
    }
    if extra:
        m.update(extra)
    m["msg_id"] = sil.ensure_msg_id(m)
    return m


def handle_inbound_sil(
    msg: dict[str, Any],
    *,
    routes: dict[str, Any],
    node_id: str,
    node_short: str,
    trusted_peers: set[str] | None,
    routing_log_path: Any,
    audit_log_path: Any | None,
    log_writes: bool,
) -> dict[str, Any]:
    sil.validate_inbound_sil(msg)
    mt = str(msg["message_type"])
    sender = str(msg["from"])
    mid = sil.ensure_msg_id(msg)

    route = R.route_for_message_type(routes, mt)
    sys_id = make_sys_id(node_short)

    def log_route(status: str, trust_level: str, auth_note: str | None = None) -> None:
        """Never raises — log failures must not block receive/respond."""
        if not log_writes:
            return
        try:
            append_routing_log(
                routing_log_path,
                sys_id=sys_id,
                message_type=mt,
                origin=sender,
                destination=str(msg.get("to")),
                trust_level=trust_level,
                status=status,
                ttl=route.get("ttl"),
                auth=auth_note,
                msg_id=mid,
            )
            if audit_log_path:
                append_audit_log(
                    audit_log_path,
                    msg_id=mid,
                    message_type=mt,
                    direction="inbound",
                    origin=sender,
                    destination=str(msg.get("to")),
                    result=status,
                )
        except Exception as exc:
            log_nonfatal_warning(exc, "append_routing_log/audit")

    if not R.destination_matches_node(str(msg["to"]), node_id):
        log_route("not_delivered", "unknown", "wrong_destination")
        return _response(
            node_id=node_id,
            to_peer=sender,
            in_reply_to=mid,
            status=404,
            intent="no_route_to_peer",
            extra={"detail": "to does not match this node"},
        )

    if R.ttl_exceeded(route, msg):
        log_route("ttl_exceeded", str(route.get("trust_required", "peer")), None)
        return _response(
            node_id=node_id,
            to_peer=sender,
            in_reply_to=mid,
            status=410,
            intent="ttl_exceeded",
        )

    tr = str(route.get("trust_required", "any"))
    if not R.trust_allows_sender(tr, sender, trusted_peers):
        log_route("unauthorized", tr, "trust")
        return _response(
            node_id=node_id,
            to_peer=sender,
            in_reply_to=mid,
            status=403,
            intent="trust_denied",
        )

    ok, reason = R.auth_ok(route, msg)
    if not ok:
        log_route("unauthorized", tr, reason)
        return _response(
            node_id=node_id,
            to_peer=sender,
            in_reply_to=mid,
            status=403,
            intent="auth_failed",
            extra={"detail": reason},
        )

    # Delivered
    trust_level = tr
    log_route("delivered", trust_level, reason if ok else None)

    if mt == "ping":
        return _response(
            node_id=node_id,
            to_peer=sender,
            in_reply_to=mid,
            status=200,
            intent="pong",
        )

    if mt == "echo":
        return _response(
            node_id=node_id,
            to_peer=sender,
            in_reply_to=mid,
            status=202,
            intent="echo_reflected",
            extra={"reflected": {k: msg.get(k) for k in ("message_type", "from", "to", "intent") if k in msg}},
        )

    if mt == "handshake":
        return _response(
            node_id=node_id,
            to_peer=sender,
            in_reply_to=mid,
            status=200,
            intent="handshake_ack",
        )

    if mt == "query":
        return _response(
            node_id=node_id,
            to_peer=sender,
            in_reply_to=mid,
            status=200,
            intent="query_stub",
            extra={"answer": {"note": "placeholder — wire real handler in Phase 4"}},
        )

    if mt == "trace":
        return _response(
            node_id=node_id,
            to_peer=sender,
            in_reply_to=mid,
            status=200,
            intent="trace_received",
        )

    if mt == "response":
        # Responses are logged; minimal ack
        return _response(
            node_id=node_id,
            to_peer=sender,
            in_reply_to=mid,
            status=200,
            intent="ack",
        )

    return _response(
        node_id=node_id,
        to_peer=sender,
        in_reply_to=mid,
        status=501,
        intent="unsupported_message_type",
    )
