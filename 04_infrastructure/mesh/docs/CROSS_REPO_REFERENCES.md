# Cross-repo reference plan (Fieldlight Mesh <-> Sanctum Zero)

Purpose: keep boundaries clear while making inter-repo navigation explicit.

## Direction of responsibility

- `fieldlight-mesh`: transport/runtime, routing, ingress/dispatch, message exchange tests
- `sanctum-zero`: memory substrate, identity continuity patterns, governance primitives

## Candidate reference links to add next

From `fieldlight-mesh` -> `sanctum-zero`:

- identity continuity concepts (anchor patterns)
- ledger/trace conventions for long-lived audit structure

From `sanctum-zero` -> `fieldlight-mesh`:

- runnable mesh transport layer entry (`docs/TECH_INDEX.md`)
- current external test status (`docs/TEST_STATUS.md`)

## Rule for references

- Link across repos for context only.
- Do not duplicate source-of-truth runtime contracts.
- Keep operator docs in technical indexes; keep narrative/governance docs in canon indexes.
