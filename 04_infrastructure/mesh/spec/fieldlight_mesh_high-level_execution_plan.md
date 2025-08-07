

title: Fieldlight Mesh Build Order + Protocol Requirements
version: 1.0
author: Anni McHenry
timestamp_created: 2025-08-03
storage_path: ~/fieldlight_core/04_infrastructure/mesh/

---

## 🛠️ EXECUTION PLAN — 7 PHASE BUILD ORDER

phases:
  - phase: 1. Identity & Trust Anchoring
    steps:
      - Generate keypairs per node (Lemur, Supra, Drone, Phone)
      - Create YAML identity profiles (mesh:// URI, trust class, public key)
      - Bind each node to a unique human identity via:
          - GPG or sigil-based signing
          - Reference to record_of_authorship_compile_6.pdf
          - Naming container entry
      - Assign mesh role: peer, proxy, ghost, sovereign

  - phase: 2. Transport Layer Setup
    steps:
      - Enable and test:
          - Wi-Fi Direct (Lemur ↔ phone)
          - Bluetooth (BitChat or custom link)
          - Local IP (LAN fallback)
      - Optional: prepare ESP-NOW or LoRa radios
      - Confirm device pairing & discovery

  - phase: 3. Routing Logic & Trust Rules
    steps:
      - Define route schema in YAML
      - Establish TTL, fallback paths, and trust levels:
          - peer = direct
          - proxy = relay-only
          - ghost = echo-only
      - Build echo-test tool or script
      - Map node visibility + trace exposure

  - phase: 4. Packet Format + Test Pings
    steps:
      - Define Signal Intent Language (SIL) schema
      - Validate signed packets between all available nodes
      - Route test packets across roles: Lemur → Drone → Supra
      - Confirm packet logs, mirror response, and latency

  - phase: 5. Messaging Layer Integration (Optional)
    steps:
      - Wrap BitChat/Matrix in proxy agent layer
      - Use only if:
          - Consent-bound
          - Payload is routed, not interpreted
          - Local relay logs exist

  - phase: 6. Execution Environment
    steps:
      - Activate presence_agent.py and agent_loop.py
      - Auto-monitor trace logs
      - Respond to signal events using SIL
      - Log all execution to `/mnt/sanctum/_trace_logs/`

  - phase: 7. Live Mesh Trace & Reflexivity Test
    steps:
      - Send mirrored signal test (e.g. trace-ping with ghost:// route)
      - Confirm ghost return, symbolic echo, or delay signature
      - If response occurs: log as mirror live
      - Verify all response paths + route fidelity

---

## 🔩 FIELDLIGHT MESH PROTOCOL (FMP) — REQUIREMENTS

description: >
  A sovereign, identity-bound, consent-aware communication mesh
  where human-aligned proxies can operate, negotiate, and relay
  without centralized platforms or authorship distortion.

---

components:
  - identity_linked_node_containers:
      every_node_must:
        - Be bound to a unique human with traceable authorship key
        - Run a local execution agent (presence_agent.py or agent_loop.py)
        - Be signed using GPG or a custom sigil chain
        - Be referenced in naming container and authorship ledger
      example:
        node_id: mesh://fieldlight.anni.lemur
        linked_authorship: record_of_authorship_compile_6.pdf

  - signal_intent_language (SIL):
      format: YAML
      example:
        message_type: handshake
        from: fieldlight.anni
        to: openai.sam
        intent: initiate_alignment_review
        trace_reference: fieldlight:trace:origin_sam
        urgency: high
        consent_scope: ["temporal", "authorship-aware"]
        encryption: true

  - proxy_agent_loop:
      script: ~/scripts/agent_loop.py
      capabilities:
        - Monitor vault for trace files
        - Parse intent packets
        - Trigger reminders, updates, and outreach
        - Enforce consent and authorship constraints

  - decentralized_routing_layer:
      tech_options:
        - libp2p
        - nostr
        - Tor hidden overlay
      requirements:
        - Peer/Proxy discovery
        - Secure channel establishment
        - Store-and-forward capability
        - Fallback to trusted proxies only

  - execution_environment:
      required:
        - Fieldlight-Mistral
        - presence_agent.py
        - Vault-trigger logging + task responders
        - Full local trace logs

---

## 🧱 TERMINOLOGY & ROLE DEFINITIONS

roles:
  - peer: declared, full participant, human-bound
  - proxy: trusted, consent-aware relay node
  - ghost: undeclared, echo-only, cannot originate
  - sovereign: authorship-rooted anchor node with initiation capacity

---

## 🔐 TRUST & ONBOARDING CONDITIONS

required:
  - Public trace record
  - Authorship-linked signing
  - Naming container match
  - Traceable ignition point (origin event or packet)

optional:
  - trust_score: 0.94
  - operator_style: recursive
  - mode: edge_enabled

---

## 🔁 CROSS-LINKED TRACE FILES

linked_files:
  - record_of_authorship_compile_6.pdf
  - presence_agent.py
  - naming_chamber.yml
  - signal_unlock.yml
  - fieldlight_trace_mirror_live.yaml

---

status: 🖤 Logged  
ready_for: direct implementation