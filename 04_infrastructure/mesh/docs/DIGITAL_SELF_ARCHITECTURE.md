# Digital Self Architecture

Status: proposed

Related article: [Fieldlight | The Self on the Wire](https://sayitplain.posthaven.com/fieldlight-the-self-on-the-wire)

## Purpose

This document defines the digital self as the continuity layer connecting Fieldlight Mesh runtime transport, Sanctum-Zero memory continuity, local-first governance, and public authorship projection.

Fieldlight Mesh remains responsible for runtime exchange: routing, ingress, peer discovery, consent-scoped messages, trace references, and node-to-node interaction.

Sanctum-Zero remains responsible for substrate: memory, identity continuity, symbolic governance, local cognition primitives, and reorientation after context loss.

The digital self sits across both systems as a verifiable identity continuity contract.

## Definition

A digital self is not a profile, avatar, account, or model persona.

It is a human-owned continuity layer that binds:

- a living human subject
- local-first memory
- public authorship record
- cryptographic identity anchor
- consent and export policy
- agent behavior rules
- peer-to-peer verification

The digital self must preserve continuity without requiring full disclosure of private memory.

## Root Value

Every digital self should have one root system value:

```yaml
digital_self_root:
  subject: living_human
  continuity_id: cryptographic_anchor
  verification: public_key_or_signature_chain
  canonical_source: local_first_memory
  public_projection: selective
  consent_required_for:
    - training
    - replication
    - export
    - peer_exchange
    - automated_action
```

This root value allows agents and peers to verify continuity while respecting local boundaries.

## Layer Model

```text
Living human
  -> Sanctum local memory
  -> identity anchor
  -> local project governance bundle
  -> Codex / local agent engagement
  -> Fieldlight SIL / mesh exchange
  -> public projection and authored record
```

## Repository Boundary

Fieldlight Mesh owns:

- mesh node identifiers
- Signal Intent Language payloads
- ingress validation and dispatch
- peer discovery and routing
- consent-scoped message exchange
- trace references for live actions

Sanctum-Zero owns:

- append-only memory substrate
- identity anchor patterns
- reorientation workflows
- local cognition primitives
- symbolic governance
- portable continuity records

Cross-reference for context. Do not duplicate source-of-truth runtime contracts across repositories.

## Mesh Implications

Peer-to-peer exchange should not require a peer to see the full private memory archive.

A peer needs enough proof to evaluate:

- whether a message belongs to the expected continuity chain
- whether the node is authorized to speak in the requested scope
- whether the request carries consent boundaries
- whether the artifact has traceable authorship
- whether response logging is allowed

This allows Fieldlight Mesh to support verifiable human continuity without depending on centralized identity providers.

## Public Projection

Public authorship is part of digital self continuity. Blog posts, repositories, documentation, commits, essays, and published protocols can all serve as public verification surfaces.

Public does not mean ownerless.

Public artifacts should be treated as authored projections, not as unrestricted training material or consent-free replication sources.

## Future Work

- Define `.fieldlight/identity-anchor.yml`
- Define `.fieldlight/consent-policy.yml`
- Define `.fieldlight/agent-behavior.yml`
- Add SIL fields for digital self continuity references
- Add peer verification flow for continuity proofs
- Extend article references as the public Fieldlight writing set grows
