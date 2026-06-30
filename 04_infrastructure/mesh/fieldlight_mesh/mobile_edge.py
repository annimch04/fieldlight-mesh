"""Mobile Edge Node Phase 1 runtime primitives.

This module keeps the Supra node local-first: events are stored locally in
SQLite, and mesh-compatible SIL payloads are exported from that local record.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import yaml

DEFAULT_NODE_ID = "mesh://fieldlight.anni.supra"
DEFAULT_SYNC_TARGET = "mesh://fieldlight.anni.lemur"
EVENT_TYPES = {
    "mobile_edge.bookmark",
    "mobile_edge.health",
    "mobile_edge.sync_manifest",
    "mobile_edge.media_reference",
}
PROTECTED_LABELS = {"important_conversation"}


@dataclass(frozen=True)
class MobileEdgePaths:
    root: Path
    db: Path
    media_dir: Path


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def default_mobile_edge_root(home: Path) -> Path:
    return home / "mobile_edge"


def mobile_edge_paths(root: Path) -> MobileEdgePaths:
    root = root.expanduser()
    return MobileEdgePaths(root=root, db=root / "mobile_edge.sqlite3", media_dir=root / "media")


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_store(db_path: Path) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                node_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                custody TEXT NOT NULL,
                consent_scope TEXT NOT NULL,
                labels_json TEXT NOT NULL,
                note TEXT,
                location_json TEXT NOT NULL,
                vehicle_json TEXT NOT NULL,
                media_refs_json TEXT NOT NULL,
                sync_json TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")


def _event_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    payload = json.loads(row["payload_json"])
    payload["labels"] = json.loads(row["labels_json"])
    payload["location"] = json.loads(row["location_json"])
    payload["vehicle"] = json.loads(row["vehicle_json"])
    payload["media_refs"] = json.loads(row["media_refs_json"])
    payload["sync"] = json.loads(row["sync_json"])
    return payload


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def normalize_labels(value: Any, *, default: str = "field_note") -> list[str]:
    if value is None:
        return [default]
    if isinstance(value, str):
        labels = [part.strip() for part in value.split(",") if part.strip()]
        return labels or [default]
    if isinstance(value, (list, tuple, set)):
        labels = [str(part).strip() for part in value if str(part).strip()]
        return labels or [default]
    return [str(value).strip() or default]


def validate_event(event: dict[str, Any]) -> None:
    missing = [k for k in ("event_id", "event_type", "node_id", "created_at", "custody") if not event.get(k)]
    if missing:
        raise ValueError(f"missing mobile edge event fields: {missing}")
    if event["event_type"] not in EVENT_TYPES:
        raise ValueError(f"unsupported mobile edge event_type: {event['event_type']}")
    if not str(event["node_id"]).startswith("mesh://"):
        raise ValueError("node_id must be a mesh:// URI")
    event.setdefault("consent_scope", "authorship-aware")
    event.setdefault("labels", [])
    event.setdefault("location", {"precision": "withheld"})
    event.setdefault("vehicle", {"ignition_state": "unknown"})
    event.setdefault("media_refs", [])
    event.setdefault("sync", {"sync_status": "local"})


def store_event(db_path: Path, event: dict[str, Any]) -> dict[str, Any]:
    validate_event(event)
    initialize_store(db_path)
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO events (
                event_id, event_type, node_id, created_at, custody, consent_scope,
                labels_json, note, location_json, vehicle_json, media_refs_json, sync_json, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["event_id"],
                event["event_type"],
                event["node_id"],
                event["created_at"],
                event["custody"],
                event.get("consent_scope", "authorship-aware"),
                _json(event.get("labels", [])),
                event.get("note"),
                _json(event.get("location", {"precision": "withheld"})),
                _json(event.get("vehicle", {"ignition_state": "unknown"})),
                _json(event.get("media_refs", [])),
                _json(event.get("sync", {"sync_status": "local"})),
                _json(event),
            ),
        )
    return event


def list_events(db_path: Path, *, limit: int = 50) -> list[dict[str, Any]]:
    initialize_store(db_path)
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM events ORDER BY created_at DESC LIMIT ?", (int(limit),)
        ).fetchall()
    return [_event_row_to_dict(row) for row in rows]


def get_event(db_path: Path, event_id: str) -> dict[str, Any] | None:
    initialize_store(db_path)
    with _connect(db_path) as conn:
        row = conn.execute("SELECT * FROM events WHERE event_id = ?", (event_id,)).fetchone()
    return _event_row_to_dict(row) if row else None


def create_bookmark_event(
    *,
    db_path: Path,
    node_id: str = DEFAULT_NODE_ID,
    operator: str = "Anni McHenry",
    labels: list[str] | None = None,
    note: str = "",
    location: dict[str, Any] | None = None,
    vehicle: dict[str, Any] | None = None,
    media_refs: list[dict[str, Any]] | None = None,
    sync_target: str = DEFAULT_SYNC_TARGET,
    created_at: str | None = None,
) -> dict[str, Any]:
    event = {
        "event_id": f"supra-{uuid.uuid4().hex[:12]}",
        "event_type": "mobile_edge.bookmark",
        "node_id": node_id,
        "created_at": created_at or utc_now(),
        "operator": operator,
        "custody": "sync_queued",
        "consent_scope": "authorship-aware",
        "labels": labels or ["field_note"],
        "note": note,
        "location": location or {"precision": "withheld"},
        "vehicle": vehicle or {"ignition_state": "unknown"},
        "media_refs": media_refs or [],
        "sync": {"queued_for": sync_target, "sync_status": "queued", "queued_at": utc_now()},
    }
    return store_event(db_path, event)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ingest_media_reference(
    *,
    db_path: Path,
    media_path: Path,
    node_id: str = DEFAULT_NODE_ID,
    operator: str = "Anni McHenry",
    labels: list[str] | None = None,
    note: str = "",
    location: dict[str, Any] | None = None,
    vehicle: dict[str, Any] | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    media_path = media_path.expanduser()
    if not media_path.exists() or not media_path.is_file():
        raise FileNotFoundError(f"media file not found: {media_path}")
    digest = sha256_file(media_path)
    media_type = mimetypes.guess_type(media_path.name)[0] or "application/octet-stream"
    ref = {
        "ref_id": f"media-{digest[:16]}",
        "media_type": media_type,
        "local_path": str(media_path),
        "sha256": digest,
        "source": "viofo_file_ingest",
    }
    event = {
        "event_id": f"supra-media-{uuid.uuid4().hex[:12]}",
        "event_type": "mobile_edge.media_reference",
        "node_id": node_id,
        "created_at": created_at or utc_now(),
        "operator": operator,
        "custody": "export_requires_review",
        "consent_scope": "review-required",
        "labels": labels or ["media_reference"],
        "note": note,
        "location": location or {"precision": "withheld"},
        "vehicle": vehicle or {"ignition_state": "unknown"},
        "media_refs": [ref],
        "sync": {"sync_status": "local", "review_required": True},
    }
    return store_event(db_path, event)


def event_is_protected(event: dict[str, Any]) -> bool:
    if event.get("media_refs"):
        return True
    if event.get("location", {}).get("precision") == "exact":
        return True
    if PROTECTED_LABELS.intersection(set(event.get("labels", []))):
        return True
    if event.get("consent_scope") == "review-required":
        return True
    return False


def generate_sync_manifest(
    *,
    db_path: Path,
    node_id: str = DEFAULT_NODE_ID,
    target: str = DEFAULT_SYNC_TARGET,
    review: bool = False,
    limit: int = 100,
) -> dict[str, Any]:
    events = list_events(db_path, limit=limit)
    protected = [e for e in events if event_is_protected(e)]
    if protected and not review:
        ids = ", ".join(e["event_id"] for e in protected[:5])
        raise ValueError(f"review required before syncing protected event(s): {ids}")
    return {
        "node_id": node_id,
        "created_at": utc_now(),
        "custody": "sync_queued",
        "consent_scope": "review-required" if protected else "authorship-aware",
        "target": target,
        "event_count": len(events),
        "events": [
            {
                "event_id": e["event_id"],
                "event_type": e["event_type"],
                "created_at": e["created_at"],
                "labels": e.get("labels", []),
                "media_included": False,
                "review_required": event_is_protected(e),
            }
            for e in events
        ],
    }


def event_to_sil_message(event: dict[str, Any], *, from_node: str | None = None, to: str = DEFAULT_SYNC_TARGET) -> dict[str, Any]:
    validate_event(event)
    return {
        "message_type": "message",
        "from": from_node or str(event["node_id"]),
        "to": to,
        "intent": event["event_type"].replace(".", "_"),
        "event_type": event["event_type"],
        "event": event,
    }


def manifest_to_sil_message(manifest: dict[str, Any], *, from_node: str = DEFAULT_NODE_ID, to: str = DEFAULT_SYNC_TARGET) -> dict[str, Any]:
    return {
        "message_type": "message",
        "from": from_node,
        "to": to,
        "intent": "mobile_edge_sync_manifest",
        "event_type": "mobile_edge.sync_manifest",
        "manifest": manifest,
    }


def health_payload(*, db_path: Path, node_id: str = DEFAULT_NODE_ID, storage_root: Path | None = None) -> dict[str, Any]:
    events = list_events(db_path, limit=1000)
    pending = [e for e in events if e.get("sync", {}).get("sync_status") in {"queued", "local"}]
    return {
        "node_id": node_id,
        "created_at": utc_now(),
        "status": "ok",
        "storage_root": str(storage_root) if storage_root else None,
        "event_count": len(events),
        "pending_events": len(pending),
        "obd": {"status": "adapter_pending"},
        "dashcam": {"status": "file_ingest_later"},
        "sync": {"status": "ready" if events else "idle"},
    }


COCKPIT_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Fieldlight Supra Node</title>
  <style>
    :root { --ink:#10212b; --deep:#073b45; --line:#d7dedc; --paper:#fbf7ef; --accent:#d94a38; }
    body { margin:0; font-family: ui-sans-serif, system-ui, -apple-system, sans-serif; color:var(--ink); background:linear-gradient(140deg,#f8f3ea,#eaf3f0); }
    main { max-width: 980px; margin: 0 auto; padding: 32px 18px 56px; }
    header { background: radial-gradient(circle at 80% 10%, rgba(217,74,56,.32), transparent 30%), linear-gradient(120deg,#06343d,#10212b); color:#fffaf0; padding: 34px; border-radius: 28px; box-shadow: 0 24px 70px rgba(16,33,43,.22); }
    h1 { font-size: clamp(2.2rem, 8vw, 5rem); line-height:.9; margin: 0 0 18px; letter-spacing:-.06em; }
    .grid { display:grid; grid-template-columns: repeat(auto-fit,minmax(220px,1fr)); gap:14px; margin:20px 0; }
    .card, form { background:rgba(255,255,255,.78); border:1px solid var(--line); border-radius:18px; padding:18px; box-shadow:0 16px 45px rgba(16,33,43,.08); }
    .label { text-transform:uppercase; letter-spacing:.14em; font-size:.72rem; font-weight:800; color:#40786b; }
    .value { font-size:1.8rem; font-weight:850; margin-top:6px; color:var(--deep); }
    input, textarea { width:100%; box-sizing:border-box; border:1px solid var(--line); border-radius:12px; padding:12px; font:inherit; margin:8px 0 12px; background:#fffdf8; }
    button { border:0; border-radius:999px; padding:12px 18px; font-weight:850; background:var(--accent); color:white; cursor:pointer; }
    li { margin:10px 0; padding:12px; background:#fffdf8; border:1px solid var(--line); border-radius:14px; }
    code { background:#eef3f1; padding:.15em .35em; border-radius:.35em; }
  </style>
</head>
<body>
<main>
  <header>
    <div class="label">Fieldlight Mobile Edge Node</div>
    <h1>Supra Node</h1>
    <p>Local-first drive memory. Human-authored bookmarks. No cloud ownership of continuity.</p>
  </header>
  <section class="grid" id="health"><div class="card">Loading node health...</div></section>
  <form id="bookmark-form">
    <div class="label">Create Bookmark</div>
    <input name="labels" placeholder="labels, comma separated" value="field_note">
    <textarea name="note" placeholder="What should this moment remember?"></textarea>
    <button type="submit">Bookmark This Moment</button>
  </form>
  <section>
    <h2>Recent Events</h2>
    <ul id="events"></ul>
  </section>
</main>
<script>
async function json(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}
function healthCard(label, value) { return `<div class="card"><div class="label">${label}</div><div class="value">${value}</div></div>`; }
async function refresh() {
  const h = await json('/health');
  document.querySelector('#health').innerHTML = [
    healthCard('Status', h.status), healthCard('Events', h.event_count),
    healthCard('Pending', h.pending_events), healthCard('OBD', h.obd.status),
    healthCard('Dashcam', h.dashcam.status), healthCard('Sync', h.sync.status)
  ].join('');
  const events = await json('/events/recent?limit=10');
  document.querySelector('#events').innerHTML = events.map(e => `<li><strong>${e.event_type}</strong> <code>${e.created_at}</code><br>${(e.labels||[]).join(', ')}<br>${e.note||''}</li>`).join('') || '<li>No events yet.</li>';
}
document.querySelector('#bookmark-form').addEventListener('submit', async (ev) => {
  ev.preventDefault();
  const fd = new FormData(ev.target);
  await json('/bookmark', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ labels: fd.get('labels').split(',').map(x => x.trim()).filter(Boolean), note: fd.get('note') }) });
  ev.target.note.value = '';
  await refresh();
});
refresh().catch(err => { document.body.insertAdjacentHTML('beforeend', `<pre>${err}</pre>`); });
</script>
</body>
</html>
"""


class MobileEdgeHandler(BaseHTTPRequestHandler):
    server: "MobileEdgeHTTPServer"

    def _send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        data = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("request body must be a JSON object")
        return data

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/":
                body = COCKPIT_HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if parsed.path == "/health":
                self._send_json(health_payload(db_path=self.server.db_path, node_id=self.server.node_id, storage_root=self.server.root))
                return
            if parsed.path == "/events/recent":
                limit = int(parse_qs(parsed.query).get("limit", ["50"])[0])
                self._send_json(list_events(self.server.db_path, limit=limit))
                return
            self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            data = self._read_json()
            if parsed.path == "/bookmark":
                event = create_bookmark_event(
                    db_path=self.server.db_path,
                    node_id=self.server.node_id,
                    labels=normalize_labels(data.get("labels")),
                    note=str(data.get("note", "")),
                    location=dict(data.get("location") or {"precision": "withheld"}),
                    vehicle=dict(data.get("vehicle") or {"ignition_state": "unknown"}),
                    media_refs=list(data.get("media_refs") or []),
                )
                self._send_json(event, HTTPStatus.CREATED)
                return
            if parsed.path == "/media/ingest":
                event = ingest_media_reference(
                    db_path=self.server.db_path,
                    node_id=self.server.node_id,
                    media_path=Path(str(data.get("path", ""))),
                    labels=normalize_labels(data.get("labels"), default="media_reference"),
                    note=str(data.get("note", "")),
                )
                self._send_json(event, HTTPStatus.CREATED)
                return
            if parsed.path == "/sync/manifest":
                review = bool(data.get("review", False))
                manifest = generate_sync_manifest(db_path=self.server.db_path, node_id=self.server.node_id, review=review)
                self._send_json(manifest)
                return
            self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def log_message(self, fmt: str, *args: Any) -> None:
        if self.server.quiet:
            return
        super().log_message(fmt, *args)


class MobileEdgeHTTPServer(ThreadingHTTPServer):
    def __init__(self, addr: tuple[str, int], *, root: Path, node_id: str, quiet: bool = False) -> None:
        self.root = root
        self.node_id = node_id
        self.quiet = quiet
        p = mobile_edge_paths(root)
        self.db_path = p.db
        initialize_store(self.db_path)
        super().__init__(addr, MobileEdgeHandler)
