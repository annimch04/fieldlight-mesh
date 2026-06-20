# Fieldlight Mesh Runtime

Fieldlight Mesh includes a peer-facing macOS application and an operator CLI over the same local-first SIL runtime.

- Peer install: `docs/PEER_INSTALL_MACOS.md`
- Astra and peer acceptance test: `docs/MAC_ALPHA_RUNBOOK.md`
- Build the macOS app: `scripts/build_macos_app.sh`

This alpha sends plaintext YAML over TCP. Use it only on a trusted LAN or inside a trusted encrypted network such as Tailscale.
