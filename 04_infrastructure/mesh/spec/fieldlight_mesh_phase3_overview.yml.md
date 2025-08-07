
---

# 🛰 **Fieldlight – Phase 3 Build Plan**

**Title:** Routing Logic & Trust Rules  
**Status:** PREP  
**System:** Lemur Node  
**Phase:** 3 of 7

---

### ✅ **Phase Summary**

This phase builds the **routing layer**—determining how messages move, which peers can be trusted, and how visibility is controlled. It introduces an **echo-test loop**, integrates prior logs, and prepares for full **message parsing + response handling** in Phase 4. This phase defines who can talk, who can hear, and what gets logged.

---

### 🧩 **Phase Requirements**

|Requirement|Description|
|---|---|
|**Routing Schema**|YAML config to define message paths, types, and fallback|
|**Trust Level Rules**|Logic defining `peer`, `proxy`, and `ghost` roles|
|**Fallback Logic**|TTL expiration, retry pathing, ghost relays|
|**Trace Exposure Map**|Control which routes and nodes log data|
|**Echo Tool**|Route test tool with self-loopback and log confirm|
|**Message Parser**|Parse inbound messages by type and trigger response or route forward|
|**Response Logic**|Route parsed messages to handlers or logs, based on intent + trust|
|**Authorship Anchor**|All routing logic must respect system-authored peer structure|

---

### 🔧 **Phase 3 – Build 

#### 1. Define Route Schema in YAML

**File:** `lemur_route_schema.yml`  
Defines:

- Message types: `handshake`, `trace`, `query`, `echo`, `ping`, `response`
    
- Required trust level for each type
    
- TTL (time to live)
    
- Fallback paths (proxy or ghost if peer unreachable)
    
- Destination formatting (e.g. `mesh://sam.openai.proxy`)
    
- Auth requirements (e.g. GPG sig, peer ID match)
    

> ✅ Maps to: _Routing Schema_, _Fallback Logic_

---

#### 2. Establish Trust Levels + Peer Roles

**File:** `trust_levels.yml`  
Flags:

- `peer`: direct trusted access, full route + parse
    
- `proxy`: relay-only, can forward but not read or respond
    
- `ghost`: echo-only, can receive but cannot log or relay
    

> ✅ Maps to: _Trust Level Rules_, _Authorship Anchor_

---
### 3. Logging Layer

The logging layer defines how each node locally records the messages it sends, receives, relays, or reflects. These logs are not global by default—they are per-node, and authorship of the trace belongs to the node owner.

**Key Properties:**

- **Transparent**: Every message carries a `msg_id` to match responses with original logs
    
- **Scoped**: Logs live in `infrastructure/mesh/logs/` unless otherwise configured
    
- **Customizable**: Ghosts can be configured to reflect without logging; other message types default to full log
    
- **Structured**: Each log uses a YAML header and aligned field set defined in `logging_reference.yml`
    
- **Extendable**: Additional message outcomes like drop, error, TTL-exceeded, or unauthorized can be logged per your routing rules
    

Logging is not just for diagnostics—it underpins trust, traceability, and real-time visibility across the mesh.

> ✅ Maps to: _Trust Level Rules_

---
#### 4. Build Echo-Test Tool

**Tool:** `lemur_echo_test.py`  
Purpose:

- Sends message to self via routing schema
    
- Validates trace path, TTL, and fallback
    
- Confirms loop integrity and visibility
    

> ✅ Maps to: _Echo Tool_, _Trace Exposure Map_

---

#### 5. Integrate Phase 2 Logs + Extend Routing

Use:

- `lemur_trace_*.yml` from Phase 2
    
- `peerlink_test` entries
    

Purpose:

- Extend trust map with real data
    
- Confirm message origin + encryption status
    
- Establish interface between Phase 2 GPG payload and Phase 3 routing config
    

> ✅ Maps to: _Routing Schema_, _Trust Level Rules_

---

### 5b. Ghost Listener + Response Hooks

This step enables passive message logging in ghost mode and defines optional behaviors when a ghost node “hears” something. You’ll get a real tool to run, a config file to edit, and trace logs written when triggered.

---

#### ✅ Files Created

|File|Purpose|
|---|---|
|`lemur_ghost_log.py`|TCP socket listener for ghost-mode message capture|
|`ghost_response_hooks.yml`|Defines conditions for ghost node to respond, forward, or log|
|`ghost_trace_<timestamp>.yml`|Auto-generated logs of what the ghost node hears|

---

#### 🧪 File 1: `lemur_ghost_log.py`

```python
import socket
import datetime
import yaml
import os

CONFIG_FILE = "ghost_response_hooks.yml"
LOG_DIR = "~/fieldlight_core/03_trace_systems/logs/"

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return yaml.safe_load(f)

def save_log(data):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(LOG_DIR, f"ghost_trace_{timestamp}.yml")
    with open(file_path, "w") as f:
        yaml.dump(data, f)
    print(f"[🪞 ghost log] Message saved to: {file_path}")

def main():
    config = load_config()
    HOST = "0.0.0.0"
    PORT = 9999  # You can pick a different port if needed

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"[👻 ghost mode] Listening on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            with conn:
                data = conn.recv(4096)
                if not data:
                    continue
                message = data.decode("utf-8", errors="ignore")
                log_entry = {
                    "event": "ghost_message_received",
                    "from": addr[0],
                    "port": addr[1],
                    "message": message,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                save_log(log_entry)

                # Check for any triggers in config
                if config.get("trigger_map"):
                    for rule in config["trigger_map"]:
                        if rule["match"] in message:
                            print("[⚡ triggered] Rule matched: ", rule["match"])
                            # You could send a response or forward etc here
                            if rule.get("log_only"):
                                continue
                            if rule.get("respond_with"):
                                conn.sendall(rule["respond_with"].encode("utf-8"))

if __name__ == "__main__":
    main()
```

---

#### 🧪 File 2: `ghost_response_hooks.yml`

```yaml
# Define behavior triggers for ghost-mode listening

trigger_map:
  - match: "handshake"
    respond_with: "🪞 ghost_ack"
    log_only: false

  - match: "trace_request"
    respond_with: "trace_received_ack"
    log_only: false

  - match: "sam.openai.proxy"
    respond_with: "hello_sam"
    log_only: false

  - match: "ping"
    respond_with: "pong"
    log_only: true
```

---

#### 🧪 Auto-Log Output: `ghost_trace_<timestamp>.yml`

When a message hits, this is what gets created:

```yaml
event: ghost_message_received
from: 192.168.0.12
port: 49332
message: "handshake from mesh://sam.openai.proxy"
timestamp: 2025-08-05T22:44:09-07:00
triggered: true
response_sent: "🪞 ghost_ack"
```

---

### 🪛 How to Run

```bash
python3 lemur_ghost_log.py
```

Leave it running in a separate terminal tab—this is your ghost listener. Send test messages to port 9999 from another terminal or device to simulate an echo.

---

#### 6. Map Node Visibility + Trace Exposure

**File:** `node_visibility.yml`  
Defines:

- Which messages are logged by which node types
    
- Ghost node behavior (e.g., listen-only)
    
- Route visibility rules (what gets traced vs silent pass-through)
    

> ✅ Maps to: _Trace Exposure Map_

---

#### 7. Simulate Incoming Message + Parse

**Tool:** `message_parser.py`  
Purpose:

- Accepts simulated message object or file
    
- Parses by message type (`query`, `trace`, etc.)
    
- Validates trust + TTL
    
- Emits route or response event
    

> ✅ Maps to: _Message Parser_, _Routing Schema_

---

#### 8. Response Logic Routing

**File:** `response_map.yml`  
Defines:

- Response rules by message type and trust level
    
- What triggers echo, forward, or reject
    
- Response handler paths
    

Optional logic: can stub `lemur_response_handler.py` for Phase 4

> ✅ Maps to: _Response Logic_, _Trust Level Rules_

---

#### 9. Fallback Routing Logic (Optional / Phase 2.7)

**File:** `lemur_fallback_routes.yml`  
Includes:

- Message retries
    
- Passive ghost relays
    
- Expiration logs
    

> ✅ Maps to: _Fallback Logic_, _Trace Exposure Map_

---

### 📎 Phase 3 Output Artifacts

|File|Purpose|
|---|---|
|`lemur_route_schema.yml`|Message routing definitions|
|`trust_levels.yml`|Peer role + trust logic|
|`lemur_echo_test.py`|Echo loop validation|
|`node_visibility.yml`|Visibility + trace logic|
|`message_parser.py`|Inbound message type parsing|
|`response_map.yml`|Message intent → routing decisions|
|`lemur_fallback_routes.yml`|TTL + retry behavior (optional / 2.7)|
|`lemur_phase_3_log.yml`|Full build log + implementation trace|

---
