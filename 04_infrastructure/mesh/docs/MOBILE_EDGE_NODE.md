# Mobile Edge Node Technical Profile

Status: Phase 1 build implementation
Primary implementation target: Supra Edge Node
Node class: `vehicle_edge`
Runtime relationship: Fieldlight Mesh peer over trusted local network or Tailscale

## Purpose

The Mobile Edge Node turns a vehicle into a local-first Fieldlight Mesh node.

It captures field context while preserving local custody. It does not turn the vehicle into an authority. It turns the vehicle into a trusted witness whose records remain owned by the human operator.

## Mesh Identity

Recommended first node identity:

```yaml
node_id: mesh://fieldlight.anni.supra
node_name: supra-edge-node
node_class: vehicle_edge
operator: Anni McHenry
canonical_controller: mesh://fieldlight.anni.lemur
publishing_layer: mesh://fieldlight.anni.astra
```

The Supra node should be treated as a peer node with narrower authority than Lemur.

- Lemur remains source-of-truth authority.
- Astra remains publishing-layer witness/runtime.
- Supra captures mobile context and queues sync.
- Supra does not silently promote observations into canon.

## Physical Topology

```text
Home Node / Heavy Compute
        |
Fieldlight Mesh / Tailscale
        |
Supra Edge Node
        |
Raspberry Pi 5 + Samsung T7
        |
+------------+------+--------+-------+
|            |      |        |       |
VIOFO       GPS   BLE      Shure   Local API
Dual 4K          OBD-II   MV7+
        |
iPad Cockpit Interface
```

## Phase 1 Hardware

The first Supra node is built around the actual hardware ordered for the car:

- Raspberry Pi 5 as the local orchestrator.
- Samsung T7 SSD as primary local memory.
- GL.iNet router as the private Supra network.
- VIOFO dual 4K dash cam as the visual memory source.
- BLE OBD-II adapter as the vehicle telemetry source.
- Shure MV7+ as optional high-quality voice capture.

Phase 1 does not attempt live VIOFO video streaming. The dash cam records normally first; the Pi indexes copied/exported clips later as local media references.

## Phase 1 Build Target

Phase 1 succeeds when the vehicle can:

1. Boot a Raspberry Pi 5 as `mesh://fieldlight.anni.supra`.
2. Store node-local config and logs on encrypted Samsung T7-backed storage.
3. Capture or ingest timestamp, GPS/route, OBD-II context, and at least one dashcam media reference.
4. Accept a manual bookmark from the iPad or local API.
5. Bind that bookmark to nearby context.
6. Queue the event for explicit sync to a trusted home node.
7. Respond to a Fieldlight Mesh `ping` over a trusted network.

The practical win condition is the drive bookmark loop: during or after a drive, create a Fieldlight event that binds timestamp, route/GPS, OBD context, human label, note, and dashcam media reference while keeping custody local.

## Node Responsibilities

### Capture Layer

Inputs may include:

- front VIOFO dashcam reference
- rear VIOFO dashcam reference
- GPS fix or route segment
- BLE OBD-II telemetry
- Shure MV7+ voice note reference
- manual bookmark
- optional cabin context
- optional weather or landmark metadata

### Memory Layer

Local storage should preserve:

- raw event references
- normalized event metadata
- bookmark labels
- sync status
- audit timestamps
- hashes for media references when available

### Meaning Layer

The node observes. The human assigns significance.

Bookmark examples:

- `field_note`
- `beautiful`
- `research`
- `near_miss`
- `important_conversation`
- `strange_interaction`
- `institute_idea`
- `follow_up_later`

### Sync Layer

Synchronization must be explicit and inspectable.

Acceptable first sync behavior:

- queue event locally
- show pending sync count
- sync only to a trusted peer
- mark synced event with destination and timestamp
- never delete local event solely because it synced

## Phase 1 Runtime

The Phase 1 runtime lives in `fieldlight_mesh.mobile_edge`.

It provides:

- SQLite event store as the local source of truth.
- YAML/JSON export for mesh-compatible events.
- Human-authored bookmark creation.
- OBD telemetry adapter boundary through the event `vehicle` field.
- VIOFO file-reference indexing through `mobile_edge.media_reference`.
- Review-gated sync manifest generation.
- Minimal local API and iPad cockpit page.

Operator CLI:

```bash
fieldlight-mesh mobile-edge init
fieldlight-mesh mobile-edge bookmark --labels field_note,institute_idea --note "first drive note"
fieldlight-mesh mobile-edge recent
fieldlight-mesh mobile-edge ingest-media /Volumes/T7/viofo/example.mp4 --note "front clip"
fieldlight-mesh mobile-edge manifest --review
fieldlight-mesh mobile-edge serve --host 0.0.0.0 --port 8765
```

For Pi use, serve on the GL.iNet/Tailscale-accessible interface only when the network is trusted. Phase 1 has no login wall.

## SIL Message Strategy

Phase 1 should use existing runtime message types rather than adding premature handlers.

Use:

- `ping` for reachability
- `message` for bookmark/event payloads
- `message` for health and sync payloads until a dedicated `trace` route is enabled
- `query` for later retrieval requests
- `response` for acknowledgements

Payloads should include a specific `event_type`:

- `mobile_edge.bookmark`
- `mobile_edge.health`
- `mobile_edge.sync_manifest`
- `mobile_edge.media_reference`

This lets the current mesh transport carry vehicle events before the runtime has dedicated Mobile Edge handlers.

## Event Custody Rules

- Raw media remains local by default.
- Metadata may sync only when policy allows it.
- Location data is sensitive and must be treated as local-first.
- Cabin audio/video must be opt-in and clearly marked.
- Human-authored bookmarks outrank inferred labels.
- AI-generated summaries must remain traceable to source events.

## First Local API Surface

Minimum local endpoints implemented by the Phase 1 HTTP service:

```text
GET  /health
POST /bookmark
GET  /events/recent
POST /media/ingest
POST /sync/manifest
```

The iPad cockpit can sit on top of this API without needing direct access to lower-level Pi services.

## Phase 1 Decisions

- VIOFO remains autonomous; the Pi ingests copied files after a drive.
- OBD-II is treated as BLE unless hardware proves otherwise.
- Samsung T7 is the primary memory store.
- SQLite is the primary event store; YAML/JSON are exports.
- Raw media and exact location never sync automatically.
- Human bookmarks are first-class events and outrank inferred labels.
- Sync to Lemur/home is designed now, but raw media remains local until reviewed.

## Related Files

- [`../nodes/supra_edge_node.yml`](../nodes/supra_edge_node.yml)
- [`../config/mobile_edge/event_schema.yml`](../config/mobile_edge/event_schema.yml)
- [`../config/mobile_edge/sync_policy.yml`](../config/mobile_edge/sync_policy.yml)
- [`SUPRA_PHASE1_RUNBOOK.md`](SUPRA_PHASE1_RUNBOOK.md)
- [`../send/examples/mobile_edge/bookmark_event.yml`](../send/examples/mobile_edge/bookmark_event.yml)
- [`../send/examples/mobile_edge/health_trace.yml`](../send/examples/mobile_edge/health_trace.yml)
- [`../send/examples/mobile_edge/sync_manifest.yml`](../send/examples/mobile_edge/sync_manifest.yml)
