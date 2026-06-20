# Astra + Charlie Mac Alpha

This field test proves bidirectional, durable messaging over a trusted local network.

## Boundary

Fieldlight Mesh 0.2 sends plaintext TCP. It does not yet provide encryption or cryptographic identity verification. Use harmless test content, remain on a trusted LAN, and do not expose port 7750 to the public internet.

Go, libp2p, Docker, and Tailscale are not required for this test.

## Install on both Macs

Use Python 3.12 where available:

```bash
cd 04_infrastructure/mesh
python3 -m venv .venv
.venv/bin/pip install -e '.[discovery,dev]'
.venv/bin/fieldlight-mesh --help
```

Initialize Astra:

```bash
.venv/bin/fieldlight-mesh init \
  --name astra \
  --node-id mesh://fieldlight.anni.astra
.venv/bin/fieldlight-mesh doctor
```

Charlie initializes a distinct identity:

```bash
.venv/bin/fieldlight-mesh init \
  --name charlie \
  --node-id mesh://fieldlight.charlie.mac
.venv/bin/fieldlight-mesh doctor
```

Node state is stored under `~/Library/Application Support/Fieldlight Mesh`. Set `FIELDLIGHT_HOME` or pass global `--home PATH` to isolate a test identity.

## Same-Mac Smoke

On Astra, trust a temporary local sender and run the node:

```bash
.venv/bin/fieldlight-mesh peers trust mesh://fieldlight.test.local
.venv/bin/fieldlight-mesh node --host 127.0.0.1
```

In a second terminal, use an isolated sender identity:

```bash
FIELDLIGHT_HOME=/tmp/fieldlight-local .venv/bin/fieldlight-mesh init \
  --name local --node-id mesh://fieldlight.test.local
FIELDLIGHT_HOME=/tmp/fieldlight-local .venv/bin/fieldlight-mesh send-message \
  mesh://fieldlight.anni.astra "Astra local smoke" --host 127.0.0.1
.venv/bin/fieldlight-mesh inbox
```

Pass: sender receives `status: 202`, `intent: message_received`; Astra's inbox contains the text.

## Two-Mac Enrollment

Find each Mac's Wi-Fi IPv4 address:

```bash
ipconfig getifaddr en0
```

On Astra:

```bash
.venv/bin/fieldlight-mesh peers add mesh://fieldlight.charlie.mac --host CHARLIE_IPV4
.venv/bin/fieldlight-mesh peers trust mesh://fieldlight.charlie.mac
.venv/bin/fieldlight-mesh node --advertise
```

On Charlie:

```bash
.venv/bin/fieldlight-mesh peers add mesh://fieldlight.anni.astra --host ASTRA_IPV4
.venv/bin/fieldlight-mesh peers trust mesh://fieldlight.anni.astra
.venv/bin/fieldlight-mesh node --advertise
```

Allow incoming Python connections and Local Network access if macOS prompts.

Either Mac can inspect mDNS hints without granting trust:

```bash
.venv/bin/fieldlight-mesh peers discover --duration 8
.venv/bin/fieldlight-mesh peers list
```

Discovery never authorizes a peer. Keep the explicit `peers trust` step.

## Bidirectional Acceptance Test

Charlie sends:

```bash
.venv/bin/fieldlight-mesh send-message mesh://fieldlight.anni.astra "Charlie to Astra: field test one"
```

Astra verifies and replies:

```bash
.venv/bin/fieldlight-mesh inbox
.venv/bin/fieldlight-mesh send-message mesh://fieldlight.charlie.mac "Astra to Charlie: received"
```

Charlie verifies:

```bash
.venv/bin/fieldlight-mesh inbox
```

Both directions must return `202 message_received`, and both inboxes must contain the expected message before the test passes.

## Troubleshooting

Check the listener and raw TCP before debugging the protocol:

```bash
lsof -nP -iTCP:7750 -sTCP:LISTEN
nc -vz PEER_IPV4 7750
dns-sd -B _fieldlight._tcp local
```

If mDNS is unreliable, keep the explicit `peers add` address. Confirm both Macs are on the same non-guest Wi-Fi, disable VPNs for the first test, and check macOS Firewall and Local Network permissions.

Stop nodes with `Ctrl+C`. Retain the two response documents, inbox output, timestamp, macOS version, and Python version as test evidence; redact LAN addresses before publishing.
