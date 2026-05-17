# Codex + Local-First Governance

Status: proposed

Related article: [Fieldlight | The Self on the Wire](https://sayitplain.posthaven.com/fieldlight-the-self-on-the-wire)

## Purpose

This document describes how Codex or another local agent can work inside a Fieldlight / Sanctum project without replacing local-first authority.

The central pattern is simple:

Local project governance lives in the project folder. Agents read that governance before acting.

## Governance Bundle

Suggested local bundle:

```text
.fieldlight/
  identity-anchor.yml
  terms-of-engagement.yml
  consent-policy.yml
  canon-index.yml
  public-projection.yml
  agent-behavior.yml
  peer-policy.yml
  trace-policy.yml
```

This bundle turns a project folder into an authored interaction perimeter.

## Agent Entry Workflow

When Codex enters a governed project folder, it should:

1. Read `.fieldlight/identity-anchor.yml`
2. Read `.fieldlight/terms-of-engagement.yml`
3. Read `.fieldlight/consent-policy.yml`
4. Read `.fieldlight/canon-index.yml`
5. Determine whether requested work is private, scrubbed, public, exportable, or consent-gated
6. Perform local work without changing canon authority
7. Stage outward artifacts with boundary state

## Boundary States

Suggested artifact states:

```yaml
boundary_state:
  source: lemur | mac_draft | github | posthaven | unknown
  status: draft | verified | needs_consent | ready_to_publish | published
  boundary: private | scrubbed | public
  action: witness | package | export | publish | revoke_echo
```

These states align with the existing Mac / Octopus publishing boundary.

## Codex Use Case

Codex can operate in unison with local-first architecture when it treats the local folder as the governance source.

Allowed functions may include:

- drafting documentation
- preparing blog articles
- updating public repo docs
- summarizing local context
- proposing peer messages
- staging artifacts for review
- reading governance before making architectural claims

Codex should not:

- treat Mac drafts as Lemur canon
- export private memory without consent
- collapse private, scrubbed, and public state
- assume public authorship means unrestricted reuse
- initiate peer exchange without policy scope

## Relationship to Fieldlight Mesh

Fieldlight Mesh can use the governance bundle to inform:

- SIL message consent fields
- peer policy
- identity continuity references
- trace logging
- ingress validation
- outward publication state

## Relationship to Sanctum-Zero

Sanctum-Zero provides the memory and identity continuity primitives that make this workflow coherent.

Codex can reorient by reading Sanctum-style anchors and summaries, then perform work inside the current project's governance rules.

## Future Work

- Define schema files for the `.fieldlight/` governance bundle
- Add example governed project folder
- Add Codex reorientation checklist
- Add SIL examples that include digital self continuity references
- Extend article references as the public Fieldlight writing set grows
