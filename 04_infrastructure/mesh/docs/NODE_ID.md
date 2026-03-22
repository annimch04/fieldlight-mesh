# Canonical node identity (Lemur)

| Kind | Value |
|------|--------|
| **Mesh node URI** (SIL `from` / `to`, `sil_mesh --node-id`) | `mesh://fieldlight.anni.lemur` |
| **GPG UID name** (key generation / `gpg --export`) | `Fieldlight-Anni-Lemur` (human-readable; not interchangeable with the mesh URI) |

All SIL examples in this repo should use the **mesh URI** form for routing. The GPG name is only for cryptographic identity operations.

**Example peer (tests / stubs only):** `mesh://sam.openai.proxy` — used consistently across specs and sample logs (not a real endpoint).
