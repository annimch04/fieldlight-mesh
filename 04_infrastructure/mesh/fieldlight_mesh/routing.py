"""Load lemur_route_schema.yml and apply routing / auth rules (v1 subset)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml

AUTH_GPG_SIG = "gpg_sig"
AUTH_NONE = "none"
AUTH_OPTIONAL = "optional"


def load_route_schema(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict) or "routes" not in data:
        raise ValueError("route schema must contain top-level 'routes'")
    return data["routes"]


def route_for_message_type(routes: Mapping[str, Any], message_type: str) -> dict[str, Any]:
    if message_type not in routes:
        raise ValueError(f"unknown message_type for routing: {message_type}")
    r = routes[message_type]
    if not isinstance(r, dict):
        raise ValueError(f"invalid route entry for {message_type}")
    return r


def destination_matches_node(to_value: str, node_id: str) -> bool:
    """Return True if `to` is addressed to this node (prefix / exact match)."""
    to_s = str(to_value).strip()
    nid = str(node_id).strip()
    if to_s == nid:
        return True
    # Allow subpaths like mesh://x/trace when base matches
    if to_s.startswith(nid) and (len(to_s) == len(nid) or to_s[len(nid)] in "/:"):
        return True
    return False


def trust_allows_sender(
    trust_required: str,
    sender: str,
    trusted_peers: set[str] | None,
) -> bool:
    t = (trust_required or "").strip().lower()
    if t in ("any", ""):
        return True
    if t in ("peer", "proxy", "ghost"):
        if not trusted_peers:
            return False
        return sender in trusted_peers
    return False


def auth_ok(route: Mapping[str, Any], msg: Mapping[str, Any]) -> tuple[bool, str]:
    """Return (ok, reason). Does not verify GPG cryptographically (v1 stub)."""
    auth = str(route.get("auth", AUTH_OPTIONAL)).lower()
    if auth == AUTH_NONE:
        return True, "auth none"
    if auth == AUTH_OPTIONAL:
        return True, "auth optional"
    if auth == AUTH_GPG_SIG:
        return False, "gpg_sig verification is not implemented; route denied"
    return False, f"unknown auth mode denied: {auth}"


def ttl_exceeded(route: Mapping[str, Any], msg: Mapping[str, Any]) -> bool:
    max_hops = int(route.get("ttl", 99))
    hops = int(msg.get("hop", 0) or 0)
    return hops > max_hops
