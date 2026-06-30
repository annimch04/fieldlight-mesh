# Fieldlight Mesh Runtime

Fieldlight Mesh includes a peer-facing macOS application and an operator CLI over the same local-first SIL runtime.

- Peer install: `docs/PEER_INSTALL_MACOS.md`
- Astra and peer acceptance test: `docs/MAC_ALPHA_RUNBOOK.md`
- Identity and signatures: `docs/IDENTITY_AND_SIGNATURES.md`
- Town Square signed public wall alpha: `docs/TOWN_SQUARE.md`
- Build the macOS app: `scripts/build_macos_app.sh`
- Mobile Edge Node technical profile: `docs/MOBILE_EDGE_NODE.md`

Town Square posts are signed with local Ed25519 identities. Transport still sends plaintext YAML over TCP. Use it only on a trusted LAN or inside a trusted encrypted network such as Tailscale.
