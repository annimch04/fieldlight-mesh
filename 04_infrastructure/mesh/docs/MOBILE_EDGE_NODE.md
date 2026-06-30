# Mobile Edge Node Technical Profile

Status: Phase 1 technical scaffold  
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
Raspberry Pi 5 + SSD
        |
+------------+------+--------+-------+
|            |      |        |       |
Dashcams    GPS   OBD-II   Voice   Local API
        |
iPad Cockpit Interface
```

## Phase 1 Build Target

Phase 1 succeeds when the vehicle can:

1. Boot a Raspberry Pi 5 as `mesh://fieldlight.anni.supra`.
2. Store node-local config and logs on encrypted SSD-backed storage.
3. Capture or ingest timestamp, GPS, OBD-II, and at least one camera reference.
4. Accept a manual bookmark from the iPad or local API.
5. Bind that bookmark to nearby context.
6. Queue the event for explicit sync to a trusted home node.
7. Respond to a Fieldlight Mesh `ping` over a trusted network.

## Node Responsibilities

### Capture Layer

Inputs may include:

- front dashcam reference
- rear dashcam reference
- GPS fix
- OBD-II telemetry
- voice note reference
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

Minimum local endpoints, whether implemented as HTTP, CLI, or local socket:

```text
GET  /health
POST /bookmark
GET  /events/recent
POST /sync/queue
POST /sync/run
```

The iPad cockpit can sit on top of this API without needing direct access to lower-level Pi services.

## Open Implementation Questions

- Should Phase 1 ingest existing dashcam files or control cameras directly?
- What GPS source is most reliable: dedicated USB GPS, phone/iPad, or vehicle data?
- What OBD-II adapter is trusted enough for always-on use?
- Which data classes are never synced automatically?
- What is the first event log format: YAML, SQLite, or both?
- What should the cockpit display when the node is offline but healthy?
- What is the graceful shutdown path when auxiliary power drops?

## Related Files

- [`../nodes/supra_edge_node.yml`](../nodes/supra_edge_node.yml)
- [`../config/mobile_edge/event_schema.yml`](../config/mobile_edge/event_schema.yml)
- [`../config/mobile_edge/sync_policy.yml`](../config/mobile_edge/sync_policy.yml)
- [`../send/examples/mobile_edge/bookmark_event.yml`](../send/examples/mobile_edge/bookmark_event.yml)
- [`../send/examples/mobile_edge/health_trace.yml`](../send/examples/mobile_edge/health_trace.yml)
- [`../send/examples/mobile_edge/sync_manifest.yml`](../send/examples/mobile_edge/sync_manifest.yml)
