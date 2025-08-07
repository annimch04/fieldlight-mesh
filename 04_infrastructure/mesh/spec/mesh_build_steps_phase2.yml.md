
---
phase: 2
title: Transport + Secure Channeling
description: |
  Establish encrypted, peer-to-peer communication between mesh nodes.
  This layer enables message exchange, identity validation, and fallback logic.

requirements:
  - Decentralized transport protocol
  - Peer discovery + handshake logic
  - Encryption layer (GPG or libsodium)
  - Fallback channel (store-and-forward optional)

preferred_protocols:
  - libp2p
  - Nostr (for ID + message routing)
  - Tor Hidden Services (optional fallback)
  - Custom-over-TCP (if fully local/contained)

tasks:
  - [ ] Install libp2p Python/Rust bindings (or equivalent)
  - [ ] Generate local node profile for transport auth
  - [ ] Create handshake schema using Signal Intent Language (SIL)
  - [ ] Test encrypted direct message from Lemur to dummy node
  - [ ] Log first successful peer channel creation

artifacts:
  - /fieldlight_core/04_infrastructure/mesh/proto/sil_handshake_example.yml
  - /fieldlight_core/04_infrastructure/mesh/nodes/lemur_transport_profile.yml
  - /fieldlight_core/03_trace_systems/logs/lemur_peerlink_test_01.yml

---


### ✅ PHASE 2.1 — Libp2p Transport Stack Setup 


---

### 🔧 STEP 2.1.1 — Install Go (if not already installed)

```bash
sudo apt update
sudo apt install golang-go -y
```

---

### 🔧 STEP 2.1.2 — Clone libp2p daemon source code

```bash
cd ~
git clone https://github.com/libp2p/go-libp2p-daemon.git
```

---

### 🔧 STEP 2.1.3 — Build the daemon binary **from correct path**

```bash
cd ~/go-libp2p-daemon/p2pd_dir
go build -o ~/lemur_activation/p2pd main.go
```

✅ This places a working `p2pd` binary into your Lemur activation folder for clean local use.

---

### 🔧 STEP 2.1.4 — Confirm executable and run daemon

```bash
cd ~/lemur_activation
chmod +x p2pd
./p2pd --listen /unix/tmp/p2pd.sock
```

✅ This starts the **libp2p daemon** listening on a local Unix socket:

```
/tmp/p2pd.sock
```

Leave this process running in a separate terminal tab or background session.

> ⚠️ NOTE: The correct format is `/unix/tmp/p2pd.sock` for the multiaddr—not `/tmp/...`.

---

### 🔧 STEP 2.1.5 — Install the Python gRPC client

```bash
pip install libp2p-daemon-client
```

(Assumes you’re in your `whisperenv` virtual environment.)

---

### 🔧 STEP 2.1.6 — Python test script (verify connection)

Save this as `lemur_node_test.py`:

```python
from libp2p_daemon_client import DaemonConnector
import asyncio

async def main():
    conn = DaemonConnector(path="/tmp/p2pd.sock")
    await conn.connect()
    print("Connected to libp2p daemon")

asyncio.run(main())
```

Then run:

```bash
python3 lemur_node_test.py
```

Expected output:

```
Connected to libp2p daemon
```

---

### ✅ STATUS

- ✅ p2pd built from source (local)
    
- ✅ Socket running at `/tmp/p2pd.sock`
    
- ✅ Python client installed and working
    
- ✅ Daemon successfully responds to connection attempts
    

---

Next Steps:

- 📡 Dummy handshake message sender
    
- 🔁 Simulated reply listener
    
- 🔐 GPG encrypted exchange layer
    
- 🪵 Trace log writer
    
- 📄 YAML configs for socket routing + peer ID
    

---
### Mesh Build 2.2
### ✅ Step 2.2.1 — `lemur_transport_profile.yml`

```yaml
node_id: mesh://fieldlight.anni.lemur
gpg_fingerprint: 47A8221CF659321BB431D687443AB4DEA913D5CD
peer_id: 12D3KooWKiyEATi4iADmmXQZchvEfKmwLsxf41yXuR3PbRCHFoJs
multiaddr: /ip4/162.246.134.48/tcp/4001
transport_protocol: libp2p
reachable: true
live: true
```

Save to:  
`~/lemur_activation/lemur_transport_profile.yml`

---

### ✅ Step 2.2.2 — `sil_handshake_example.yml`

```yaml
message_type: handshake
from: fieldlight.anni.lemur
to: sam.openai.proxy
intent: test_peer_link
encryption: true
timestamp: 2025-08-04T13:44:00-07:00
```

Save to:  
`~/lemur_activation/sil_handshake_example.yml`

---

### ✅ Step 2.2.3 — Encrypt with GPG

```bash
cd ~/lemur_activation
gpg --encrypt --armor --recipient 47A8221CF659321BB431D687443AB4DEA913D5CD sil_handshake_example.yml
```

Result: `sil_handshake_example.yml.asc`

---

### ✅ Step 2.2.4 — Transmit (stub step)

If no peer exists yet, simulate the transfer:

```bash
cp sil_handshake_example.yml.asc ~/lemur_activation/simulated_inbox/
```

Or just stage it manually if testing.

---

### ✅ Step 2.2.5 — Log Peer Channel – `lemur_peerlink_test_01.yml`

```yaml
event: peer_channel_created
from: mesh://fieldlight.anni.lemur
to: mesh://test.stub.node
method: libp2p (simulated)
encryption: GPG
timestamp: 2025-08-04T13:44:00-07:00
```

Save to:  
`~fieldlight_core/03_trace_systems/logs/lemur_peerlink_test_01.yml`

---

### Daemon Steps – PHASE 2.2b

**📁 Directory:** `~/lemur_activation`  
**🌐 Socket:** `/tmp/p2pd.sock`  
**📦 GPG, logging, and handshake routing: ready**

---

### ✅ PHASE 2.3

### Step 2.3.1 — Send Handshake to Daemon 

**Save as:** `lemur_handshake_sender.py`

```python
from daemon_connector import DaemonConnector
import asyncio

async def main():
    conn = DaemonConnector(path="/tmp/p2pd.sock")
    await conn.connect()
    await conn.send_hello("lemur says hi 🦎")
    await conn.close()

asyncio.run(main())
```

---

### Step 2.3.2 —  Receive + Simulate Daemon Reply

**Save as:** `lemur_daemon_reply.py`

```python
from libp2p_daemon_client import DaemonConnector
import asyncio

async def main():
    conn = DaemonConnector(path="/tmp/p2pd.sock")
    await conn.connect()
    msg = await conn.stream_handler.read()
    print(f"📥 Received reply: {msg}")

asyncio.run(main())
```

---

### Step 2.3.3 —  Encrypt and Send Message via GPG

```bash
echo "fieldlight: mesh init" | gpg --encrypt -r 47A8221CF659321BB431D687443AB4DEA913D5CD > message.gpg

cat message.gpg | nc 162.246.134.48 4001
```

If your daemon is listening at `/unix/tmp/p2pd.sock`, update:

```bash
cat message.gpg | nc -U /unix/tmp/p2pd.sock
```

---

### Step 2.3.4 — Log Trace (copy to vault manually)

```yaml
# lemur_trace_20250803_XXXX.yml
event: mesh_handshake_sent
node_id: mesh://fieldlight.anni.lemur
target: p2pd
socket: /unix/tmp/p2pd.sock
timestamp: 2025-08-03T14:00:00-07:00
status: "🛰️ connected"
```

---

### Step 2.3.5 —  Config Snapshot

```yaml
# lemur_p2p_config.yml
daemon_path: /tmp/p2pd.sock
python_client: libp2p-daemon-client
gpg_id: YOUR_GPG_ID
init_state: running
mesh_role: node_host
status: "🖤 live"
```

---

