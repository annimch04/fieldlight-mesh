# Supra Mobile Edge Node Phase 1 Runbook

Status: build runbook
Node: `mesh://fieldlight.anni.supra`
Vehicle: Toyota Supra
Phase 1 goal: drive bookmark loop

## Success Condition

Phase 1 is complete when a short drive can produce at least one Fieldlight event that binds:

- timestamp
- human label
- human note
- route/GPS context when available
- OBD-II snapshot when available
- VIOFO media reference after file ingest
- local custody on the Samsung T7
- explicit sync manifest for Lemur/home review

Raw media stays local unless reviewed.

## Hardware Inventory

- Raspberry Pi 5: local orchestrator.
- Samsung T7 SSD: primary memory store.
- GL.iNet router: Supra private network.
- VIOFO dual 4K dash cam: front/rear visual memory source.
- BLE OBD-II adapter: vehicle telemetry source.
- Shure MV7+: optional voice capture.
- iPad: cockpit surface for bookmarks and node status.

## 1. Raspberry Pi OS Setup

1. Install Raspberry Pi OS Lite or Desktop on the Pi 5.
2. Set hostname to `supra-edge-node`.
3. Enable SSH only on the trusted Supra LAN/Tailscale path.
4. Install Python 3, Git, and system packages needed for SQLite/BLE tooling.
5. Clone `fieldlight-mesh` onto the T7-backed project path.
6. Install the mesh runtime locally:

```bash
cd fieldlight-mesh/04_infrastructure/mesh
python3 -m pip install -e .
fieldlight-mesh --home /mnt/fieldlight-supra init --name supra-edge-node --node-id mesh://fieldlight.anni.supra --port 7750
fieldlight-mesh --home /mnt/fieldlight-supra mobile-edge init --root /mnt/fieldlight-supra/mobile_edge
```

## 2. Samsung T7 Mount And Custody Plan

The Samsung T7 is the Supra node memory store.

Recommended mount target:

```text
/mnt/fieldlight-supra
```

Recommended structure:

```text
/mnt/fieldlight-supra/
  mesh_home/
  mobile_edge/
    mobile_edge.sqlite3
    media/
    exports/
  viofo_ingest/
  logs/
```

Phase 1 encryption decision:

- Prefer encrypted T7 storage before routine field use.
- If encryption is delayed during bench testing, label the node as `bench_unencrypted` in notes.
- Do not place private cabin audio, exact route history, or raw dashcam exports on unencrypted storage for normal use.

## 3. GL.iNet Router Topology

The GL.iNet creates the private Supra network.

Recommended roles:

- Router SSID: `Fieldlight-Supra` or equivalent private name.
- Raspberry Pi: wired or stable Wi-Fi client.
- iPad: cockpit client on same LAN.
- Tailscale: trusted mesh reachability when available.
- Internet uplink: optional, not required for drive bookmarking.

First local cockpit URL when served from the Pi:

```text
http://<pi-lan-ip>:8765/
```

For LAN cockpit access:

```bash
fieldlight-mesh --home /mnt/fieldlight-supra/mesh_home mobile-edge \
  --root /mnt/fieldlight-supra/mobile_edge serve --host 0.0.0.0 --port 8765
```

Phase 1 has no login wall. Run this only on the private GL.iNet/Tailscale network.

## 4. Tailscale And Mesh Reachability

Use Tailscale as a trusted overlay when available.

1. Install Tailscale on the Pi.
2. Authenticate the Pi under the correct tailnet.
3. Confirm the Pi appears as `supra-edge-node` or equivalent.
4. From Lemur/home, confirm basic reachability.
5. Run the Fieldlight Mesh doctor on the Pi.
6. Start the mesh node receiver when ready:

```bash
fieldlight-mesh --home /mnt/fieldlight-supra/mesh_home node --host 0.0.0.0 --port 7750
```

## 5. BLE OBD-II Pairing

Phase 1 treats the OBD-II adapter as BLE unless hardware proves otherwise.

Initial steps:

1. Pair the adapter with the Pi.
2. Confirm the adapter is visible after car startup.
3. Capture a minimal sampled telemetry object.
4. Attach the latest known telemetry snapshot to bookmarks through the `vehicle` field.

Example vehicle payload:

```yaml
ignition_state: on
speed_mph: 18
rpm: 1200
obd_source: ble_obd_ii
```

If live BLE integration is not ready, use `ignition_state: unknown`; the bookmark loop still counts as long as the event is created and stored locally.

## 6. VIOFO Dashcam Ingest Workflow

Phase 1 does not live-stream VIOFO video.

Workflow:

1. Let the VIOFO record normally to its own storage during the drive.
2. After the drive, copy selected clips to the T7 ingest folder.
3. Index the copied clip as a local media reference:

```bash
fieldlight-mesh --home /mnt/fieldlight-supra/mesh_home mobile-edge \
  --root /mnt/fieldlight-supra/mobile_edge ingest-media \
  /mnt/fieldlight-supra/viofo_ingest/front-clip.mp4 \
  --labels media_reference,viofo_front \
  --note "front VIOFO clip from first drive"
```

This creates a `mobile_edge.media_reference` event with SHA-256 hash and local path. It does not upload raw media.

## 7. Shure MV7+ Voice Capture

The MV7+ is optional in Phase 1.

Allowed Phase 1 use:

- Explicit voice notes only.
- No ambient cabin recording by default.
- Any voice file should be indexed as a media reference with `review-required` consent scope.

## 8. First Drive Test

Before drive:

1. Boot Pi.
2. Confirm T7 is mounted.
3. Join iPad to GL.iNet network.
4. Start cockpit/API.
5. Open cockpit on the iPad.
6. Confirm `/health` is `ok`.

During drive:

1. Press bookmark button at least once.
2. Add a human note if safe to do so.
3. Let VIOFO record normally.

After drive:

1. Copy one VIOFO clip to T7 ingest folder.
2. Run `mobile-edge ingest-media` for the clip.
3. Generate sync manifest:

```bash
fieldlight-mesh --home /mnt/fieldlight-supra/mesh_home mobile-edge \
  --root /mnt/fieldlight-supra/mobile_edge manifest --review
```

Verify:

- Bookmark event exists in SQLite.
- Media reference exists with SHA-256 hash.
- Manifest marks media as not included.
- Raw media remains local on T7.
- Protected media/location requires review before sync.

## 9. Phase 1 Non-Goals

- No live VIOFO stream.
- No automatic cloud upload.
- No autonomous public publishing.
- No cabin recording without explicit opt-in.
- No home/server sync until the local drive bookmark loop works.

## 10. Next Phase Candidates

After the bookmark loop works:

- BLE OBD telemetry adapter implementation.
- GPS route sampler.
- Media time-window matching for bookmarks.
- T7 encryption hardening.
- Lemur/home sync receiver.
- Cockpit authentication on trusted networks.
