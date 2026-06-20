"""LAN mDNS helpers for Fieldlight presence (browse metadata + register)."""

from __future__ import annotations

import dataclasses
import ipaddress
import socket
import threading
import time
from datetime import datetime, timezone
from typing import Any

try:
    from zeroconf import ServiceBrowser, ServiceInfo, ServiceListener, Zeroconf
except ImportError as e:  # pragma: no cover
    raise ImportError("lan_mdns requires zeroconf (pip install -r requirements.txt)") from e


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def resolve_mdns_service(
    zc: Zeroconf, type_: str, name: str, timeout_ms: int = 2000
) -> ServiceInfo | None:
    info = zc.get_service_info(type_, name, timeout=timeout_ms)
    if info is None:
        info = zc.get_service_info(type_, name, timeout=timeout_ms)
    return info


def decode_txt(info: ServiceInfo | None) -> dict[str, str]:
    if not info or not info.properties:
        return {}
    out: dict[str, str] = {}
    for k, v in info.properties.items():
        if v is None:
            continue
        key = k.decode("utf-8", errors="replace") if isinstance(k, bytes) else str(k)
        if not key.strip():
            continue
        val = v.decode("utf-8", errors="replace") if isinstance(v, bytes) else str(v)
        out[key] = val
    return out


def is_legacy_fieldlight_http_name(name: str) -> bool:
    """True if an _http._tcp instance name should be treated as legacy Fieldlight."""
    return "fieldlight" in name.lower()


@dataclasses.dataclass
class LANAdvertisement:
    """One resolved mDNS row (bridge-friendly)."""

    mesh_uri: str | None
    host: str
    port: int
    peer_id: str | None
    source: str
    service_type: str
    service_name: str
    txt: dict[str, str]
    last_seen: str

    def as_registry_entry(self) -> dict[str, Any]:
        return {
            "mesh_uri": self.mesh_uri,
            "host": self.host,
            "port": self.port,
            "peer_id": self.peer_id,
            "source": self.source,
            "service_type": self.service_type,
            "service_name": self.service_name,
            "txt": dict(self.txt) if self.txt else {},
            "last_seen": self.last_seen,
        }


def _row_from_info(
    *,
    info: ServiceInfo | None,
    type_: str,
    name: str,
    source: str,
) -> LANAdvertisement | None:
    if not info:
        return None
    txt = decode_txt(info)
    mesh_uri = txt.get("mesh_uri") or None
    peer_id = txt.get("peer") or None
    port = int(info.port)
    addrs = []
    try:
        addrs = list(info.parsed_addresses())
    except Exception:
        addrs = []
    if not addrs:
        return None
    # Prefer non-loopback for SIL dial; still record loopback if alone.
    preferred = [a for a in addrs if not _is_loopback(a)]
    host = (preferred[0] if preferred else addrs[0]).strip()
    return LANAdvertisement(
        mesh_uri=mesh_uri,
        host=host,
        port=port,
        peer_id=peer_id,
        source=source,
        service_type=type_,
        service_name=name,
        txt=txt,
        last_seen=_utc_now_iso(),
    )


def _is_loopback(addr: str) -> bool:
    try:
        return ipaddress.ip_address(addr).is_loopback
    except ValueError:
        return addr.startswith("127.")


class _CollectListener(ServiceListener):
    def __init__(self, *, legacy_http: bool) -> None:
        self.legacy_http = legacy_http
        self._lock = threading.Lock()
        self.rows: list[LANAdvertisement] = []

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        if type_.startswith("_http._tcp") and not (
            self.legacy_http and is_legacy_fieldlight_http_name(name)
        ):
            return
        info = resolve_mdns_service(zc, type_, name)
        source = "mdns:_fieldlight._tcp.local."
        if type_.startswith("_http._tcp"):
            source = "mdns:_http._tcp.local.(legacy)"
        row = _row_from_info(info=info, type_=type_, name=name, source=source)
        if row:
            with self._lock:
                self.rows.append(row)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        return

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        return


def collect_lan_advertisements(*, duration: float, legacy_http: bool = False) -> list[LANAdvertisement]:
    """Browse for `duration` seconds and return resolved advertisements (may omit slow peers)."""
    listener = _CollectListener(legacy_http=legacy_http)
    zc = Zeroconf()
    browsers: list[ServiceBrowser] = []
    try:
        browsers.append(ServiceBrowser(zc, "_fieldlight._tcp.local.", listener))
        if legacy_http:
            browsers.append(ServiceBrowser(zc, "_http._tcp.local.", listener))
        time.sleep(max(0.0, duration))
    finally:
        zc.close()
    with listener._lock:
        merged = _dedupe_rows(listener.rows)
        return merged


def _dedupe_rows(rows: list[LANAdvertisement]) -> list[LANAdvertisement]:
    seen: set[tuple[str | None, str, int, str, str]] = set()
    out: list[LANAdvertisement] = []
    for r in rows:
        key = (r.mesh_uri, r.host, r.port, r.service_type, r.service_name)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def _non_loopback_ips() -> list[str]:
    hostname = socket.gethostname()
    ips: list[str] = []
    try:
        for fam, _, _, _, sockaddr in socket.getaddrinfo(hostname, None):
            if fam != socket.AF_INET and fam != socket.AF_INET6:
                continue
            ip = sockaddr[0]
            if ip and not _is_loopback(ip):
                ips.append(ip)
    except OSError:
        pass
    # SIL v1 listens on IPv4 by default; prefer a reachable IPv4 advertisement.
    ips.sort(key=lambda ip: 0 if ":" not in ip else 1)
    # de-dupe preserving order
    out: list[str] = []
    for ip in ips:
        if ip not in out:
            out.append(ip)
    return out


def build_fieldlight_service(
    *,
    instance: str,
    port: int,
    mesh_uri: str,
    peer_id: str | None = None,
    txt_version: str = "1",
) -> ServiceInfo:
    """Build ServiceInfo for _fieldlight._tcp (caller registers with Zeroconf)."""
    props: dict[str, str] = {
        "mesh_uri": mesh_uri,
        "sil_port": str(port),
        "v": txt_version,
    }
    if peer_id:
        props["peer"] = peer_id
    name = f"{instance}._fieldlight._tcp.local."
    type_ = "_fieldlight._tcp.local."
    parsed = _non_loopback_ips()
    if not parsed:
        parsed = ["127.0.0.1"]
    return ServiceInfo(
        type_,
        name,
        port=port,
        properties=props,
        parsed_addresses=parsed,
    )
