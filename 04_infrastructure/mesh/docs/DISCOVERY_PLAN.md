# Discovery and presence plan

This document is the durable map for **LAN mDNS presence**, **libp2p peer discovery**, and the **bridge** between them. It complements [`TEST_STATUS.md`](./TEST_STATUS.md) (transport test blockers) and [`NODE_ID.md`](./NODE_ID.md) (canonical `mesh://` IDs).

## Goals

1. **LAN track:** Know when another node is **advertising** on the subnet (join/leave as browse results appear and age out). This does **not** prove SIL framing or libp2p handshakes succeed.
2. **libp2p track:** Observe **libp2p-level** peers (mDNS inside libp2p, DHT, bootstrap, rendezvous, etc.). This does **not** by itself give a SIL TCP `--host`/`--port` until mapped.
3. **Bridge:** Correlate one logical node with both a **SIL endpoint** and **libp2p identity/addresses**, so tooling can prefer one path and fall back to the other. The bridge is **additive**: each track must remain **usable alone**.

## Track A — LAN mDNS (Avahi-compatible)

### Service type

- **Canonical:** `_fieldlight._tcp` — Fieldlight-specific; avoids noise from generic `_http._tcp` browsers.
- **Legacy (operator notes):** `_http._tcp` with instance name `FieldlightNode` and port `8080` — still valid for local experiments; browse tooling can optionally watch this.

### Suggested TXT keys (bridge-friendly)

Advertisers should set TXT records where possible (length limits apply; keep values short).

| Key | Meaning |
|-----|---------|
| `mesh_uri` | SIL node id, e.g. `mesh://fieldlight.anni.lemur` |
| `sil_port` | TCP port for `sil_mesh receive` (e.g. `7750`) |
| `sil_host` | Optional; usually omitted (use resolved mDNS target address) |
| `peer` | Optional libp2p **Peer ID** string (future bridge) |
| `v` | Optional schema version for TXT parsing (e.g. `1`) |

Example (Avahi publishes TXT as extra arguments when supported):

```bash
avahi-publish -s "fieldlight-lemur" _fieldlight._tcp 7750 \
  mesh_uri=mesh://fieldlight.anni.lemur sil_port=7750 v=1
```

If your `avahi-publish` build does not accept TXT key=value pairs, use the **Python advertiser** below (`zeroconf`), which sets the same keys.

### Runnable tools — LAN (Track A)

From `04_infrastructure/mesh` with venv:

**Browse** (stream join/leave style events to the terminal):

```bash
.venv/bin/python scripts/lan_presence_browse.py
.venv/bin/python scripts/lan_presence_browse.py --legacy-http
```

**Advertise** this host as `_fieldlight._tcp` with TXT (`mesh_uri`, `sil_port`, optional `peer`):

```bash
.venv/bin/python scripts/lan_presence_advertise.py --instance fieldlight-lemur --port 7750 \
  --mesh-uri mesh://fieldlight.anni.lemur
```

**Write peer registry YAML** (SIL dial hints from LAN; libp2p addrs merged when JSONL is supplied):

```bash
.venv/bin/python scripts/sil_mesh.py discover --duration 8 --legacy-http
.venv/bin/python scripts/sil_mesh.py discover --merge --duration 5   # merge into existing file
.venv/bin/python scripts/sil_mesh.py discover --stdout --duration 3   # print only
```

**Ingest libp2p probe output** (JSON lines on stdout — capture without stderr noise):

```bash
# Record probe JSON lines (from repo: 04_infrastructure/mesh)
cd discovery/libp2p_peer_probe
go run . 2>/dev/null | head -20 > /tmp/libp2p_events.jsonl
cd ../..

.venv/bin/python scripts/sil_mesh.py discover --merge --duration 3 --libp2p-jsonl /tmp/libp2p_events.jsonl
# libp2p only (no LAN scan):
.venv/bin/python scripts/sil_mesh.py discover --merge --skip-lan --libp2p-jsonl /tmp/libp2p_events.jsonl
# stdin:
go run . 2>/dev/null | head -20 | (cd ../.. && .venv/bin/python scripts/sil_mesh.py discover --merge --skip-lan --libp2p-jsonl -)
```

Parsed events: `mdns_peer_found`, `connected` (updates `libp2p_addrs`), `disconnected` (touches `last_seen`). Rows with the same **`peer_id`** (e.g. LAN TXT `peer=` and libp2p ingest) are **coalesced** into one registry entry.

**Send using the registry** (requires a row with matching `mesh_uri` and non-empty `host` / `port`):

```bash
.venv/bin/python scripts/sil_mesh.py send send/examples/ping_to_peer.yml --use-registry
.venv/bin/python scripts/sil_mesh.py send send/examples/ping_to_peer.yml --use-registry \
  --resolve-to mesh://fieldlight.anni.lemur \
  --registry config/discovered_peers.yml
```

`--use-registry` overrides `--host` / `--port` using `to` from the payload (or `--resolve-to` if set). Libp2p-only rows (no SIL host) cannot satisfy SIL dial until LAN or manual YAML supplies `host` and `port`.

Default registry path: `config/discovered_peers.yml` (gitignored). Example shape: `config/discovered_peers.example.yml`.

Join/leave lines on the browse tool are **Added** / **Removed** service events (removal may lag briefly after the peer stops advertising).

## Track B — libp2p

- **`p2pd`** and standalone **`go-libp2p`** nodes each maintain their own peer sets; they are **not** automatically the same process or the same discovery namespace as SIL.
- **In-repo probe:** `discovery/libp2p_peer_probe` — minimal `go-libp2p` host with **mDNS** and **JSON lines** on stdout for `host_started`, `mdns_peer_found`, `connected`, `disconnected`:

```bash
cd discovery/libp2p_peer_probe
go run . --service-name fieldlight-libp2p
```

Current `go-libp2p` pulls a **recent Go toolchain** (see `go.mod`); allow the Go toolchain to auto-download if prompted.

- **Independence:** this probe runs without Python, without `_fieldlight._tcp`, and without SIL.

## Bridge (registry + TXT `peer`)

**Intent:** One **logical node** (identified by `mesh_uri` / human label) can be reached via:

- SIL TCP → from resolved LAN TXT, `discovered_peers.yml`, or static `--host`/`--port`, and/or
- libp2p → from peer ID + multiaddrs.

**Minimal bridge contract:**

- LAN TXT supplies **`mesh_uri`** + **`sil_port`** and optional **`peer`** (libp2p Peer ID string).
- libp2p side supplies **Peer ID** + **multiaddrs** (e.g. from `libp2p_peer_probe` or your daemon).
- **`sil_mesh discover`** merges **LAN scan** and optional **`--libp2p-jsonl`** into **`config/discovered_peers.yml`**, then **coalesces** rows that share **`peer_id`** (bridge). **`sil_mesh send --use-registry`** resolves **`mesh_uri` → host:port** for SIL TCP (libp2p multiaddrs are carried for future transports, not dialed by SIL v1).

**Rule:** If the bridge is down or incomplete, **Track A** and **Track B** still work on their own for their respective semantics.

## Relation to cross-host SIL tests

[`TEST_STATUS.md`](./TEST_STATUS.md) documents **raw TCP reachability** (e.g. Tailscale path). Discovery does **not** replace fixing that path; it helps **find** endpoints on LAN and, later, align libp2p with SIL identities.

## Validated end-to-end — local discovery → registry → SIL send (2026-05-06)

This path was run successfully on a **single host** (automated operator run): **mDNS advertise → browse → `discover` → `send --use-registry` → `pong`**.

**Ordering (four terminals or background jobs):**

1. **Receive:** `sil_mesh receive --host 0.0.0.0 --port 7750 --node-id mesh://fieldlight.anni.lemur`  
   Must match the SIL payload’s **`to:`** (e.g. `send/examples/ping_to_peer.yml`).
2. **Advertise:** `lan_presence_advertise.py --instance fieldlight-lemur --port 7750 --mesh-uri mesh://fieldlight.anni.lemur`
3. **Optional:** `lan_presence_browse.py` — expect **`[+]`** on `fieldlight-lemur._fieldlight._tcp.local.` with TXT `mesh_uri` / `sil_port` / `v`.
4. **Registry:** `sil_mesh discover --duration 3 -o config/discovered_peers.yml` (or `--stdout` to inspect without writing).
5. **Send:** `sil_mesh send send/examples/ping_to_peer.yml --use-registry` (optional `--no-log`).

**Observed success criteria:**

- Discover produced a row for **`mesh://fieldlight.anni.lemur`** with **`host`** and **`port`** (here **`127.0.0.1:7750`** after browse resolved the advertisement).
- Sender printed **`Registry dial mesh://fieldlight.anni.lemur -> …`** and a YAML **`response`** with **`status: 200`** and **`intent: pong`**.

**Operator notes:**

- On a machine with **non-loopback LAN addresses**, `lan_presence_advertise.py` typically registers those IPs; browse/discover may then show a LAN IP instead of (or in addition to) loopback. Same-host runs may still resolve **`127.0.0.1`** only if that is what mDNS returns first—behavior is still valid for SIL dial.
- **`config/discovered_peers.yml`** is **gitignored**; regenerate with `discover` when needed.
- Stop **`receive`** and **`lan_presence_advertise`** when finished so ports and mDNS registrations are not left open.
