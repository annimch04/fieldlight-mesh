"""TCP SIL receiver (one request → one response per connection)."""

from __future__ import annotations

import socketserver
from pathlib import Path
from typing import Any

import yaml

from . import sil
from .frame import read_frame, write_frame
from .handler import handle_inbound_sil


def load_trusted_peers(path: Path | None) -> set[str] | None:
    if path is None or not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if isinstance(data, list):
        return {str(x).strip() for x in data if x}
    if isinstance(data, dict) and "peers" in data:
        return {str(x).strip() for x in data["peers"] if x}
    return None


class SILRequestHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        cfg: dict[str, Any] = self.server.cfg  # type: ignore[attr-defined]
        try:
            raw = read_frame(self.rfile)
            text = raw.decode("utf-8")
            msg = sil.load_sil_yaml(text)
        except Exception as e:
            err = {
                "message_type": "response",
                "from": cfg["node_id"],
                "to": "mesh://unknown",
                "status": 400,
                "intent": "parse_error",
                "detail": str(e),
            }
            err["msg_id"] = sil.ensure_msg_id(err)
            write_frame(self.wfile, sil.sil_to_yaml_bytes(err))
            return

        out = handle_inbound_sil(
            msg,
            routes=cfg["routes"],
            node_id=cfg["node_id"],
            node_short=cfg["node_short"],
            trusted_peers=cfg.get("trusted_peers"),
            routing_log_path=cfg["routing_log_path"],
            audit_log_path=cfg.get("audit_log_path"),
            log_writes=cfg.get("log_writes", True),
        )
        write_frame(self.wfile, sil.sil_to_yaml_bytes(out))


class SILMeshServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

    def __init__(
        self,
        addr: tuple[str, int],
        cfg: dict[str, Any],
    ) -> None:
        self.cfg = cfg
        super().__init__(addr, SILRequestHandler)
