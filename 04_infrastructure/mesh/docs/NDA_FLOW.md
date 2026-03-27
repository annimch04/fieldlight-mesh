# NDA flow (protocol v1)

This document defines a **protocol-level NDA exchange** between mesh nodes.

## Scope and caveat

- This flow tracks intent, transfer reference, and response status over SIL.
- It is **not by itself** a complete legal-signature/enforcement system.
- Use this as transport + audit scaffolding; attach your legal workflow above it.

## Message types

- `nda_request`
- `nda_response`

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

## Default handler behavior (current)

For a valid `nda_request`, receiver replies:

- `status: 200`
- `intent: nda_received_review_required`
- `decision: needs_review`

For `nda_response`, receiver replies:

- `status: 200`
- `intent: nda_response_ack`

## Logging

NDA messages are logged via standard routing/audit logs using `msg_id`.
Recommended correlation keys:

- `msg_id`
- `in_reply_to`
- `nda_id`
- `document_hash`

