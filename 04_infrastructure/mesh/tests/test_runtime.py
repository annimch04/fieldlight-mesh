from __future__ import annotations

import io
import threading
from pathlib import Path

import pytest

from fieldlight_mesh.client import send_sil_message
from fieldlight_mesh.identity import initialize_identity
from fieldlight_mesh.frame import read_frame, write_frame
from fieldlight_mesh.inbox import list_messages, record_message
from fieldlight_mesh.routing import trust_allows_sender
from fieldlight_mesh.server import SILMeshServer, load_trusted_peers
from fieldlight_mesh.state import initialize, load_config, paths
from fieldlight_mesh.town_square import create_post, export_bundle, import_bundle, list_objects, verify_object, verify_store


class OneByteReader(io.BytesIO):
    def read(self, size=-1):
        return super().read(1 if size and size > 0 else size)


def test_frame_handles_partial_reads():
    stream = io.BytesIO()
    write_frame(stream, b"hello")
    assert read_frame(OneByteReader(stream.getvalue())) == b"hello"


def test_frame_rejects_empty_and_truncated():
    with pytest.raises(ValueError, match="empty"):
        read_frame(io.BytesIO(b"\x00\x00\x00\x00"))
    with pytest.raises(EOFError, match="payload"):
        read_frame(io.BytesIO(b"\x00\x00\x00\x05hi"))


def test_peer_trust_fails_closed():
    assert trust_allows_sender("any", "mesh://x", None)
    assert not trust_allows_sender("peer", "mesh://x", None)
    assert not trust_allows_sender("peer", "mesh://x", set())
    assert trust_allows_sender("peer", "mesh://x", {"mesh://x"})
    assert not trust_allows_sender("unknown", "mesh://x", {"mesh://x"})


def test_init_is_external_and_no_clobber(tmp_path: Path):
    home = tmp_path / "astra"
    initialize(home, node_id="mesh://fieldlight.anni.astra", node_name="astra", port=7750)
    assert load_config(home)["node_id"] == "mesh://fieldlight.anni.astra"
    assert paths(home)["config"].stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        initialize(home, node_id="mesh://other", node_name="other", port=7750)


def test_desktop_app_module_imports():
    from fieldlight_mesh.gui import MeshApp

    assert MeshApp.__name__ == "MeshApp"


def test_inbox_deduplicates_and_detects_conflict(tmp_path: Path):
    db = tmp_path / "inbox.sqlite3"
    msg = {"message_type": "message", "from": "mesh://a", "to": "mesh://b", "msg_id": "one", "body": "hi"}
    assert record_message(db, msg) == "stored"
    assert record_message(db, msg) == "duplicate"
    changed = dict(msg, body="changed")
    with pytest.raises(ValueError, match="different content"):
        record_message(db, changed)
    assert len(list_messages(db)) == 1


def test_two_node_message_is_stored_before_ack(tmp_path: Path):
    astra = tmp_path / "astra"
    initialize(astra, node_id="mesh://fieldlight.anni.astra", node_name="astra", port=7750)
    p = paths(astra)
    p["trusted"].write_text("peers:\n  - mesh://fieldlight.peer.test\n", encoding="utf-8")
    from fieldlight_mesh.routing import load_route_schema

    cfg = {
        "routes": load_route_schema(p["routes"]),
        "node_id": "mesh://fieldlight.anni.astra",
        "node_short": "ASTRA",
        "trusted_peers": load_trusted_peers(p["trusted"]),
        "routing_log_path": p["routing_log"],
        "audit_log_path": p["audit_log"],
        "inbox_path": p["inbox"],
        "town_square_path": p["town_square"],
        "log_writes": False,
        "socket_timeout": 2,
    }
    server = SILMeshServer(("127.0.0.1", 0), cfg)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        response = send_sil_message(
            host="127.0.0.1", port=server.server_address[1],
            msg={"message_type": "message", "from": "mesh://fieldlight.peer.test",
                 "to": "mesh://fieldlight.anni.astra", "body": "Hello Astra"},
            node_short="PEER", routing_log_path=None, audit_log_path=None, log_writes=False,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    assert response["status"] == 202
    assert response["intent"] == "message_received"
    assert list_messages(p["inbox"])[0]["message"]["body"] == "Hello Astra"


def test_town_square_post_is_signed_and_importable(tmp_path: Path):
    home = tmp_path / "node"
    initialize(home, node_id="mesh://fieldlight.node.alpha", node_name="alpha", port=7750)
    initialize_identity(home, node_id="mesh://fieldlight.node.alpha", label="alpha")
    p = paths(home)
    obj = create_post(p["town_square"], home, "hello public square")
    ok, reason = verify_object(obj)
    assert ok, reason
    assert obj["object_type"] == "town_square.post"
    bundle = export_bundle(p["town_square"])
    other = tmp_path / "other.sqlite3"
    assert import_bundle(other, bundle) == {"stored": 1, "duplicates": 0}
    assert import_bundle(other, bundle) == {"stored": 0, "duplicates": 1}
    assert verify_store(other) == {"verified": 1, "failed": 0}


def test_town_square_rejects_tampered_post(tmp_path: Path):
    home = tmp_path / "node"
    initialize(home, node_id="mesh://fieldlight.node.alpha", node_name="alpha", port=7750)
    initialize_identity(home, node_id="mesh://fieldlight.node.alpha", label="alpha")
    p = paths(home)
    obj = create_post(p["town_square"], home, "original")
    obj["content"]["body"] = "tampered"
    ok, reason = verify_object(obj)
    assert not ok
    assert "object_id" in reason or "signature" in reason


def test_two_node_town_square_bundle_sync(tmp_path: Path):
    sender = tmp_path / "sender"
    receiver = tmp_path / "receiver"
    initialize(sender, node_id="mesh://fieldlight.node.sender", node_name="sender", port=7750)
    initialize(receiver, node_id="mesh://fieldlight.node.receiver", node_name="receiver", port=7750)
    initialize_identity(sender, node_id="mesh://fieldlight.node.sender", label="sender")
    sender_paths = paths(sender)
    receiver_paths = paths(receiver)
    receiver_paths["trusted"].write_text("peers:\n  - mesh://fieldlight.node.sender\n", encoding="utf-8")
    create_post(sender_paths["town_square"], sender, "replicate me")

    from fieldlight_mesh.routing import load_route_schema

    cfg = {
        "routes": load_route_schema(receiver_paths["routes"]),
        "node_id": "mesh://fieldlight.node.receiver",
        "node_short": "RECEIVER",
        "trusted_peers": load_trusted_peers(receiver_paths["trusted"]),
        "routing_log_path": receiver_paths["routing_log"],
        "audit_log_path": receiver_paths["audit_log"],
        "inbox_path": receiver_paths["inbox"],
        "town_square_path": receiver_paths["town_square"],
        "log_writes": False,
        "socket_timeout": 2,
    }
    server = SILMeshServer(("127.0.0.1", 0), cfg)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        response = send_sil_message(
            host="127.0.0.1", port=server.server_address[1],
            msg={"message_type": "town_square_bundle", "from": "mesh://fieldlight.node.sender",
                 "to": "mesh://fieldlight.node.receiver", "bundle": export_bundle(sender_paths["town_square"])},
            node_short="SENDER", routing_log_path=None, audit_log_path=None, log_writes=False,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    assert response["status"] == 202
    assert response["intent"] == "town_square_bundle_received"
    assert response["stored"] == 1
    assert list_objects(receiver_paths["town_square"])[0]["content"]["body"] == "replicate me"
