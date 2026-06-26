# Town Square

Status: v0.4.0 signed public wall alpha

Town Square is the first public-space protocol in Fieldlight Mesh.

It is a local-first, signed, append-only wall. A node can create public posts, verify authorship, export a bundle, import another node's bundle, or sync the bundle to a trusted peer over SIL.

## Design Rules

- Public reading does not mean ownerless authorship.
- Posts are signed at creation.
- Storage is append-only by default.
- Removal or moderation should be represented by signed records, not silent deletion.
- Replication starts with trusted peers only.
- Transport is still plaintext in v0.4.0.

## Object Types

Current:

- `town_square.post`
- `town_square.reply`

Reserved next:

- `town_square.moderation`
- `town_square.tombstone`
- `identity.key`
- `delegation.grant`

## CLI

Create or show identity:

```sh
fieldlight-mesh identity init
fieldlight-mesh identity show
```

Create a signed post:

```sh
fieldlight-mesh town post "hello from my node"
```

List local feed:

```sh
fieldlight-mesh town list
```

Verify local feed:

```sh
fieldlight-mesh town verify
```

Export/import a bundle:

```sh
fieldlight-mesh town export town-square.yml
fieldlight-mesh town import town-square.yml
```

Sync to a trusted peer already in the registry:

```sh
fieldlight-mesh town sync mesh://fieldlight.peer.example
```

## Mesh Message

Town Square sync uses:

```yaml
message_type: town_square_bundle
from: mesh://fieldlight.node.a
to: mesh://fieldlight.node.b
intent: town_square_sync
bundle:
  bundle_type: fieldlight.town_square.bundle
  version: 1
  exported_at: "..."
  objects:
    - object_type: town_square.post
```

The receiver verifies each object before storing it.

## Acceptance Test

On Astra:

```sh
fieldlight-mesh identity init
fieldlight-mesh town post "Astra is live on the square."
fieldlight-mesh town export astra-square.yml
```

On a peer:

```sh
fieldlight-mesh town import astra-square.yml
fieldlight-mesh town verify
fieldlight-mesh town list
```

For live sync:

1. Start the peer node.
2. Add and trust the sender peer.
3. Run `fieldlight-mesh town sync <peer mesh URI>`.
4. Verify that the receiver reports `town_square_bundle_received`.

## Current Limitations

- No encrypted transport.
- No key rotation or revocation yet.
- No automatic multi-hop replication.
- No moderation/tombstone records yet.
- No public HTTP reader yet.

This is enough to prove the central primitive: public speech can be created locally, signed, moved between nodes, and verified without a platform account being the source of truth.
