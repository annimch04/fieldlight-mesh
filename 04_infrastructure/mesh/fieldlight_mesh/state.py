"""Per-user configuration and durable state for an installed mesh node."""

from __future__ import annotations

import os
import platform
import re
import socket
from importlib import resources
from pathlib import Path
from typing import Any

import yaml


def default_home() -> Path:
    override = os.environ.get("FIELDLIGHT_HOME")
    if override:
        return Path(override).expanduser()
    if platform.system() == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Fieldlight Mesh"
    return Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "fieldlight-mesh"


def default_node_id() -> str:
    name = re.sub(r"[^a-z0-9]+", "-", socket.gethostname().lower()).strip("-") or "node"
    return f"mesh://fieldlight.local.{name}"


def paths(home: Path) -> dict[str, Path]:
    return {
        "home": home,
        "config": home / "config.yml",
        "routes": home / "routes.yml",
        "trusted": home / "trusted_peers.yml",
        "registry": home / "peers.yml",
        "inbox": home / "inbox.sqlite3",
        "routing_log": home / "logs" / "routing.yml",
        "audit_log": home / "logs" / "audit.yml",
    }


def load_yaml(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return fallback if data is None else data


def write_yaml(path: Path, data: Any, *, exclusive: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "x" if exclusive else "w"
    with path.open(mode, encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    try:
        path.chmod(0o600)
    except OSError:
        pass


def initialize(home: Path, *, node_id: str, node_name: str, port: int, force: bool = False) -> None:
    p = paths(home)
    home.mkdir(parents=True, exist_ok=True)
    try:
        home.chmod(0o700)
    except OSError:
        pass
    if p["config"].exists() and not force:
        raise FileExistsError(f"node already initialized: {p['config']}")
    write_yaml(
        p["config"],
        {"version": 1, "node_id": node_id, "node_name": node_name, "host": "0.0.0.0", "port": port},
    )
    default_routes = resources.files("fieldlight_mesh").joinpath("default_routes.yml").read_text(encoding="utf-8")
    p["routes"].write_text(default_routes, encoding="utf-8")
    p["routes"].chmod(0o600)
    write_yaml(p["trusted"], {"peers": []})
    write_yaml(p["registry"], {"version": 1, "entries": []})


def load_config(home: Path) -> dict[str, Any]:
    config = load_yaml(paths(home)["config"], {})
    if not isinstance(config, dict) or not config.get("node_id"):
        raise FileNotFoundError(f"not initialized; run: fieldlight-mesh init --home {home}")
    return config
