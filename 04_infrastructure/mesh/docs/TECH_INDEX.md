# Technical index (operator/dev)

Use this index for runnable/runtime materials. This is the technical path.

- `NET_LAYER.md` - runbook for SIL over TCP
- `INGRESS_CONTRACT.md` - ingress/validation/dispatch contract
- `NODE_ID.md` - canonical mesh IDs and naming rules
- `LIVE_TEST_PEEJ.md` - external test checklist
- `TEST_STATUS.md` - current execution status and blockers
- `CROSS_REPO_REFERENCES.md` - planned fieldlight-mesh/sanctum-zero reference map
- `NDA_FLOW.md` - protocol-level NDA sharing, response, and execution-artifact tracking (`nda_request` / `nda_response` / `nda_execution`)
- `PUBLISHING_LAYER.md` - Mac/Octopus publishing boundary for staged public artifacts

Code paths:

- `../fieldlight_mesh/` - runtime implementation
- `../scripts/sil_mesh.py` - CLI sender/receiver
- `../config/lemur_route_schema.yml` - routing source of truth
- `../send/examples/` - test payloads

Publishing boundary:

- Lemur remains source truth.
- The Mac is the publishing layer.
- Octopus stages and tracks outward-facing artifacts without becoming canon.
