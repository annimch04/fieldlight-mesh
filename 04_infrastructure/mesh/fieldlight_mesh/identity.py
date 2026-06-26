"""Ed25519 identity records for signed Fieldlight mesh objects."""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import yaml
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .state import paths, write_yaml


def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64d(data: str) -> bytes:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def public_key_text(public_key: Ed25519PublicKey) -> str:
    raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return _b64e(raw)


def load_private_key(path: Path) -> Ed25519PrivateKey:
    raw = path.read_bytes()
    key = serialization.load_pem_private_key(raw, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError("identity key is not Ed25519")
    return key


def load_public_key(public_key: str) -> Ed25519PublicKey:
    return Ed25519PublicKey.from_public_bytes(_b64d(public_key))


def identity_exists(home: Path) -> bool:
    p = paths(home)
    return p["identity_private_key"].exists() and p["identity_public"].exists()


def initialize_identity(home: Path, *, node_id: str, label: str, force: bool = False) -> dict[str, Any]:
    p = paths(home)
    p["identity_dir"].mkdir(parents=True, exist_ok=True)
    if p["identity_private_key"].exists() and not force:
        raise FileExistsError(f"identity already exists: {p['identity_private_key']}")
    key = Ed25519PrivateKey.generate()
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    p["identity_private_key"].write_bytes(private_pem)
    try:
        p["identity_private_key"].chmod(0o600)
    except OSError:
        pass
    record = {
        "version": 1,
        "identity_type": "fieldlight.ed25519",
        "node_id": node_id,
        "label": label,
        "public_key": public_key_text(key.public_key()),
        "created_at": now_utc(),
    }
    write_yaml(p["identity_public"], record)
    return record


def load_identity(home: Path) -> dict[str, Any]:
    p = paths(home)
    if not p["identity_public"].exists():
        raise FileNotFoundError("identity not initialized; run: fieldlight-mesh identity init")
    data = yaml.safe_load(p["identity_public"].read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("identity_type") != "fieldlight.ed25519":
        raise ValueError("invalid Fieldlight identity record")
    return data


def sign_bytes(home: Path, payload: bytes) -> str:
    key = load_private_key(paths(home)["identity_private_key"])
    return _b64e(key.sign(payload))


def verify_signature(public_key: str, payload: bytes, signature: str) -> bool:
    key = load_public_key(public_key)
    try:
        key.verify(_b64d(signature), payload)
    except InvalidSignature:
        return False
    return True
