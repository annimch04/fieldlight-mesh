# Runtime ingress contract — `sil_mesh` (SIL over TCP v1)

Single-page contract for what a node **receives**, **validates**, **dispatches**, **rejects**, **responds**, and **logs**.

## Transport

- **Protocol:** TCP, one bidirectional stream per request.
- **Framing:** 4-byte big-endian length + UTF-8 YAML (one SIL document), then optional second frame: same format for the **response** (see `fieldlight_mesh/frame.py`).
- **Return path:** The **pong / response bytes** are written on the **same TCP connection** the client opened. There is no separate “callback” socket. The OS already knows the peer’s address for the open connection.
- **Semantic fields:** `from` / `to` in YAML identify **mesh peers** (identity). They do **not** replace the TCP session; routing for delivery is: **inbound `to` must match receiver `--node-id`**; **response `to` is set to inbound `from`** so the document is self-consistent for logs and future multi-hop work.

## What a node receives

1. Length-prefixed UTF-8 YAML.
2. Parsed as a **SIL** mapping with required keys: `message_type`, `from`, `to` (`fieldlight_mesh/sil.py`).

## Validation order (inbound)

1. **Parse** YAML → fail → `400` **response** (`intent: parse_error`).
2. **Destination:** `to` must match this node’s `--node-id` (string match with optional subpath for `/trace` etc.; see `routing.destination_matches_node`).
3. **TTL / hops:** optional `hop` in message vs route `ttl` (`routing.ttl_exceeded`).
4. **Trust:** `trust_required` from `config/lemur_route_schema.yml` vs `from` and optional `--trusted-peers` file.
5. **Auth:** per route `auth` field (`gpg_sig` / `optional` / `none`) — see `routing.auth_ok` (GPG is **stub** unless extended).

## Dispatch

- By `message_type`, handler returns a **`message_type: response`** document with `status`, `intent`, `in_reply_to`, etc. (`fieldlight_mesh/handler.py`).
- **`ping`** → `status: 200`, `intent: pong` (when allowed).

## Rejection

- Wrong destination → `404` / `no_route_to_peer`.
- TTL exceeded → `410` / `ttl_exceeded`.
- Trust → `403` / `trust_denied`.
- Auth → `403` / `auth_failed`.

## Logging

- **Best-effort:** append to `routing_log.yml` / `message_audit_log.yml`. **Failures are non-fatal** (stderr warning only); **receive/respond still completes**.

## Schema source of truth

- **`config/lemur_route_schema.yml`** — per-type `trust_required`, `ttl`, `auth`, etc. Handler behavior must stay aligned with this file for each `message_type`.
