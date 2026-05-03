# NDA flow (protocol v1)

This document defines a **protocol-level NDA exchange** between mesh nodes.

## Scope and caveat

- This flow tracks intent, transfer reference, review state, execution state, and artifact hashes over SIL.
- It is **not by itself** a complete legal-signature/enforcement system.
- Use this as transport + audit scaffolding; attach your legal workflow above it.
- Final legal validity depends on the governing agreement, signature method, parties, jurisdiction, and retained records.

## Purpose

The mesh can be used to share and execute an NDA without treating the mesh as the legal authority.

The mesh provides:

- identity-aware routing between nodes
- document transfer references
- hash-based artifact integrity
- review and decision status
- execution artifact correlation
- traceable audit logs

The legal/signature layer provides:

- the actual NDA text
- party identity requirements
- signature or acceptance mechanism
- governing law and enforceability terms
- storage of executed legal record

## Message types

- `nda_request`
- `nda_response`
- `nda_execution`
- `nda_execution_ack`

## Required fields

### nda_request

```yaml
message_type: nda_request
from: mesh://sender.node
to: mesh://receiver.node
msg_id: nda-req-0001
nda_id: NDA-2026-0001
document_hash: "sha256:<hex>"
document_name: mutual_nda_v1.pdf
document_ref: https://example.invalid/nda/mutual_nda_v1.pdf
intent: nda_exchange_request
```

Required for handler acceptance:

- `nda_id`
- `document_hash`

If either is missing, handler returns `status: 422`, `intent: nda_invalid`.

### nda_response

```yaml
message_type: nda_response
from: mesh://receiver.node
to: mesh://sender.node
msg_id: nda-resp-0001
in_reply_to: nda-req-0001
nda_id: NDA-2026-0001
decision: accepted   # accepted | rejected | needs_review
intent: nda_exchange_response
```

### nda_execution

Use `nda_execution` after the parties have completed the external signing or acceptance step.

```yaml
message_type: nda_execution
from: mesh://sender.node
to: mesh://receiver.node
msg_id: nda-exec-0001
in_reply_to: nda-resp-0001
nda_id: NDA-2026-0001
execution_status: executed   # executed | voided | superseded
executed_document_hash: "sha256:<hex>"
executed_document_name: mutual_nda_v1_executed.pdf
executed_document_ref: https://example.invalid/nda/mutual_nda_v1_executed.pdf
signature_method: external_e_signature
signed_at: "2026-05-03T12:00:00Z"
intent: nda_execution_notice
```

Required for handler acceptance:

- `nda_id`
- `execution_status`
- `executed_document_hash`

### nda_execution_ack

```yaml
message_type: nda_execution_ack
from: mesh://receiver.node
to: mesh://sender.node
msg_id: nda-exec-ack-0001
in_reply_to: nda-exec-0001
nda_id: NDA-2026-0001
status: 200
intent: nda_execution_ack
```

## Share and execute flow

1. Prepare the NDA document outside the mesh.
2. Compute a SHA-256 hash of the exact document being shared.
3. Send `nda_request` over the mesh with `nda_id`, `document_hash`, and `document_ref`.
4. Receiver validates message shape and hash presence.
5. Receiver replies with `nda_response`:
   - `needs_review` if human/legal review is required.
   - `accepted` if the receiver is ready to proceed to execution.
   - `rejected` if the NDA is declined.
6. Parties complete the legal signing/acceptance step outside the mesh.
7. Sender computes a SHA-256 hash of the executed document.
8. Sender sends `nda_execution` with `executed_document_hash` and execution metadata.
9. Receiver verifies the executed artifact reference and returns `nda_execution_ack`.
10. Both sides retain the message chain and executed document in their legal/archive system.

## Default handler behavior (current)

For a valid `nda_request`, receiver replies:

- `status: 200`
- `intent: nda_received_review_required`
- `decision: needs_review`

For `nda_response`, receiver replies:

- `status: 200`
- `intent: nda_response_ack`

For `nda_execution`, receiver should reply:

- `status: 200`
- `intent: nda_execution_ack`

If `nda_execution` is missing `nda_id`, `execution_status`, or `executed_document_hash`, receiver should return:

- `status: 422`
- `intent: nda_execution_invalid`

## Logging

NDA messages are logged via standard routing/audit logs using `msg_id`.
Recommended correlation keys:

- `msg_id`
- `in_reply_to`
- `nda_id`
- `document_hash`
- `executed_document_hash`
- `execution_status`
- `signed_at`

## Boundary rule

The mesh can prove what was sent, when it was routed, what hash identified the document, and what execution artifact was later referenced.

The mesh should not claim that a document is legally enforceable by transport alone.

Legal execution remains a higher-level workflow layered above the mesh.
