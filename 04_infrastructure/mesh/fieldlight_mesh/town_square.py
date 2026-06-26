"""Signed public Town Square objects and local append-only storage."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

from .identity import canonical_bytes, load_identity, now_utc, sign_bytes, verify_signature


SCHEMA = """
CREATE TABLE IF NOT EXISTS objects (
  object_id TEXT PRIMARY KEY,
  object_type TEXT NOT NULL,
  author TEXT NOT NULL,
  created_at TEXT NOT NULL,
  content TEXT NOT NULL,
  public_key TEXT NOT NULL,
  signature TEXT NOT NULL,
  body_yaml TEXT NOT NULL,
  received_at TEXT NOT NULL,
  verified INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS objects_created_at_idx ON objects(created_at);
CREATE INDEX IF NOT EXISTS objects_type_idx ON objects(object_type);
"""

SIGNED_FIELDS = ("version", "object_type", "author", "created_at", "content", "refs")


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


def unsigned_payload(obj: Mapping[str, Any]) -> dict[str, Any]:
    return {key: obj[key] for key in SIGNED_FIELDS if key in obj}


def object_hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def make_signed_object(
    home: Path,
    *,
    object_type: str,
    content: Mapping[str, Any],
    refs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    ident = load_identity(home)
    obj: dict[str, Any] = {
        "version": 1,
        "object_type": object_type,
        "author": ident["node_id"],
        "created_at": now_utc(),
        "content": dict(content),
        "refs": dict(refs or {}),
    }
    payload = unsigned_payload(obj)
    digest = object_hash(payload)
    obj["object_id"] = f"flobj-{digest[:32]}"
    obj["signature"] = {
        "alg": "Ed25519",
        "public_key": ident["public_key"],
        "sig": sign_bytes(home, canonical_bytes(payload)),
    }
    return obj


def verify_object(obj: Mapping[str, Any]) -> tuple[bool, str]:
    try:
        sig = obj["signature"]
        if not isinstance(sig, Mapping) or sig.get("alg") != "Ed25519":
            return False, "unsupported signature"
        payload = unsigned_payload(obj)
        expected_id = f"flobj-{object_hash(payload)[:32]}"
        if str(obj.get("object_id")) != expected_id:
            return False, "object_id does not match payload"
        if not verify_signature(str(sig["public_key"]), canonical_bytes(payload), str(sig["sig"])):
            return False, "signature verification failed"
    except Exception as exc:
        return False, str(exc)
    return True, "verified"


def store_object(path: Path, obj: Mapping[str, Any]) -> str:
    ok, reason = verify_object(obj)
    if not ok:
        raise ValueError(reason)
    body = yaml.safe_dump(dict(obj), default_flow_style=False, sort_keys=False, allow_unicode=True)
    content = yaml.safe_dump(obj.get("content", {}), default_flow_style=False, sort_keys=False, allow_unicode=True)
    sig = obj["signature"]
    with _connect(path) as conn:
        existing = conn.execute("SELECT body_yaml FROM objects WHERE object_id = ?", (obj["object_id"],)).fetchone()
        if existing:
            if existing[0] != body:
                raise ValueError("object_id already exists with different content")
            return "duplicate"
        conn.execute(
            "INSERT INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(obj["object_id"]),
                str(obj["object_type"]),
                str(obj["author"]),
                str(obj["created_at"]),
                content,
                str(sig["public_key"]),
                str(sig["sig"]),
                body,
                now_utc(),
                1,
            ),
        )
    return "stored"


def create_post(path: Path, home: Path, text: str, *, visibility: str = "public") -> dict[str, Any]:
    if not text.strip():
        raise ValueError("post text is required")
    obj = make_signed_object(
        home,
        object_type="town_square.post",
        content={"body": text.strip(), "visibility": visibility},
    )
    store_object(path, obj)
    return obj


def create_reply(path: Path, home: Path, text: str, *, parent: str) -> dict[str, Any]:
    if not parent.strip():
        raise ValueError("parent object_id is required")
    obj = make_signed_object(
        home,
        object_type="town_square.reply",
        content={"body": text.strip(), "visibility": "public"},
        refs={"reply_to": parent.strip()},
    )
    store_object(path, obj)
    return obj


def list_objects(path: Path, limit: int = 50) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with _connect(path) as conn:
        rows = conn.execute(
            "SELECT body_yaml FROM objects ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [yaml.safe_load(row[0]) for row in rows]


def export_bundle(path: Path, *, limit: int = 500) -> dict[str, Any]:
    return {
        "bundle_type": "fieldlight.town_square.bundle",
        "version": 1,
        "exported_at": now_utc(),
        "objects": list(reversed(list_objects(path, limit=limit))),
    }


def import_bundle(path: Path, bundle: Mapping[str, Any]) -> dict[str, int]:
    if bundle.get("bundle_type") != "fieldlight.town_square.bundle":
        raise ValueError("not a Fieldlight Town Square bundle")
    objects = bundle.get("objects", [])
    if not isinstance(objects, Iterable):
        raise ValueError("bundle objects must be iterable")
    stored = duplicates = 0
    for obj in objects:
        if not isinstance(obj, Mapping):
            raise ValueError("bundle object must be a mapping")
        result = store_object(path, obj)
        if result == "stored":
            stored += 1
        else:
            duplicates += 1
    return {"stored": stored, "duplicates": duplicates}


def verify_store(path: Path) -> dict[str, int]:
    ok = failed = 0
    for obj in list_objects(path, limit=100000):
        verified, _ = verify_object(obj)
        if verified:
            ok += 1
        else:
            failed += 1
    return {"verified": ok, "failed": failed}
