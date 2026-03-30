# Live test checklist — external ping (you send → Peej receives)

Current execution state, timeline, and **blocked-path notes** are in [`TEST_STATUS.md`](./TEST_STATUS.md) (including **2026-03-29** Tailscale + `nc` proof + next steps).

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

---

## 7. Tailscale / multi-path — verify from the **sender** machine

A successful `nc` or `sil_mesh` from **Peej’s phone** or another host on **his** tailnet proves **his** listener and **that** path. It does **not** prove the **sender’s** node can open TCP to the same address.

**Before** treating `sil_mesh` as “wrong,” run on the **same OS** that runs `sil_mesh send`:

```bash
nc -vz 100.104.20.119 7750
```

- **succeeded** → proceed with `sil_mesh send`; if send still fails, compare **Python socket** vs `nc` (MTU, bind address, etc.).
- **timeout / refused** → treat as **network path** (sender routing, firewall OUTPUT, tailscale ACLs, asymmetric path), not as SIL/schema bugs.

**IPv6 vs Tailscale:** Prefer **one** agreed address family per session (Tailscale IPv4 **or** global IPv6) so everyone matches `--host` and firewall rules.

### If transport works but output looks confusing

Use a **plain HTTP** listener on the receiver (`python3 -m http.server 7750 --bind 0.0.0.0`) and **`curl -v`** from the sender to confirm **TCP + HTTP** before debugging SIL framing.

### Asymmetric path / capture

If **ICMP** or **tailscale ping** works but **TCP** does not from the sender, suspect **policy/routing** (not “listener down”). Optional: **tcpdump** on sender egress and receiver ingress on the next attempt; optional **reverse-direction** TCP (receiver → sender) to detect asymmetric blocks.

---

## 8. Sanity check — you’re not “thinking too much”

Isolating **control-plane vs data-plane** (ping vs TCP to **port**), **proving the receiver locally**, and **proving path from the sender** are normal steps. The repo’s **pass** is still: **`response` with `pong`** from the remote `sil_mesh` receive; everything else is **diagnostics** to get there.
