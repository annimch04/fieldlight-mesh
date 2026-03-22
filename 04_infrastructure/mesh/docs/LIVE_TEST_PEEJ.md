# Live test checklist — external ping (you send → Peej receives)

## Success criteria (v1)

**Pass =** sender prints a YAML **`response`** with **`status: 200`** and **`intent: pong`** returned from the remote host.

**Do not** require log files for first proof. Inspect logs **after** the response works.

## 0. Schema alignment — `ping`

Confirmed in **`config/lemur_route_schema.yml`**:

- **`ping`** exists under `routes:`.
- **`trust_required: any`** — any sender allowed (no peer list required for dev).
- **`auth: optional`** — **no GPG required** for ping; handler accepts without `gpg_signature`.
- Handler maps **`ping`** → **`response`** with **`status: 200`**, **`intent: pong`**.

If anything drifts, fix **`lemur_route_schema.yml`** and **`handler.py`** together.

## 1. Node ID — exact string, three places

1. Peej sends you **one** string, e.g. `mesh://peejmachine` (copy from his node YAML).
2. You put **that exact string** in payload **`to:`**.
3. Peej uses **the same string** for **`--node-id`** (no trimming, no reformatting).

Your **`from:`** = `mesh://fieldlight.anni.lemur` (see **`NODE_ID.md`**).

**No runtime normalization** — mismatch = `404`.

## 2. Auth for this test

**Explicit:** first cross-machine test uses **`message_type: ping`** only → **unauthenticated wire** (auth optional in schema; no GPG check for ping). Do **not** enable `FIELDLIGHT_INSECURE_SKIP_GPG` for ping unless you switch to a type that requires `gpg_sig`.

## 3. Transport — where the pong goes

- **TCP:** response travels on the **same connection** you opened to Peej’s IP:port.
- YAML **`to`** on the response = your **`from`** mesh id (semantic identity); the **bytes** still flow on that socket.

See **`INGRESS_CONTRACT.md`**.

## 4. Logging

Logging is **non-blocking**. If `routing_log.yml` append fails, you still get **`pong`** (warnings on stderr).

## 5. Operational order

1. Peej starts **receiver** (`receive --host 0.0.0.0 --port …`).
2. Peej confirms **exact** `mesh://…` for `--node-id`.
3. Peej confirms **reachable IP** and **firewall** for that TCP port.
4. You **send** ping (use dedicated payload below).
5. Peej confirms process received (optional stderr / console).
6. You confirm **`pong`** in terminal output.
7. **Then** open log files if desired.

## 6. Payload — use a unique marker

Use **`send/examples/ping_peej_live_test_01.yml`** (or copy it):

- **`intent: peej_live_test_01`**
- **`msg_id: peej-live-0001`**

Update **`to:`** to Peej’s exact node id before sending.
