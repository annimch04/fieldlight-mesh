"""SQLite-backed durable inbox with idempotent message receipt."""

from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
  msg_id TEXT PRIMARY KEY,
  sender TEXT NOT NULL,
  recipient TEXT NOT NULL,
  message_type TEXT NOT NULL,
  body TEXT NOT NULL,
  body_hash TEXT NOT NULL,
  received_at TEXT NOT NULL,
  read_at TEXT
)
"""


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(SCHEMA)
    return conn


def record_message(path: Path, msg: dict[str, Any]) -> str:
    body = yaml.safe_dump(msg, default_flow_style=False, sort_keys=True, allow_unicode=True)
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    msg_id = str(msg["msg_id"])
    with _connect(path) as conn:
        existing = conn.execute("SELECT body_hash FROM messages WHERE msg_id = ?", (msg_id,)).fetchone()
        if existing:
            if existing[0] != digest:
                raise ValueError("msg_id already exists with different content")
            return "duplicate"
        conn.execute(
            "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?, ?, NULL)",
            (
                msg_id,
                str(msg["from"]),
                str(msg["to"]),
                str(msg["message_type"]),
                body,
                digest,
                datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            ),
        )
    return "stored"


def list_messages(path: Path, limit: int = 50) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with _connect(path) as conn:
        rows = conn.execute(
            "SELECT msg_id, sender, recipient, message_type, body, received_at, read_at "
            "FROM messages ORDER BY received_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [
        {"msg_id": r[0], "from": r[1], "to": r[2], "message_type": r[3],
         "message": yaml.safe_load(r[4]), "received_at": r[5], "read_at": r[6]}
        for r in rows
    ]
