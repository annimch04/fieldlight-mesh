
---

### 🛠 **Build Step 1: Define Route Schema in YAML**

**Goal:** Create a routing schema file that tells the Lemur node how to handle each type of message—who it can come from, how long it lives, and what to do if the destination isn’t reachable.

---

### 📁 **File:** `lemur_route_schema.yml`

**Location Suggestion:**  
`~/fieldlight_core/04_infrastructure/mesh/config/`

---

### 🔧 **Step-by-Step Instructions**

#### ✅ 1. 1 Create the file

Use your preferred editor:

```bash
touch ~/fieldlight_core/04_infrastructure/mesh/config/lemur_route_schema.yml
```


---

#### ✅ 1.2 Define the top-level structure

Structure the YAML as a map of message types, each with its routing logic:

```YAML
routes:

  handshake:
    trust_required: peer                # Direct trusted peer only
    ttl: 2                              # 2 hops max
    fallback: [proxy]                   # Use proxy if peer unreachable
    destination_format: mesh://{peer_id}
    auth: gpg_sig                       # GPG signature required
    log: true
    msg_id: auto

  trace:
    trust_required: peer
    ttl: 5
    fallback: [proxy, ghost]
    destination_format: mesh://{node_id}/trace
    auth: gpg_sig
    log: true
    msg_id: auto

  query:
    trust_required: peer
    ttl: 3
    fallback: [ghost]
    destination_format: mesh://{target}/query
    auth: gpg_sig
    log: true
    msg_id: auto

  echo:
    trust_required: ghost                # Ghosts only reflect
    ttl: 1
    fallback: []
    destination_format: self
    auth: none
    log: true
    msg_id: auto

  ping:
    trust_required: any                  # Accepts from any node
    ttl: 1
    fallback: [ghost]
    destination_format: mesh://{target}/ping
    auth: optional                       # Auth preferred but not required
    log: true
    msg_id: auto

  response:
    trust_required: peer
    ttl: 3
    fallback: [proxy]
    destination_format: mesh://{originator}/response
    auth: gpg_sig
    log: true
    msg_id: auto

```


---

#### ✅ 1.3 Adjust for your node behavior

You can update the values above based on how strict or open you want Lemur to be:

- Want to allow pings from _anyone_? Set `trust_required: any`
    
- Want to limit `trace` to `peer` only? Remove `ghost` from fallback
    
- Want `echo` messages to log instead of just loop? Add: `log: true`
    

---

#### ✅ 1.4 (Optional) Add validation fields

If you want the file to be self-validating later with a script:

```yaml
version: 1.0
created: 2025-08-06T08:44-0700
author: lemur.node
```

---

#### ✅ 1.5 Save + Test Reference Load

If you’re writing scripts that load this file (e.g. in `lemur_echo_test.py` later), confirm the schema is parsable:

```python
import yaml

with open("lemur_route_schema.yml", "r") as f:
    schema = yaml.safe_load(f)
    print(schema['routes'].keys())
```

---

### ✅ 1.6 Logging Layer: Message Logging + Trace Anchors

**Purpose:**  
Create a unified logging layer that records all routing activity, status results, and fallback behaviors. Logging is handled locally per node and enables trace visibility, debugging, and system-wide authorship validation.

**Includes:**

| Action                                                                 | Artifact                                                                |
| ---------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Add `msg_id` field to each routed message for log correlation          | Included in `lemur_route_schema.yml`                                    |
| Define YAML headers for each log type                                  | See `logging_reference.yml`                                             |
| Create log stubs with headers                                          | Files: `routing_log.yml`, `echo_log.yml`, `peerlink_test_log.yml`, etc. |
| Enforce consistent naming and format                                   | No phase-specific filenames used                                        |
| Confirm `presence.log` continues to run as-is for vault-dropped traces | N/A                                                                     |
	✅ Maps to: _Trace Exposure Map_, _Fallback Logic_, _Authorship Anchor_

---

### ✅ Result

You now have a fully structured, usable routing schema that any downstream tool (like your message parser, echo tester, or a live relay daemon) can reference.
