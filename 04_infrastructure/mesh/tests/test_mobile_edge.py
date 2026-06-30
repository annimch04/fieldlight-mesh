from __future__ import annotations

import json
import threading
from pathlib import Path
from urllib import request

import pytest

from fieldlight_mesh.mobile_edge import (
    MobileEdgeHTTPServer,
    create_bookmark_event,
    event_to_sil_message,
    generate_sync_manifest,
    ingest_media_reference,
    list_events,
    mobile_edge_paths,
)


def test_create_bookmark_event_and_list(tmp_path: Path):
    p = mobile_edge_paths(tmp_path)
    event = create_bookmark_event(
        db_path=p.db,
        labels=["field_note", "institute_idea"],
        note="first Supra bookmark",
        location={"precision": "withheld"},
        vehicle={"speed_mph": 12, "ignition_state": "on"},
        created_at="2026-06-30T12:00:00Z",
    )
    assert event["event_type"] == "mobile_edge.bookmark"
    assert event["labels"] == ["field_note", "institute_idea"]
    rows = list_events(p.db)
    assert rows[0]["note"] == "first Supra bookmark"
    assert rows[0]["vehicle"]["speed_mph"] == 12


def test_bookmark_exports_mesh_message(tmp_path: Path):
    p = mobile_edge_paths(tmp_path)
    event = create_bookmark_event(db_path=p.db, note="export me")
    msg = event_to_sil_message(event)
    assert msg["message_type"] == "message"
    assert msg["from"] == "mesh://fieldlight.anni.supra"
    assert msg["to"] == "mesh://fieldlight.anni.lemur"
    assert msg["event_type"] == "mobile_edge.bookmark"
    assert msg["event"]["note"] == "export me"


def test_media_ingest_creates_protected_reference(tmp_path: Path):
    media = tmp_path / "clip.mp4"
    media.write_bytes(b"fake-viofo-clip")
    p = mobile_edge_paths(tmp_path / "node")
    event = ingest_media_reference(db_path=p.db, media_path=media, note="dashcam clip")
    assert event["event_type"] == "mobile_edge.media_reference"
    assert event["media_refs"][0]["sha256"]
    assert event["custody"] == "export_requires_review"


def test_manifest_refuses_protected_without_review(tmp_path: Path):
    media = tmp_path / "clip.mp4"
    media.write_bytes(b"protected")
    p = mobile_edge_paths(tmp_path / "node")
    ingest_media_reference(db_path=p.db, media_path=media)
    with pytest.raises(ValueError, match="review required"):
        generate_sync_manifest(db_path=p.db, review=False)
    manifest = generate_sync_manifest(db_path=p.db, review=True)
    assert manifest["events"][0]["review_required"] is True


def test_local_api_bookmark_health_and_manifest(tmp_path: Path):
    p = mobile_edge_paths(tmp_path)
    server = MobileEdgeHTTPServer(("127.0.0.1", 0), root=p.root, node_id="mesh://fieldlight.anni.supra", quiet=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        req = request.Request(
            base + "/bookmark",
            data=json.dumps({"labels": ["field_note"], "note": "from iPad"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=3) as resp:
            body = json.loads(resp.read().decode())
        assert body["note"] == "from iPad"
        with request.urlopen(base + "/health", timeout=3) as resp:
            health = json.loads(resp.read().decode())
        assert health["event_count"] == 1
        with request.urlopen(base + "/events/recent?limit=1", timeout=3) as resp:
            events = json.loads(resp.read().decode())
        assert events[0]["note"] == "from iPad"
        req = request.Request(base + "/sync/manifest", data=b"{}", headers={"Content-Type": "application/json"}, method="POST")
        with request.urlopen(req, timeout=3) as resp:
            manifest = json.loads(resp.read().decode())
        assert manifest["event_count"] == 1
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
