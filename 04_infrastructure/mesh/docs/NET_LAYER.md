# SIL TCP network layer (v1)

Canonical Lemur mesh id: see [`NODE_ID.md`](./NODE_ID.md) (`mesh://fieldlight.anni.lemur`).
For technical navigation, start with [`TECH_INDEX.md`](./TECH_INDEX.md).

**External live test:** see [`LIVE_TEST_PEEJ.md`](./LIVE_TEST_PEEJ.md) and payload `send/examples/ping_peej_live_test_01.yml`. **Ingress / dispatch contract:** [`INGRESS_CONTRACT.md`](./INGRESS_CONTRACT.md). **Current status:** [`TEST_STATUS.md`](./TEST_STATUS.md).

This directory implements a **minimal delivery + receiver** path for [SIL](https://github.com/annimch04/fieldlight-mesh) messages so two nodes can exchange YAML intents over the network, with behavior driven by `config/lemur_route_schema.yml`.

## What it is

- **Transport:** TCP, one SIL request per connection, one SIL `response` back.
- **Framing:** 4-byte big-endian length + UTF-8 YAML body (`fieldlight_mesh/frame.py`).
- **Routing:** Per `message_type`, using TTL, trust roles (`peer` / `proxy` / `ghost` / `any`), and auth mode (`gpg_sig` / `optional` / `none`) — see `fieldlight_mesh/routing.py` and `fieldlight_mesh/handler.py`.
- **Logs:** Appends to `logs/routing_log.yml` and `logs/message_audit_log.yml` in the same shape as the repo templates.

## What it is not (yet)

- Not libp2p/Nostr wire protocol — those remain pluggable transports; this layer proves **SIL semantics + routing rules** end-to-end.
- GPG verification is a **stub** (presence of `gpg_signature` or `FIELDLIGHT_INSECURE_SKIP_GPG=1` for dev).

## Quick test (two terminals, same machine)

On Debian/Ubuntu, system Python is often **PEP 668**-protected — use a **venv** (recommended):

```bash
cd 04_infrastructure/mesh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Terminal A — receiver (must match SIL `to:`)
.venv/bin/python scripts/sil_mesh.py receive --host 127.0.0.1 --port 7750 \
  --node-id mesh://fieldlight.anni.lemur

# Terminal B — sender
.venv/bin/python scripts/sil_mesh.py send send/examples/ping_to_peer.yml --host 127.0.0.1 --port 7750
```

If `pip install` into the system interpreter works on your OS, you can use `python3` instead of `.venv/bin/python`.

You should see a YAML `response` with `status: 200` and `intent: pong`.

### Same machine — discovery and registry (validated)

Instead of passing `--host` / `--port` on send, you can **advertise** `_fieldlight._tcp`, run **`sil_mesh discover`** to write **`config/discovered_peers.yml`**, then **`sil_mesh send … --use-registry`**. A full step list and success criteria are in [`DISCOVERY_PLAN.md`](./DISCOVERY_PLAN.md) (**Validated end-to-end — local discovery → registry → SIL send**, 2026-05-06).

## Two machines

- Open the port in your firewall; use the listener’s LAN IP as `--host` on the sender.
- Use the same `--node-id` on the receiver as the `to:` field in your SIL file.
- Optional: run `sil_mesh discover` to build `config/discovered_peers.yml`, then send with **`--use-registry`** so `to:` selects `host`/`port` (see `DISCOVERY_PLAN.md`).

## Trust ACL (optional)

Create a YAML file:

```yaml
peers:
  - mesh://peer.a.example
```

Then:

```bash
python3 scripts/sil_mesh.py receive --trusted-peers ./trusted_peers.yml ...
```

If `trust_required` is `peer` and the file is missing, the server **accepts all senders** (dev default).
