# Mesh test status (current)

## Session outcome

- Local single-machine test: **PASS** (`ping` -> `pong`)
- Cross-machine test (Anni -> Peej over public IPv6): **BLOCKED** (TCP connect timeout)
- Cross-machine test (Anni -> Peej over Tailscale): **BLOCKED** (TCP connect timeout)

## What has been confirmed

- Peej receiver process runs and listens on `7750`
- Tailscale control path exists (`tailscale ping` succeeds)
- Sender payload is valid and uses `to: mesh://peejmachine`
- SIL handler and framing are not the failure point (raw TCP connect times out before protocol exchange)

## Current blocker

- Network policy/path issue allowing control-plane visibility but blocking service-plane TCP from sender to receiver on `100.104.20.119:7750`.

## Next steps (ordered)

1. Keep `sil_mesh.py receive` running on Peej side.
2. Resolve Tailscale service-plane policy/path for sender -> `100.104.20.119:7750`.
3. Re-run sender command from Anni side.
4. Success criteria: sender prints YAML response with `status: 200` and `intent: pong`.
5. After first success, capture logs and add a dated trace note in this file.

## Commands (retest)

Sender:

```bash
.venv/bin/python scripts/sil_mesh.py send send/examples/ping_peej_live_test_01.yml --host 100.104.20.119 --port 7750
```

Receiver:

```bash
.venv/bin/python scripts/sil_mesh.py receive --host 0.0.0.0 --port 7750 --node-id mesh://peejmachine
```
