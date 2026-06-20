# Publishing Layer

This document defines the Mac / Octopus publishing boundary for Fieldlight.

## Core Split

Lemur remains the Fieldlight source-of-truth node.

The Mac is the publishing layer and the host of Astra, an independently identified mesh runtime node.

This distinction keeps canonical state, local-first memory, and consent-gated execution separate from the outward-facing process of drafting, packaging, and publishing artifacts.

Astra (`mesh://fieldlight.anni.astra`) may run packaged mesh transport, maintain its own peer trust and inbox state, and participate in explicit tests. Astra does not inherit Lemur's identity or silently become Fieldlight's canonical source node.

## Lemur Source Authority

Lemur is the System76 node identified in this repository as the primary Fieldlight node.

Lemur remains authoritative for:

- source protocols
- Fieldlight canonical state
- consent-gated local execution
- private trace and invocation records
- Kestrel and Ghost agent activity
- root routing and memory continuity

A Mac-side artifact may reference Lemur-derived truth, but it should not silently become canon.

## Mac Publishing Role

The Mac is allowed to act as a publication workbench.

It may:

- prepare public summaries
- draft blog posts, docs, decks, and site material
- stage GitHub documentation updates
- scrub private material for public use
- track publication state
- maintain review queues

It should not:

- originate canonical Fieldlight state without source verification
- overwrite Lemur-side truth
- blur private memory, scrubbed export, and public artifact states
- treat convenience copies as authoritative records

## Octopus

Octopus is the Codex-side publishing-layer companion on the Mac.

It is not Kestrel.
It is not Ghost.
It is not Lemur.

Octopus watches the publication boundary. Its job is to hold many outgoing artifacts at once without collapsing their state.

Expected Octopus states:

- `source`: Lemur, Mac draft, GitHub, Posthaven, unknown
- `status`: draft, verified, needs consent, ready to publish, published
- `boundary`: private, scrubbed, public
- `action`: witness, package, export, publish, revoke echo

Suggested arms:

1. source
2. consent
3. trace
4. draft
5. package
6. publish
7. echo
8. witness

## Relationship to Existing Mesh Docs

Runtime execution still belongs under the technical path:

- `TECH_INDEX.md`
- `NET_LAYER.md`
- `INGRESS_CONTRACT.md`
- `NODE_ID.md`
- `TEST_STATUS.md`

Canon and symbolic framing still belong under the canon path:

- `CANON_INDEX.md`
- `00_Start_Here/`
- mesh design specs

The publishing layer sits between private source truth and public artifact release. It is a boundary and workflow layer, not a replacement for runtime or canon.

## Publication Rule

Before an artifact leaves the private system, Octopus should help answer four questions:

1. What is the source?
2. What consent applies?
3. What trace or attribution must remain attached?
4. Is this draft, scrubbed export, or public record?

If those answers are unclear, the artifact is not ready to publish.
