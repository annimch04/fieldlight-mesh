# Technical index (operator/dev)

Use this index for runnable/runtime materials. This is the technical path.

- **CI** — repo root [`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml) (Python mesh + Go probe). Local parity: `make -C 04_infrastructure/mesh ci-local` after `make install`.

- `NET_LAYER.md` - runbook for SIL over TCP
- `INGRESS_CONTRACT.md` - ingress/validation/dispatch contract
- `IDENTITY_AND_SIGNATURES.md` - Ed25519 local identity, signed objects, and verification rules
- `TOWN_SQUARE.md` - signed public wall alpha and trusted-peer bundle sync
- `NODE_ID.md` - canonical mesh IDs and naming rules
- `LIVE_TEST_PEEJ.md` - external test checklist
- `TEST_STATUS.md` - current execution status and blockers
- `DISCOVERY_PLAN.md` - LAN mDNS + libp2p discovery + bridge; **validated local** flow (2026-05-06) at end of doc
- `CROSS_REPO_REFERENCES.md` - planned fieldlight-mesh/sanctum-zero reference map
- `NDA_FLOW.md` - protocol-level NDA sharing, response, and execution-artifact tracking (`nda_request` / `nda_response` / `nda_execution`)
- `PUBLISHING_LAYER.md` - Mac/Octopus publishing boundary for staged public artifacts
- `DIGITAL_SELF_ARCHITECTURE.md` - digital self continuity contract across Fieldlight transport, Sanctum memory, local governance, and public authorship
- `CODEX_LOCAL_FIRST_GOVERNANCE.md` - Codex/local-agent workflow for governed local project folders

Code paths:

- `../fieldlight_mesh/` - runtime implementation (`lan_mdns.py`, `peer_registry.py`, …)
- `../scripts/sil_mesh.py` - CLI `send` / `receive` / `discover`
- `../config/discovered_peers.example.yml` - registry shape (`discovered_peers.yml` is gitignored)
- `../scripts/lan_presence_browse.py` - stream LAN mDNS presence
- `../scripts/lan_presence_advertise.py` - register `_fieldlight._tcp` + TXT
- `../discovery/libp2p_peer_probe/` - Go libp2p mDNS + connection JSON log
- `../config/lemur_route_schema.yml` - routing source of truth
- `../send/examples/` - test payloads

Publishing boundary:

- Lemur remains source truth.
- The Mac is the publishing layer.
- Octopus stages and tracks outward-facing artifacts without becoming canon.
