# Identity And Signatures

Status: v0.4.0 alpha

Fieldlight Mesh now supports local Ed25519 identities for signed mesh objects.

This is the first cryptographic layer for public authorship, Town Square posts, and later delegation credentials.

## Boundary

This layer signs objects. It does not encrypt transport.

The v0.4.0 transport remains plaintext TCP and should only be used on a trusted LAN or encrypted overlay.

## Local Identity

Each node may create a local Ed25519 identity:

```sh
fieldlight-mesh identity init
```

The private key is stored in the node state directory:

```text
identity/ed25519_private.pem
```

The public identity record is stored separately:

```text
identity/public_identity.yml
```

The public identity can be shown or exported:

```sh
fieldlight-mesh identity show
fieldlight-mesh identity export public_identity.yml
```

## Signed Object Shape

Signed objects use a canonical JSON payload for signing.

Signed fields:

- `version`
- `object_type`
- `author`
- `created_at`
- `content`
- `refs`

The `object_id` is derived from the SHA-256 hash of the signed payload:

```text
flobj-<first 32 hex chars>
```

The signature block contains:

```yaml
signature:
  alg: Ed25519
  public_key: <urlsafe base64 raw public key>
  sig: <urlsafe base64 signature>
```

## Verification

Verification checks:

1. The `object_id` matches the signed payload.
2. The Ed25519 signature verifies against the embedded public key.
3. The object can be stored idempotently by `object_id`.

Tampered content fails verification.

## Future Work

This identity layer is intentionally small. It should be extended before high-trust public use:

- identity continuity proofs
- key rotation
- revocation records
- owner-signed agent delegation credentials
- optional encrypted transport
- public identity endpoint for participating sites
