"""YAML peer registry: LAN mDNS, libp2p JSONL ingest, coalescing, SIL dial resolution."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable

import yaml

if TYPE_CHECKING:
    from fieldlight_mesh.lan_mdns import LANAdvertisement

REGISTRY_VERSION = 1


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "version": REGISTRY_VERSION,
            "updated_at": _now_iso(),
            "entries": [],
        }
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {"version": REGISTRY_VERSION, "updated_at": _now_iso(), "entries": []}
    entries = raw.get("entries")
    if not isinstance(entries, list):
        entries = []
    return {
        "version": int(raw.get("version") or REGISTRY_VERSION),
        "updated_at": str(raw.get("updated_at") or _now_iso()),
        "entries": [e for e in entries if isinstance(e, dict)],
    }


def dump_registry(data: dict[str, Any]) -> str:
    return yaml.safe_dump(
        data,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )


def _empty_p2p_record(pid: str) -> dict[str, Any]:
    return {
        "mesh_uri": None,
        "host": None,
        "port": None,
        "peer_id": pid,
        "libp2p_addrs": [],
        "source": "libp2p:mdns",
        "service_type": None,
        "service_name": None,
        "txt": {},
        "last_seen": _now_iso(),
    }


def ingest_libp2p_jsonl_lines(lines: Iterable[str]) -> list[dict[str, Any]]:
    """Build libp2p-only registry dicts from `libp2p_peer_probe` JSON lines (stdout)."""
    accum: dict[str, dict[str, Any]] = {}
    for raw_line in lines:
        line = raw_line.strip()
        if not line.startswith("{"):
            continue
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        ev = o.get("event")
        ts = str(o.get("ts") or _now_iso())
        if ev == "mdns_peer_found":
            pid = str(o.get("id") or "").strip()
            if not pid:
                continue
            addrs = [str(a) for a in (o.get("addrs") or []) if a]
            rec = accum.setdefault(pid, _empty_p2p_record(pid))
            cur = list(rec.get("libp2p_addrs") or [])
            rec["libp2p_addrs"] = sorted(set(cur) | set(addrs))
            rec["last_seen"] = ts
            rec["source"] = "libp2p:mdns"
        elif ev == "connected":
            pid = str(o.get("remote_peer") or "").strip()
            ra = o.get("remote_addr")
            if not pid:
                continue
            rec = accum.setdefault(pid, _empty_p2p_record(pid))
            if ra:
                ra = str(ra)
                cur = list(rec.get("libp2p_addrs") or [])
                if ra not in cur:
                    cur.append(ra)
                rec["libp2p_addrs"] = sorted(set(cur))
            rec["last_seen"] = ts
            rec["source"] = _merge_source(str(rec.get("source") or ""), "libp2p:connected")
        elif ev == "disconnected":
            pid = str(o.get("remote_peer") or "").strip()
            if pid and pid in accum:
                accum[pid]["last_seen"] = ts
                accum[pid]["source"] = _merge_source(
                    str(accum[pid].get("source") or ""), "libp2p:disconnected"
                )
    return list(accum.values())


def load_libp2p_jsonl(path: Path | None, *, stdin: bool = False) -> list[dict[str, Any]]:
    if stdin:
        return ingest_libp2p_jsonl_lines(sys.stdin)
    if path is None:
        return []
    return ingest_libp2p_jsonl_lines(path.read_text(encoding="utf-8").splitlines())


def _merge_source(old: str, new: str) -> str:
    if not old:
        return new
    parts = [p for p in old.split("+") if p]
    if new not in parts:
        parts.append(new)
    return "+".join(parts)


def _merge_two_entries(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    out = dict(a)
    for k, v in b.items():
        if v is None:
            continue
        if k == "libp2p_addrs":
            if not v:
                continue
            la = list(out.get("libp2p_addrs") or [])
            lb = list(v) if isinstance(v, list) else []
            out["libp2p_addrs"] = sorted(set(la) | set(lb))
        elif k == "txt" and isinstance(v, dict) and v:
            mt = dict(out.get("txt") or {})
            mt.update(v)
            out["txt"] = mt
        elif k == "port":
            try:
                iv = int(v)
            except (TypeError, ValueError):
                continue
            if iv <= 0:
                continue
            if not out.get("port"):
                out[k] = iv
        elif k in ("host", "mesh_uri", "service_name", "service_type"):
            if str(v).strip() and not str(out.get(k) or "").strip():
                out[k] = v
        elif k == "peer_id":
            if str(v).strip():
                out[k] = v
        elif k == "source":
            out[k] = _merge_source(str(out.get("source") or ""), str(v))
        elif k == "last_seen":
            out[k] = max(str(out.get("last_seen") or ""), str(v))
        elif k not in out or out[k] in (None, ""):
            out[k] = v
    return out


def _merge_entry_group(group: list[dict[str, Any]]) -> dict[str, Any]:
    acc: dict[str, Any] = {}
    for e in group:
        acc = _merge_two_entries(acc, e)
    return acc


def coalesce_registry_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge rows that share peer_id; dedupe SIL-only rows by mesh/host/port/service_name."""
    by_peer: dict[str, list[dict[str, Any]]] = defaultdict(list)
    no_peer: list[dict[str, Any]] = []
    for e in entries:
        pid = str(e.get("peer_id") or "").strip()
        if pid:
            by_peer[pid].append(e)
        else:
            no_peer.append(e)
    merged = [_merge_entry_group(g) for g in by_peer.values()]
    sil_map: dict[tuple[str, str, int, str], dict[str, Any]] = {}
    for e in no_peer:
        k = (
            str(e.get("mesh_uri") or ""),
            str(e.get("host") or ""),
            int(e.get("port") or 0),
            str(e.get("service_name") or ""),
        )
        if k in sil_map:
            sil_map[k] = _merge_two_entries(sil_map[k], e)
        else:
            sil_map[k] = dict(e)
    merged.extend(sil_map.values())
    return merged


def merge_registry(
    existing: dict[str, Any],
    new_lan_rows: list["LANAdvertisement"] | None = None,
    *,
    libp2p_entries: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = [
        dict(e) for e in (existing.get("entries") or []) if isinstance(e, dict)
    ]
    if new_lan_rows is not None:
        entries.extend(r.as_registry_entry() for r in new_lan_rows)
    if libp2p_entries:
        entries.extend(dict(e) for e in libp2p_entries)
    coalesced = coalesce_registry_entries(entries)
    return {
        "version": REGISTRY_VERSION,
        "updated_at": _now_iso(),
        "entries": sorted(coalesced, key=_registry_sort_key),
    }


def _registry_sort_key(e: dict[str, Any]) -> tuple:
    return (
        str(e.get("mesh_uri") or ""),
        str(e.get("peer_id") or ""),
        str(e.get("host") or ""),
        int(e.get("port") or 0),
    )


def resolve_sil_address(entries: list[Any], mesh_uri: str) -> tuple[str, int] | None:
    """Return (host, port) to dial for SIL given destination mesh_uri, or None."""
    if not mesh_uri:
        return None
    cands: list[dict[str, Any]] = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        if str(e.get("mesh_uri") or "") != mesh_uri:
            continue
        host = str(e.get("host") or "").strip()
        port = e.get("port")
        if not host or port in (None, "", 0):
            continue
        try:
            port_i = int(port)
        except (TypeError, ValueError):
            continue
        if port_i <= 0:
            continue
        cands.append(e)
    if not cands:
        return None

    def score(e: dict[str, Any]) -> tuple[int, int, str]:
        h = str(e.get("host") or "")
        non_loop = 1 if not (h.startswith("127.") or h == "::1") else 0
        src = str(e.get("source") or "").lower()
        # Prefer LAN _fieldlight / legacy HTTP rows over rows that only got SIL from coalescing with libp2p.
        lan_bonus = 1 if "_fieldlight" in src or "(legacy)" in src else 0
        return (non_loop, lan_bonus, str(e.get("last_seen") or ""))

    best = max(cands, key=score)
    return (str(best["host"]), int(best["port"]))
