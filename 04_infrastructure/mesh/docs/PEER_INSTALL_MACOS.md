# Install Fieldlight Mesh on a Peer Mac

Fieldlight Mesh is distributed as a self-contained macOS application. A peer does not need Python, Git, Homebrew, or a repository checkout.

## Current Build

- Apple Silicon (`arm64`)
- Fieldlight Mesh 0.4.0
- Ad-hoc signed for direct, in-person testing
- Not Apple-notarized

## Install

1. Open `Fieldlight-Mesh-0.4.0-macOS-arm64.dmg`.
2. Drag **Fieldlight Mesh** into **Applications**.
3. On first launch, Control-click the app, choose **Open**, then confirm **Open** if macOS displays an unidentified-developer warning.
4. Allow Local Network and incoming-network access when macOS asks.

The Control-click step is required because this test build is not signed with an Apple Developer ID or notarized. A public release should be Developer ID signed, hardened, notarized, and stapled.

## First Run

The application asks for:

- a local node name
- a unique `mesh://` identity

It creates private node state under:

```text
~/Library/Application Support/Fieldlight Mesh
```

No source checkout or terminal setup is required.

## Connect Two Macs

1. Open the app on both Macs.
2. Select **Start Node** on both.
3. Open **Peers** and select **Discover**.
4. If discovery does not find the other Mac, choose **Add Peer** and enter its mesh identity and LAN IP address.
5. Select the peer and choose **Trust Selected**. Each operator must do this independently.
6. Open **Messages**, choose the peer, write harmless test text, and send.
7. Confirm delivery in the receiving app's inbox.

Discovery never grants trust automatically.

## Security Boundary

Version 0.4.0 is a trusted-LAN alpha. Town Square posts are cryptographically signed, but transport still uses plaintext TCP. Do not expose port 7750 to the public internet or send sensitive material.

The next protocol release will add signed identities and scoped delegation before public town-square or vehicle-agent use.
